from dataclasses import dataclass
from tqdm import tqdm
import functools
from itertools import product
from cara import models
import numpy as np
import scipy.stats as sct
from scipy.integrate import quad
import typing
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines
from sklearn.neighbors import KernelDensity

# This is a test comment

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
weibull_parameters = [((0.5951563631241763, 0.027071715346754264),  # emission_concentration
                       (15.312035476444153, 0.8433059432279654 * 3.33)),  # particle_diameter_breathing
                      ((2.0432559401256634, 3.3746316960164147),  # emission_rate_speaking
                       (5.9493671011143965, 1.081521101924364 * 3.33)),  # particle_diameter_speaking
                      ((2.317686940362959, 5.515253884170728),  # emission_rate_speaking_loudly
                       (7.348365409721486, 1.1158159287760463 * 3.33))]  # particle_diameter_speaking_loudly

# NOT USED
# (Xmin, Xmax, a, b)
beta_parameters = ((0.0, 0.0558823529411764, 0.40785196091099885, 0.6465433589950477),  # Breathing
                   (0.00735294117647056, 0.094485294117647, 0.5381693341323044,
                    1.055612645201782))  # Breathing (fast-deep)

# (csi, lamb)
lognormal_parameters = ((0.10498338229297108, -0.6872121723362303),  # BR, seated
                        (0.09373162411398223, -0.5742377578494785),  # BR, standing
                        (0.09435378091059601, 0.21380242785625422),  # BR, light exercise
                        (0.1894616357138137, 0.551771330362601),  # BR, moderate exercise
                        (0.21744554768657565, 1.1644665696723049))  # BR, heavy exercise

# NOT USED (directly in calculated in concentration_vs_diameter )
emission_concentrations = (1.38924e-6, 1.07098e-4, 5.29935e-4)

concentration_vs_diameter = (
    # B-mode
    lambda d:
    (1 / d) * (0.1 / (np.sqrt(2 * np.pi) * 0.26)) * np.exp(-1 * (np.log(d) - 1.0) ** 2 / (2 * 0.26 ** 2)),
    # L-mode
    lambda d:
    (1 / d) * (1.0 / (np.sqrt(2 * np.pi) * 0.5)) * np.exp(-1 * (np.log(d) - 1.4) ** 2 / (2 * 0.5 ** 2)),
    # O-mode
    lambda d:
    (1 / d) * (0.001 / (np.sqrt(2 * np.pi) * 0.56)) * np.exp(-1 * (np.log(d) - 4.98) ** 2 / (2 * 0.56 ** 2))
)


def mask_leak_out(d: float) -> float:
    if d < 0.5:
        return 1

    if d < 0.94614:
        return 1 - (0.5893 * d + 0.1546)

    if d < 3:
        return 1 - (0.0509 * d + 0.664)

    return 1 - 0.8167


log_viral_load_frequencies = scoeh_vl_frequencies if USE_SCOEH else symptomatic_vl_frequencies


def lognormal(csi: float, lamb: float, samples: int) -> np.ndarray:
    """
    Generates a number of samples from a specified lognormal distribution
    :param csi: A parameter used to specify the lognormal distribution
    :param lamb: A parameter used to specify the lognormal distribution
    :param samples: The number of samples to be generated
    :return: A numpy-array containing 
    """
    sf_norm = sct.norm.sf(np.random.normal(size=samples))
    return sct.lognorm.isf(sf_norm, csi, loc=0, scale=np.exp(lamb))


@dataclass(frozen=True)
class MCVirus:
    #: Biological decay (inactivation of the virus in air)
    halflife: float

    #: RNA-copies per quantum
    qID: int

    @property
    def decay_constant(self):
        # Viral inactivation per hour (h^-1)
        return np.log(2) / self.halflife


@dataclass(frozen=True)
class MCPopulation:
    """
    Represents a group of people all with exactly the same behaviour and
    situation.

    """
    #: How many in the population.
    number: int

    #: The times in which the people are in the room.
    presence: models.Interval

    #: Indicates whether or not masks are being worn
    masked: bool

    #: An integer signifying the expiratory activity of the population
    # (1 = breathing, 2 = speaking, 3 = speaking loudly)
    expiratory_activity: int

    #: An integer signifying the breathing category of the population
    # (1 = seated, 2 = standing, 3 = light exercise, 4 = moderate exercise, 5 = heavy exercise)
    breathing_category: int

    def person_present(self, time):
        return self.presence.triggered(time)


