from dataclasses import dataclass
import functools
from cara import models
import numpy as np
import scipy.stats as sct
import typing
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity

USE_SCOEH = False

scoeh_vl_frequencies = ((1.880302953, 2.958422139, 3.308759599, 3.676921581, 4.036604757, 4.383770594,
                         4.743136608, 5.094658141, 5.45613857, 5.812946142, 6.160090835, 6.518505362,
                         6.866918705, 7.225333232, 7.574148314, 7.923640008, 8.283027166, 8.641758855,
                         9.000448256, 9.35956054, 9.707720153, 10.06554264, 10.41435773, 10.76304594,
                         11.12198907, 11.47118475),
                        (0.001694915, 0.00720339, 0.027966102, 0.205932203, 0.213983051, 0.171186441,
                         0.172881356, 0.217372881, 0.261440678, 0.211864407, 0.168644068, 0.151271186,
                         0.133474576, 0.116101695, 0.106355932, 0.110169492, 0.112288136, 0.101271186,
                         0.08940678, 0.086016949, 0.063135593, 0.033898305, 0.024152542, 0.011864407,
                         0.005084746, 0.002966102))

symptomatic_vl_frequencies = ((2.46032, 2.67431, 2.85434, 3.06155, 3.25856, 3.47256, 3.66957, 3.85979, 4.09927, 4.27081,
                               4.47631, 4.66653, 4.87204, 5.10302, 5.27456, 5.46478, 5.6533, 5.88428, 6.07281, 6.30549,
                               6.48552, 6.64856, 6.85407, 7.10373, 7.30075, 7.47229, 7.66081, 7.85782, 8.05653, 8.27053,
                               8.48453, 8.65607, 8.90573, 9.06878, 9.27429, 9.473, 9.66152, 9.87552),
                              (0.001206885, 0.007851618, 0.008078144, 0.01502491, 0.013258014, 0.018528495, 0.020053765,
                               0.021896167, 0.022047184, 0.018604005, 0.01547796, 0.018075445, 0.021503523, 0.022349217,
                               0.025097721, 0.032875078, 0.030594727, 0.032573045, 0.034717482, 0.034792991,
                               0.033267721, 0.042887485, 0.036846816, 0.03876473, 0.045016819, 0.040063473, 0.04883754,
                               0.043944602, 0.048142864, 0.041588741, 0.048762031, 0.027921732, 0.033871788,
                               0.022122693, 0.016927718, 0.008833228, 0.00478598, 0.002807662))

# NOT USED
# The (k, lambda) parameters for the weibull-distributions corresponding to each quantity
weibull_parameters = [((0.5951563631241763, 0.027071715346754264),          # emission_concentration
                       (15.312035476444153, 0.8433059432279654 * 3.33)),    # particle_diameter_breathing
                      ((2.0432559401256634, 3.3746316960164147),            # emission_rate_speaking
                       (5.9493671011143965, 1.081521101924364 * 3.33)),     # particle_diameter_speaking
                      ((2.317686940362959, 5.515253884170728),              # emission_rate_speaking_loudly
                       (7.348365409721486, 1.1158159287760463 * 3.33))]     # particle_diameter_speaking_loudly

# NOT USED
# (Xmin, Xmax, a, b)
beta_parameters = ((0.0, 0.0558823529411764, 0.40785196091099885, 0.6465433589950477),              # Breathing
                   (0.00735294117647056, 0.094485294117647, 0.5381693341323044, 1.055612645201782)) # Breathing (fast-deep)

# (csi, lamb)
lognormal_parameters = ((0.10498338229297108, -0.6872121723362303),     # BR, seated
                        (0.09373162411398223, -0.5742377578494785),     # BR, standing
                        (0.09435378091059601, 0.21380242785625422),     # BR, light exercise
                        (0.1894616357138137, 0.551771330362601),        # BR, moderate exercise
                        (0.21744554768657565, 1.1644665696723049))      # BR, heavy exercise

