from dataclasses import dataclass
import functools
from cara import models
import numpy as np
import scipy.stats as sct
import typing
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity


# The (k, lambda) parameters for the weibull-distributions corresponding to each quantity
weibull_parameters = [((0.5951563631241763, 0.027071715346754264),          # emission_concentration
                       (15.312035476444153, 0.8433059432279654 * 3.33)),    # particle_diameter_breathing
                      ((2.0432559401256634, 3.3746316960164147),            # emission_rate_speaking
                       (5.9493671011143965, 1.081521101924364 * 3.33)),     # particle_diameter_speaking
                      ((2.317686940362959, 5.515253884170728),              # emission_rate_speaking_loudly
                       (7.348365409721486, 1.1158159287760463 * 3.33))]     # particle_diameter_speaking_loudly


log_viral_load_frequencies = ((1.880302953, 2.958422139, 3.308759599, 3.676921581, 4.036604757, 4.383770594,
                               4.743136608, 5.094658141, 5.45613857, 5.812946142, 6.160090835, 6.518505362,
                               6.866918705, 7.225333232, 7.574148314, 7.923640008, 8.283027166, 8.641758855,
                               9.000448256, 9.35956054, 9.707720153, 10.06554264, 10.41435773, 10.76304594,
                               11.12198907, 11.47118475),
                              (0.001694915, 0.00720339, 0.027966102, 0.205932203, 0.213983051, 0.171186441,
                               0.172881356, 0.217372881, 0.261440678, 0.211864407, 0.168644068, 0.151271186,
                               0.133474576, 0.116101695, 0.106355932, 0.110169492, 0.112288136, 0.101271186,
                               0.08940678, 0.086016949, 0.063135593, 0.033898305, 0.024152542, 0.011864407,
                               0.005084746, 0.002966102))


@dataclass(frozen=True)
class MCVirus:
    #: Biological decay (inactivation of the virus in air)
    halflife: float

    #: RNA copies  / mL
    viral_load_in_sputum: typing.Tuple[float, float]

    @property
    def decay_constant(self):
        # Viral inactivation per hour (h^-1)
        return np.log(2) / self.halflife


@dataclass(frozen=True)
class MCInfectedPopulation(models.Population):
    #: The virus with which the population is infected.
    virus: MCVirus

    #: An integer signifying the expiratory activity of the infected subject
    # (1 = breathing, 2 = speaking, 3 = speaking loudly)
    expiratory_activity: int

    # The total number of samples to be generated
    samples: int

    # The quantum infectious dose to be used in the calculations
    qid: int

    viral_load: typing.Optional[float] = None

    def _generate_viral_loads(self):
        kde_model = KernelDensity(kernel='gaussian', bandwidth=0.1)
        kde_model.fit(np.asarray(log_viral_load_frequencies)[0, :][:, np.newaxis],
                      sample_weight=np.asarray(log_viral_load_frequencies)[1, :])

        return kde_model.sample(n_samples=self.samples)[:, 0]

    def emission_rate_when_present(self) -> np.ndarray:
        """
        Randomly samples values for the quantum generation rate
        :return: A numpy array of length = samples, containing randomly generated qr-values
        """

        # Extracting only the needed information from the pre-existing Mask class
        masked = self.mask.exhale_efficiency != 0

        (e_k, e_lambda), (d_k, d_lambda) = weibull_parameters[self.expiratory_activity]
        emissions = sct.weibull_min.isf(sct.norm.sf(np.random.normal(size=self.samples)), e_k, loc=0, scale=e_lambda)
        diameters = sct.weibull_min.isf(sct.norm.sf(np.random.normal(size=self.samples)), d_k, loc=0, scale=d_lambda)
        if self.viral_load is None:
            viral_loads = np.random.normal(loc=7.8, scale=1.7, size=self.samples)
        else:
            viral_loads = np.full(self.samples, self.viral_load)

        mask_efficiency = [0.75, 0.81, 0.81][self.expiratory_activity] if masked else 0
        qr_func = np.vectorize(self._calculate_qr)

        # TODO: Add distributions for parameters
        breathing_rate = 1

        return qr_func(viral_loads, emissions, diameters, mask_efficiency, self.qid)

    @staticmethod
    def _calculate_qr(viral_load: float, emission: float, diameter: float, mask_efficiency: float,
                     copies_per_quantum: float, breathing_rate: typing.Optional[float] = None) -> float:
        """
        Calculates the quantum generation rate given a set of parameters.
        """
        # Unit conversions
        diameter *= 1e-4
        viral_load = 10 ** viral_load
        emission = (emission * 3600) if breathing_rate is None else (emission * 1e6)

        volume = (4 * np.pi * (diameter / 2) ** 3) / 3
        if breathing_rate is None:
            breathing_rate = 1

        return viral_load * emission * volume * (1 - mask_efficiency) * breathing_rate / copies_per_quantum

    def individual_emission_rate(self, time) -> np.ndarray:
        """
        The emission rate of a single individual in the population.

        """
        # Note: The original model avoids time dependence on the emission rate
        # at the cost of implementing a piecewise (on time) concentration function.

        if not self.person_present(time):
            return np.zeros(self.samples)

        # Note: It is essential that the value of the emission rate is not
        # itself a function of time. Any change in rate must be accompanied
        # with a declaration of state change time, as is the case for things
        # like Ventilation.

        return self.emission_rate_when_present()

    @functools.lru_cache()
    def emission_rate(self, time) -> float:
        """
        The emission rate of the entire population.

        """
        return self.individual_emission_rate(time) * self.number