@dataclass(frozen=True)
class MCInfectedPopulation(MCPopulation):
    #: The virus with which the population is infected.
    virus: MCVirus

    #: The total number of samples to be generated
    samples: int

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

    @functools.lru_cache()
    def _concentration_distribution_without_mask(self) -> typing.Callable:
        if self.expiratory_activity == 1:
            return concentration_vs_diameter[0]

        if self.expiratory_activity == 2:
            return lambda d: sum(f(d) for f in concentration_vs_diameter)

        if self.expiratory_activity == 3:
            return lambda d: 5 * sum(f(d) for f in concentration_vs_diameter)

    @functools.lru_cache()
    def _concentration_distribution_with_mask(self) -> typing.Callable:
        concentration = self._concentration_distribution_without_mask()
        return lambda d: concentration(d) * mask_leak_out(d)

    def _calculate_emission_concentration(self) -> float:
        function = self._concentration_distribution_with_mask() if self.masked else \
            self._concentration_distribution_without_mask()

        def integrand(d: int) -> float:
            return function(d) * np.pi * d ** 3 / 6.0

        return quad(integrand, 0.1, 30)[0] * 1e-6

    @functools.lru_cache()
    def emission_rate_when_present(self) -> np.ndarray:
        """
        Randomly samples values for the quantum generation rate
        :return: A numpy array of length = samples, containing randomly generated qr-values
        """
        viral_loads = self._generate_viral_loads()

        emission_concentration = self._calculate_emission_concentration()

        breathing_rates = self._generate_breathing_rates()

        viral_loads = 10 ** viral_loads

        return viral_loads * emission_concentration * breathing_rates / self.qid

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

    @property
    def qid(self):
        return self.virus.qID


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
        vg = 1.88 * 10 ** -4  # new value different from initial CARA model (see paper)
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
    """
    A class representing a specific case described in a paper by Buonanno et al., previously used to compare our
    results with the results of the paper.
    """
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
            times = np.arange(start, stop, 0.01)
            concentrations = np.asarray([self.concentration_model.concentration(t) for t in times])
            integrals = np.trapz(concentrations, times, axis=0)
            exposure += integrals

        return exposure * self.repeats

    def infection_probability(self):
        exposure = self.quanta_exposure()
        # f_dep - fraction of the inhaled particles that actually stay here
        # not present in the CARA model
        f_dep = 0.6

        inf_aero = (
                self.exposed.activity.inhalation_rate *
                (1 - self.exposed.mask.η_inhale) *
                exposure *
                f_dep
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
    :return: Nothing, a graph is displayed
    """
    hist, binlist = np.histogram(x, bins=bins)
    logscale_bins = np.logspace(np.log10(binlist[0]), np.log10(binlist[-1]), len(binlist))
    plt.hist(x, bins=logscale_bins)
    plt.xscale('log')


def print_qr_info(log_qr: np.ndarray) -> None:
    """
    Prints statistical parameters of a given (logarithmic) distribution of qR-values
    :param log_qr: A numpy-array of the logarithms of qR-values
    :return: Nothing, parameters are printed
    """
    qr_values = 10 ** log_qr
    print(f"MEAN of log_10(qR) = {np.mean(log_qr)}\n"
          f"SD of log_10(qR) = {np.std(log_qr)}\n"
          f"MEAN of qR = {np.mean(qr_values)}\n"
          f"SD of qR = {np.std(qr_values)}\n")

    for quantile in (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99):
        print(f"qR_{quantile} = {np.quantile(qr_values, quantile)}")


def present_model(model: MCConcentrationModel, bins: int = 200,
                  title: str = 'Summary of model parameters') -> None:
    """
    Displays a number of plots and prints a handful of key parameters and results of a given MCConcentrationModel
    :param model: The MCConcentrationModel representing the scenario to be presented
    :param bins: The number of bins (bars) to use for the histograms
    :param title: A string giving the title at the top of the generated plot
    :return: Nothing, graphs are displayed and parameters are printed
    """
    fig, axs = plt.subplots(2, 2, sharex=False, sharey=False)
    fig.set_figheight(8)
    fig.set_figwidth(10)
    fig.suptitle(title)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4)
    plt.subplots_adjust(wspace=0.2)
    plt.subplots_adjust(top=0.88)
    plt.subplots_adjust(bottom=0.1)
    fig.set_figheight(10)

    for x, y in ((0, 0), (1, 0), (1, 1)):
        axs[x, y].set_yticklabels([])
        axs[x, y].set_yticks([])

    viral_loads, breathing_rates, qRs = (model.infected._generate_viral_loads(),
                                         model.infected._generate_breathing_rates(),
                                         np.log10(model.infected.emission_rate_when_present()))

    for data, (x, y) in zip((viral_loads, breathing_rates, qRs), ((0, 0), (1, 0), (1, 1))):
        axs[x, y].hist(data, bins=bins)
        top = axs[x, y].get_ylim()[1]
        mean, median, std = np.mean(data), np.median(data), np.std(data)
        axs[x, y].vlines(x=(mean, median, mean - std, mean + std), ymin=0, ymax=top,
                         colors=('grey', 'black', 'lightgrey', 'lightgrey'),
                         linestyles=('solid', 'solid', 'dashed', 'dashed'))

    axs[0, 0].set_title('Viral load')
    axs[0, 0].set_xlabel('Viral load [$log10(RNA\,copies\;mL^{-1}$)]')
    axs[0, 0].set_xlim(2, 11.5)

    ds = np.linspace(0.1, 15, 2000)
    unmasked = [model.infected._concentration_distribution_without_mask()(d) for d in ds]
    masked = [model.infected._concentration_distribution_with_mask()(d) for d in ds]
    if model.infected.masked:
        axs[0, 1].plot(ds, masked, 'b', label="With mask")
        axs[0, 1].plot(ds, unmasked, 'k--', label="Without mask")
        axs[0, 1].legend(loc="upper right")
    else:
        axs[0, 1].plot(ds, masked, 'b--', label="With mask")
        axs[0, 1].plot(ds, unmasked, 'k', label="Without mask")
        axs[0, 1].legend(loc="upper right")

    categories_particles = ("Breathing", "Speaking", "Shouting")
    axs[0, 1].set_title(r'Particle emissions - '
                        f'{categories_particles[model.infected.expiratory_activity - 1]}')
    axs[0, 1].set_ylabel('Particle emission concentration [$cm^{-3}$]')
    axs[0, 1].set_xlabel(r'Diameter [$\mu$m]')

    categories = ("seated", "standing", "light activity", "moderate activity", "heavy activity")
    axs[1, 0].set_title(f'Breathing rate - '
                        f'{categories[model.infected.breathing_category - 1]}')
    axs[1, 0].set_xlabel('Breathing rate [$m^3\;h^{-1}$]')

    top = axs[1, 1].get_ylim()[1]
    axs[1, 1].set_title('Quantum generation rate')
    axs[1, 1].set_xlabel('qR [log10($q\;h^{-1}$)]')
    mean, std = np.mean(qRs), np.std(qRs)
    axs[1, 1].annotate('', xy=(mean + std, top * 0.88), xytext=(np.max(qRs), top * 0.88),
                       arrowprops={'arrowstyle': '<|-|>', 'ls': 'dashed'})
    axs[1, 1].text(mean + std + 0.1, top * 0.92, 'Superspreader', fontsize=8)

    lines = [mlines.Line2D([], [], color=color, markersize=15, label=label, linestyle=style)
             for color, label, style in zip(['grey', 'black', 'lightgrey'],
                                            ['Mean', 'Median', 'Standard deviation'],
                                            ['solid', 'solid', 'dashed'])]

    fig.legend(handles=lines, loc="upper left")

    print_qr_info(np.asarray(qRs))

    plt.show()


def plot_pi_vs_viral_load(baselines: typing.Union[MCExposureModel, typing.List[MCExposureModel]],
                          samples_per_vl: int = 20000, title: str = 'Probability of infection vs viral load',
                          labels: typing.List[str] = None) -> None:
    if isinstance(baselines, MCExposureModel):
        baselines = [baselines]

    viral_loads = np.linspace(3, 12, 200)

    for baseline in baselines:
        infected = baseline.concentration_model.infected
        pi_means = []
        pi_medians = []
        lower_percentiles = []
        upper_percentiles = []
        for viral_load in tqdm(viral_loads):
            model = MCExposureModel(concentration_model=MCConcentrationModel(
                room=baseline.concentration_model.room,
                ventilation=baseline.concentration_model.ventilation,
                infected=MCInfectedPopulation(
                    number=infected.number,
                    presence=infected.presence,
                    masked=infected.masked,
                    expiratory_activity=infected.expiratory_activity,
                    breathing_category=infected.breathing_category,
                    virus=infected.virus,
                    samples=samples_per_vl,
                    viral_load=viral_load
                )
            ),
                exposed=baseline.exposed)

            infection_probabilities = model.infection_probability()
            pi_means.append(np.mean(infection_probabilities))
            pi_medians.append(np.median(infection_probabilities))
            lower_percentiles.append(np.quantile(infection_probabilities, 0.01))
            upper_percentiles.append(np.quantile(infection_probabilities, 0.99))

        plt.plot(viral_loads, pi_means)
        plt.fill_between(viral_loads, lower_percentiles, upper_percentiles, alpha=0.2)

    plt.title(title)
    plt.ylabel('Percentage probability of infection')
    plt.xticks(ticks=[i for i in range(3, 13)], labels=['$10^{' + str(i) + '}$' for i in range(3, 13)])
    plt.xlabel('Viral load')
    # add vertical lines for the critical viral loads for which pi= 0 or 100
    # TODO Insert viral_load(Pi = 5) and viral_load(Pi = 95) instead of hard coded values
    plt.vlines(x=(7, 11.5), ymin=0, ymax=100,
               colors=('grey', 'black'), linestyles='dashed')
    if labels is not None:
        plt.legend(labels)

    plt.show()


def plot_pi_vs_qid(baselines: typing.Union[MCExposureModel, typing.List[MCExposureModel]], samples_per_qid: int = 20000,
                   title: str = 'Probability of infection vs qID', labels: typing.List[str] = None, qid_min: float = 5,
                   qid_max: float = 2000, qid_samples: int = 200) -> None:

    if isinstance(baselines, MCExposureModel):
        baselines = [baselines]

    qids = np.geomspace(qid_min, qid_max, qid_samples)

    for baseline in baselines:
        infected = baseline.concentration_model.infected
        pi_means = []
        pi_medians = []
        lower_percentiles = []
        upper_percentiles = []
        for qid in tqdm(qids):
            model = MCExposureModel(concentration_model=MCConcentrationModel(
                room=baseline.concentration_model.room,
                ventilation=baseline.concentration_model.ventilation,
                infected=MCInfectedPopulation(
                    number=infected.number,
                    presence=infected.presence,
                    masked=infected.masked,
                    expiratory_activity=infected.expiratory_activity,
                    breathing_category=infected.breathing_category,
                    virus=MCVirus(halflife=infected.virus.halflife, qID=qid),
                    samples=samples_per_qid,
                    viral_load=infected.viral_load
                )
            ),
                exposed=baseline.exposed)

            infection_probabilities = model.infection_probability()
            pi_means.append(np.mean(infection_probabilities))
            pi_medians.append(np.median(infection_probabilities))
            lower_percentiles.append(np.quantile(infection_probabilities, 0.01))
            upper_percentiles.append(np.quantile(infection_probabilities, 0.99))

        plt.plot(qids, pi_means)
        plt.fill_between(qids, lower_percentiles, upper_percentiles, alpha=0.2)

    plt.title(title)
    plt.ylabel('Percentage probability of infection')
    plt.xlabel('qID')
    if labels is not None:
        plt.legend(labels)

    plt.show()


def generate_boxplot(masked: bool = False, samples: int = 200000, qid: int = 100) -> None:
    """
    Generates and displays a boxplot for comparing the qR-values in scenarios with various combinations of breathing
    rates and expiratory activities
    :param masked: A bool indicating whether or not the infected subject is wearing a mask
    :param samples: The number of samples to use for the monte carlo simulation
    :param qid: The number of "viral copies per quantum"
    :return: Nothing, a graph is displayed
    """
    scenarios = [MCInfectedPopulation(
        number=1,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        masked=masked,
        virus=MCVirus(halflife=1.1, qID=qid),
        expiratory_activity=e,
        samples=samples,
        breathing_category=b,
    ) for e, b in product((1, 2, 3), (1, 3, 5))]
    qr_values = [np.log10(scenario.emission_rate_when_present()) for scenario in scenarios]

    bplot = plt.boxplot(qr_values, positions=(1, 2, 3, 5, 6, 7, 9, 10, 11), patch_artist=True)
    colors = ['lightgreen', 'lightblue', 'pink']

    for patch, color in zip(bplot['boxes'], colors * 3):
        patch.set_facecolor(color)

    handles = [patches.Patch(color=c, label=l) for c, l in zip(colors, ('Seated', 'Light activity', 'Heavy activity'))]
    plt.legend(handles=handles)

    plt.xticks((2, 6, 10), ('Breathing', 'Speaking', 'Shouting'))
    plt.xlabel('Expiratory activity')
    plt.ylabel('qR [$q\;h^{-1}$]')
    plt.yticks(ticks=[2 * i for i in range(-3, 4)], labels=['$\;10^{' + str(2 * i) + '}$' for i in range(-3, 4)])
    plt.show()


def generate_cdf_curves_vs_qr(masked: bool = False, samples: int = 200000, qid: int = 100) -> None:
    """
    Generates and displays a boxplot for comparing the qR-values in scenarios with various combinations of breathing
    rates and expiratory activities
    :param masked: A bool indicating whether or not the infected subject is wearing a mask
    :param samples: The number of samples to use for the monte carlo simulation
    :param qid: The number of "viral copies per quantum"
    :return: Nothing, a graph is displayed
    """
    fig, axs = plt.subplots(3, 1, sharex='all')

    # TODO: Insert title and y-label
    plt.suptitle("INSERT TITLE HERE")
    fig.text(0.02, 0.5, 'INSERT Y-LABEL HERE', va='center', rotation='vertical')

    scenarios = [MCInfectedPopulation(
        number=1,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        masked=masked,
        virus=MCVirus(halflife=1.1, qID=qid),
        expiratory_activity=e,
        samples=samples,
        breathing_category=b,
    ) for e, b in product((1, 2, 3), (1, 3, 5))]
    qr_values = [np.log10(scenario.emission_rate_when_present()) for scenario in scenarios]
    left = min(np.min(qrs) for qrs in qr_values)
    right = max(np.max(qrs) for qrs in qr_values)

    # Colors can be changed here
    colors = ['lightgreen', 'lightblue', 'pink']

    breathing_rates = ['Seated', 'Light activity', 'Heavy activity']
    activities = ['Breathing', 'Speaking', 'Shouting']
    lines = [mlines.Line2D([], [], color=color, markersize=15, label=label)
             for color, label in zip(colors, breathing_rates)]

    for i in range(3):
        axs[i].hist(qr_values[3 * i:3 * (i + 1)], bins=2000, histtype='step',
                         color=colors, cumulative=True, range=(left, right))
        axs[i].set_xlim(left, right)
        axs[i].set_yticks([0, samples / 2, samples])
        axs[i].set_yticklabels(['0.0', '0.5', '1.0'])
        axs[i].yaxis.set_label_position("right")
        axs[i].set_ylabel(activities[i])
        axs[i].legend(handles=lines, loc='upper left')

    plt.xlabel('qR [$q\;h^{-1}$]')
    tick_positions = np.arange(int(np.ceil(left)), int(np.ceil(right)), 2)
    plt.xticks(ticks=tick_positions, labels=['$\;10^{' + str(i) + '}$' for i in tick_positions])

    fig.set_figheight(8)
    fig.set_figwidth(5)
    plt.show()


def buonanno_exposure_model() -> MCExposureModel:
    """
    :return: An MCExposureModel object corresponding to one of the scenarios outlined in the paper of Buonanno et al.
    """
    return MCExposureModel(
        concentration_model=MCConcentrationModel(
            room=models.Room(volume=800),
            ventilation=models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                         air_exch=0.5),
            infected=BuonannoSpecificInfectedPopulation(virus=MCVirus(halflife=1.1, qID=100),    # type: ignore
                                                        samples=1)  # type: ignore
        ),
        exposed=models.Population(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            activity=models.Activity.types['Light activity'],
            mask=models.Mask.types['No mask']
        )
    )


def display_original_vs_english(original_pi: np.ndarray, english_pi: np.ndarray) -> None:
    """
    Displays a violin-plot of the distributions of probabilities of infection of the original and english virus variant
    respectively
    :param original_pi: A numpy-array of percentages [0, 100] representing probabilities of infection associated with
    the original variant
    :param english_pi: A numpy-array of percentages [0, 100] representing probabilities of infection associated with
    the english variant
    :return: Nothing, a violin-plot is displayed
    """
    print(f"\nMedian(P_i) - Original: {'{:.2f}'.format(np.median(original_pi))}%\n"
          f"Mean(P_i) - Original:   {'{:.2f}'.format(np.mean(original_pi))}%\n\n"
          f"Median(P_i) - English:  {'{:.2f}'.format(np.median(english_pi))}%\n"
          f"Mean(P_i) - English:    {'{:.2f}'.format(np.mean(english_pi))}%\n")

    plt.hist(original_pi, bins=200)
    plt.yticks([], [])
    plt.xlabel('Percentage Probability of infection')
    plt.show()

    plt.violinplot((original_pi, english_pi), positions=(1, 2), showmeans=True, showmedians=True)
    plt.xticks(ticks=[1, 2], labels=['Original', 'English'])
    plt.ylabel('Percentage probability of infection')
    plt.show()


def compare_infection_probabilities_vs_viral_loads(baseline1: MCExposureModel, baseline2: MCExposureModel,
                                                   samples_per_vl: int = 20000) -> None:
    mean_ratios = []
    p1_means, p2_means = [], []
    viral_loads = np.linspace(3, 10, 200)
    for vl in tqdm(viral_loads):
        infected1 = baseline1.concentration_model.infected
        infected2 = baseline2.concentration_model.infected

        model1, model2 = [MCExposureModel(
            concentration_model=MCConcentrationModel(
                room=baseline.concentration_model.room,
                ventilation=baseline.concentration_model.ventilation,
                infected=MCInfectedPopulation(
                    number=infected.number,
                    presence=infected.presence,
                    masked=infected.masked,
                    expiratory_activity=infected.expiratory_activity,
                    breathing_category=infected.breathing_category,
                    virus=infected.virus,
                    samples=samples_per_vl,
                    viral_load=vl
                    )
                ),
            exposed=baseline.exposed) for baseline, infected in ((baseline1, infected1), (baseline2, infected2))]

        p1_mean, p2_mean = [np.mean(model.infection_probability()) for model in (model1, model2)]
        p1_means.append(p1_mean)
        p2_means.append(p2_mean)
        mean_ratios.append(p1_mean / p2_mean)

    plt.plot(viral_loads, mean_ratios)
    plt.ylabel(f"Ratio of mean P(i) values - P(i|qID = {baseline1.concentration_model.infected.qid}) / P(i|qID = {baseline2.concentration_model.infected.qid})")
    plt.xlabel("Viral load")
    plt.xticks(ticks=[i for i in range(3, 11)], labels=['$10^{' + str(i) + '}$' for i in range(3, 11)])
    plt.show()

    plt.plot(viral_loads, p1_means)
    plt.plot(viral_loads, p2_means)
    plt.ylim(0, 100)
    plt.ylabel("Percentage probability of infection")
    plt.xlabel("Viral load")
    plt.legend([f'qID = {baseline1.concentration_model.infected.qid}',
                f'qID = {baseline2.concentration_model.infected.qid}'])
    plt.xticks(ticks=[i for i in range(3, 11)], labels=['$10^{' + str(i) + '}$' for i in range(3, 11)])

    plt.show()


fixed_vl_exposure_models = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=45),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=100),
            expiratory_activity=1,
            samples=2000000,
            breathing_category=1,
            viral_load=float(vl)
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for vl in range(6, 11)]


large_population_baselines = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=800),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=2000.
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=2,
        )

    ),
    exposed=models.Population(
        number=60,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Standing'],
        mask=models.Mask.types['No mask']
    )
) for qid in (100, 60)]


exposure_models = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=45),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=1,
            samples=2000000,
            breathing_category=1,
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for qid in (100, 60)]

generate_cdf_curves_vs_qr(masked=False)

rs = [model.expected_new_cases() for model in large_population_baselines]
print(f"R0 - original variant:\t{np.mean(rs[0])}")
print(f"R0 - english variant:\t{np.mean(rs[1])}")
print(f"Ratio between R0's:\t\t{np.mean(rs[1]) / np.mean(rs[0])}")
#
# compare_infection_probabilities_vs_viral_loads(*exposure_models)
#
#
# present_model(exposure_models[0].concentration_model)
# plot_pi_vs_qid(fixed_vl_exposure_models, labels=['Viral load = $10^{' + str(i) + '}$' for i in range(6, 11)],
#                qid_min=5, qid_max=2000, qid_samples=200)
#
# plot_pi_vs_qid(fixed_vl_exposure_models, labels=['Viral load = $10^{' + str(i) + '}$' for i in range(6, 11)],
#                qid_min=100, qid_max=400, qid_samples=100)
#
#
# plot_pi_vs_viral_load(exposure_models, labels=['Without masks', 'With masks'])
#
# for model in exposure_models:
#     present_model(model.concentration_model, title=f'Model summary - {"English" if model.concentration_model.infected.qid == 60 else "Original"} variant')
#     plt.hist(model.infection_probability(), bins=200)
#     plt.xlabel('Percentage probability of infection')
#     plt.title(f'Probability of infection in baseline case - {"English" if model.concentration_model.infected.qid == 60 else "Original"} variant')
#     plt.yticks([], [])
#     plt.show()