emission_concentrations = (3.00079e-7, 1.06008e-4, 5.28837e-4)

log_viral_load_frequencies = scoeh_vl_frequencies if USE_SCOEH else symptomatic_vl_frequencies


def lognormal(csi: float, lamb: float, samples: int) -> np.ndarray:
    sf_norm = sct.norm.sf(np.random.normal(size=samples))
    return sct.lognorm.isf(sf_norm, csi, loc=0, scale=np.exp(lamb))


@dataclass(frozen=True)
class MCVirus:
    #: Biological decay (inactivation of the virus in air)
    halflife: float

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

    #: An integer signifying the breathing category of the infected subject
    # (1 = seated, 2 = standing, 3 = light exercise, 4 = moderate exercise, 5 = heavy exercise)
    breathing_category: int

    # The total number of samples to be generated
    samples: int

    # The quantum infectious dose to be used in the calculations
    qid: int

    viral_load: typing.Optional[float] = None

    @functools.lru_cache()
    def _generate_viral_loads(self) -> np.ndarray:
        if self.viral_load is None:
            kde_model = KernelDensity(kernel='gaussian', bandwidth=0.1)
            kde_model.fit(np.asarray(log_viral_load_frequencies)[0, :][:, np.newaxis],
                          sample_weight=np.asarray(log_viral_load_frequencies)[1, :])

            return kde_model.sample(n_samples=self.samples)[:, 0]
        else:
            return np.full(self.samples, self.viral_load)

    @functools.lru_cache()
    def _generate_breathing_rates(self) -> np.ndarray:
        br_params = lognormal_parameters[self.breathing_category - 1] + (self.samples,)
        return lognormal(*br_params)

    def emission_rate_when_present(self) -> np.ndarray:
        """
        Randomly samples values for the quantum generation rate
        :return: A numpy array of length = samples, containing randomly generated qr-values
        """

        # Extracting only the needed information from the pre-existing Mask class
        masked = self.mask.exhale_efficiency != 0

        viral_loads = self._generate_viral_loads()

        emission_concentration = emission_concentrations[self.expiratory_activity - 1]

        mask_efficiency = [0.75, 0.81, 0.81][self.expiratory_activity - 1] if masked else 0
        qr_func = np.vectorize(self._calculate_qr)

        breathing_rates = self._generate_breathing_rates()

        return qr_func(viral_loads, emission_concentration, mask_efficiency, self.qid, breathing_rates)

    @staticmethod
    def _calculate_qr(viral_load: float, emission_concentration: float, mask_efficiency: float,
                      copies_per_quantum: float, breathing_rate: float) -> float:
        """
        Calculates the quantum generation rate given a set of parameters.
        """
        # Unit conversions
        viral_load = 10 ** viral_load

        return viral_load * emission_concentration * (1 - mask_efficiency) * breathing_rate / copies_per_quantum

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
class BuonannoSpecificInfectedPopulation:
    #: The virus with which the population is infected.
    virus: MCVirus

    # The total number of samples to be generated
    samples: int

    presence: models.Interval = models.SpecificInterval(((0, 2),))

    constant_qr: float = 1000

    @functools.lru_cache()
    def emission_rate(self, time) -> float:
        """
        The emission rate of the entire population.

        """
        return self.constant_qr


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


def buaonanno_exposure_model():
    return MCExposureModel(
        concentration_model=MCConcentrationModel(
            room=models.Room(volume=800),
            ventilation=models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                         air_exch=0.5),
            infected=BuonannoSpecificInfectedPopulation(virus=MCVirus(halflife=1.1),
                                                        samples=1)
        ),
        exposed=models.Population(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            activity=models.Activity.types['Light activity'],
            mask=models.Mask.types['No mask']
        )
    )


baseline_mc_exposure_model = MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            virus=MCVirus(halflife=1.1),
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

durations = tuple(np.linspace(0, 120, 10))

models = [
MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 8))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            virus=MCVirus(halflife=1.1),
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