@dataclass(frozen=True)
class MCConcentrationModel:
    room: models.Room
    ventilation: models.Ventilation
    infected: MCInfectedPopulation

    @property
    def virus(self):
        return self.infected.virus

    def infectious_virus_removal_rate(self, time: float) -> float:
        # Particle deposition on the floor
        vg = 1 * 10 ** -4
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h

        return k + self.virus.decay_constant + self.ventilation.air_exchange(self.room, time)

    @functools.lru_cache()
    def state_change_times(self):
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.

        """
        state_change_times = set()
        state_change_times.update(self.infected.presence.transition_times())
        state_change_times.update(self.ventilation.transition_times())

        return sorted(state_change_times)

    def last_state_change(self, time: float):
        """
        Find the most recent state change.

        """
        for change_time in self.state_change_times()[::-1]:
            if change_time < time:
                return change_time
        return 0

    @functools.lru_cache()
    def concentration(self, time: float) -> np.ndarray:
        if time == 0:
            return np.zeros(self.infected.samples)
        IVRR = self.infectious_virus_removal_rate(time)
        V = self.room.volume

        t_last_state_change = self.last_state_change(time)
        concentration_at_last_state_change = self.concentration(t_last_state_change)

        delta_time = time - t_last_state_change
        fac = np.exp(-IVRR * delta_time)
        concentration_limit = (self.infected.emission_rate(time)) / (IVRR * V)
        return concentration_limit * (1 - fac) + concentration_at_last_state_change * fac


@dataclass(frozen=True)
class MCExposureModel:
    #: The virus concentration model which this exposure model should consider.
    concentration_model: MCConcentrationModel

    #: The population of non-infected people to be used in the model.
    exposed: models.Population

    #: The number of times the exposure event is repeated (default 1).
    repeats: int = 1

    def quanta_exposure(self) -> np.ndarray:
        """The number of virus quanta per meter^3."""
        exposure = np.zeros(self.concentration_model.infected.samples)

        for start, stop in self.exposed.presence.boundaries():
            concentrations = np.asarray([self.concentration_model.concentration(t) for t in np.linspace(start, stop)])
            integrals = np.trapz(concentrations, axis=0)
            exposure += integrals

        return exposure * self.repeats

    def infection_probability(self):
        exposure = self.quanta_exposure()

        inf_aero = (
            self.exposed.activity.inhalation_rate *
            (1 - self.exposed.mask.η_inhale) *
            exposure
        )

        # Probability of infection.
        return (1 - np.exp(-inf_aero)) * 100

    def expected_new_cases(self):
        prob = self.infection_probability()
        exposed_occupants = self.exposed.number
        return prob * exposed_occupants / 100

    # def reproduction_number(self):
    #     """
    #     The reproduction number can be thought of as the expected number of
    #     cases directly generated by one infected case in a population.
    #
    #     """
    #     if self.concentration_model.infected.number == 1:
    #         return self.expected_new_cases()
    #
    #     # Create an equivalent exposure model but with precisely
    #     # one infected case.
    #     single_exposure_model = nested_replace(
    #         self, {'concentration_model.infected.number': 1}
    #     )
    #
    #     return single_exposure_model.expected_new_cases()


def logscale_hist(x: typing.Iterable, bins: int) -> None:
    """
    Plots the data of x as a log-scale histogram
    :param x: An array containing the data to be plotted
    :param bins: The number of bins to be used in the histogram (number of bars)
    :return: Nothing
    """
    hist, bins = np.histogram(x, bins=bins)
    logscale_bins = np.logspace(np.log10(bins[0]), np.log10(bins[-1]), len(bins))
    plt.hist(x, bins=logscale_bins)
    plt.xscale('log')


def print_qr_info(qr_values: np.ndarray) -> None:
    log_qr = np.log10(qr_values)
    print(f"MEAN of log_10(qR) = {np.mean(log_qr)}\n"
          f"MEAN of qR = {np.mean(qr_values)}")

    for quantile in (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99):
        print(f"qR_{quantile} = {np.quantile(qr_values, quantile)}")


baseline_mc_exposure_model = MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=models.PiecewiseConstant((0,24),(283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            virus=MCVirus(halflife=1.1, viral_load_in_sputum=(7.8, 1.7)),
            expiratory_activity=1,
            samples=200000,
            qid=100
        )
    ),
    exposed=models.Population(
        number=1,
        presence=models.SpecificInterval(((0, 4), (5, 8))),
        activity=models.Activity.types['Light activity'],
        mask=models.Mask.types['No mask']
    )
)


models = [
MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0,24),(293,)),
            outside_temp=models.PiecewiseConstant((0,24),(283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            virus=MCVirus(halflife=1.1, viral_load_in_sputum=(7.8, 1.7)),
            expiratory_activity=1,
            samples=2000000,
            qid=100,
            viral_load=vl
        )
    ),
    exposed=models.Population(
        number=1,
        presence=models.SpecificInterval(((0, 4), (5, 8))),
        activity=models.Activity.types['Light activity'],
        mask=models.Mask.types['No mask']
    )
) for vl in (None, 7, 8, 9, 10)
]
