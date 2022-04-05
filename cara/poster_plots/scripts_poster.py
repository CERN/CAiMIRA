""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 31/03/2022
Code version: 4.0.0 """

from tqdm import tqdm
from model_scenarios_poster import *
from cara.models import *
import cara.monte_carlo as mc
import numpy as np
import matplotlib.pyplot as plt

######### Plot material #########
np.random.seed(2000)
SAMPLE_SIZE = 250_000
TIMESTEP = 0.01
viral_loads = np.linspace(2, 12, 600)
_VectorisedFloat = typing.Union[float, np.ndarray]

############# Markers (for legend) #############
markers = [5, 'd', 4]

def emission_rate_when_present(exposure_model: mc.ExposureModel):
    aerosols = exposure_model.concentration_model.infected.expiration.aerosols(
        exposure_model.concentration_model.infected.mask).mean()
    exhalation_rate = exposure_model.concentration_model.infected.activity.exhalation_rate
    viral_load_in_sputum = exposure_model.concentration_model.infected.virus.viral_load_in_sputum
    return (viral_load_in_sputum * exhalation_rate * 10 ** 6 * aerosols) * exposure_model.concentration_model.infected.number


def _normed_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
    """The number of virions per meter^3 from time1 to time2."""
    exposure = 0.
    for start, stop in self.exposed.presence.boundaries():
        if stop < time1:
            continue
        elif start > time2:
            break
        elif start <= time1 and time2<= stop:
            exposure += self.concentration_model.normed_integrated_concentration(time1, time2)
        elif start <= time1 and stop < time2:
            exposure += self.concentration_model.normed_integrated_concentration(time1, stop)
        elif time1 < start and time2 <= stop:
            exposure += self.concentration_model.normed_integrated_concentration(start, time2)
        # The case when (time1, time2) are surrounding (start, stop)
        elif time1 <= start and stop < time2:
            exposure += self.concentration_model.normed_integrated_concentration(start, stop)
    return exposure


def exposure_between_bounds(model: mc.ExposureModel, time1: float, time2: float):
    """The number of virions per meter^3 between any two times."""
    return (_normed_exposure_between_bounds(model, time1, time2) *
            emission_rate_when_present(model))


def _deposited_exposure_between_bounds(model: mc.ExposureModel, time1: float, time2: float):
    """
    The number of virus per meter^3 deposited on the respiratory
    tract. As in the exposure method, with sampled diameters the
    aerosol volume and the deposited fraction, have to be put
    in the deposited exposure before taking the mean, to obtain the
    proper result (which corresponds to an integration on diameters).
    """
    emission_rate = model.concentration_model.infected.emission_rate_when_present()
    if (not isinstance(model.concentration_model.infected,InfectedPopulation)
        or not isinstance(model.concentration_model.infected.expiration,Expiration)
        or np.isscalar(model.concentration_model.infected.expiration.diameter)
        ):
        # in all these cases, there is no distribution of
        # diameters that need to be integrated over
        return (_normed_exposure_between_bounds(model, time1, time2) *
                model.fraction_deposited() *
                emission_rate)
    else:
        # the mean of the diameter-dependent exposure (including
        # aerosols volume, but NOT the other factors) has to be
        # taken first (this is equivalent to integrating over the
        # diameters)
        mask = model.concentration_model.infected.mask
        aerosols = model.concentration_model.infected.expiration.aerosols(mask)
        return (np.array(_normed_exposure_between_bounds(model, time1, time2) * aerosols *
                model.fraction_deposited()).mean() *
                emission_rate/aerosols)

    
def inf_aero_between_bounds(model: mc.ExposureModel, time1: float, time2: float):
    inhalation_rate = model.exposed.activity.inhalation_rate
    inhale_efficiency = model.exposed.mask.inhale_efficiency()
    f_inf = model.concentration_model.infected.fraction_of_infectious_virus()
    deposited_exposure = _deposited_exposure_between_bounds(model, time1, time2)

    return inhalation_rate * (1 - inhale_efficiency) * deposited_exposure * f_inf

######### Methods #########

############ Compare concentration curves ############

def compare_concentration_curves(models, labels, colors):

    exp_models = [model.build_model(size=SAMPLE_SIZE) for model in models]

    start = min(min(model.concentration_model.infected.presence.transition_times())
                for model in exp_models)
    stop = max(max(model.concentration_model.infected.presence.transition_times())
               for model in exp_models)

    times = np.arange(start, stop, TIMESTEP)

    concentrations = [[np.mean(model.concentration_model.concentration(
        t)) for t in times] for model in tqdm(exp_models)]
    
    fig, ax = plt.subplots()
    
    for c, label, color in zip(concentrations, labels, colors):
        ax.plot(times, c, label=label, color=color, lw=2)

    # ax.legend(fontsize=12, loc='lower left', bbox_to_anchor=(1.12, 0.))
    ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] * 1.01)
    ax.spines["right"].set_visible(False)

    cumulative_doses = [np.cumsum([
        np.array(inf_aero_between_bounds(model,
            float(time1), float(time2))).mean()
        for time1, time2 in tqdm(zip(times[:-1], times[1:]))
    ]) for model in exp_models]

    plt.xlabel("Exposure time ($h$)", fontsize=14)
    plt.ylabel("Mean concentration exposure\n(virions m$^{-3}$)", fontsize=14)
    plt.legend(loc='lower left', bbox_to_anchor=(1.12, 0.))

    ax1 = ax.twinx()
    for vd, label, color in tqdm(zip(cumulative_doses, labels, colors)):
        ax1.plot(times[:-1], vd, label='vD - ' + label,
                 color=color, linestyle='dotted', lw=2)
        ax1.scatter([times[-1]], [vd[-1]], marker='.', color=color)
        # ax1.errorbar([times[-1]], [vd[-1]], [[vd[-1] - d_05[-1]], [d_95[-1] - vd[-1]]],
        #      fmt='.', mfc=color, mec=color, ecolor=color, lw=1, capsize=3)
    ax1.spines["right"].set_linestyle((0, (1, 5)))
    ax1.set_ylabel('Mean cumulative dose\n(infectious virus)', fontsize=14)
    ax1.set_ylim(ax1.get_ylim()[0], ax1.get_ylim()[1] * 1.1)

    plt.show()


######### Probability of infection vs Viral load #########
def plot_pi_vs_viral_load(activity, expiration, mask):

    TIMESTEP = 0.001

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    pi_means = []
    lower_percentiles = []
    upper_percentiles = []

    pi_omicron_means = []
    pi_omicron_vaccinated_means = []

    for vl in tqdm(viral_loads):
        # Nominal strain
        exposure_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=1, hi=0.)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        pi = exposure_model.infection_probability()/100
        pi_means.append(np.mean(pi))
        lower_percentiles.append(np.quantile(pi, 0.05))
        upper_percentiles.append(np.quantile(pi, 0.95))

        # Omicron
        exposure_omicron_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=0.2, hi=0.)
        exposure_omicron_model = exposure_omicron_mc.build_model(size=SAMPLE_SIZE)
        pi_omicron = exposure_omicron_model.infection_probability()/100
        pi_omicron_means.append(np.mean(pi_omicron))

        # nominal and vaccinated
        #TODO change exposure_omicron_vaccinated_mc to exposure_delta_vaccinated_mc (etc.) here below
        exposure_omicron_vaccinated_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=0.51, hi=0.75)
        exposure_omicron_vaccinated_model = exposure_omicron_vaccinated_mc.build_model(size=SAMPLE_SIZE)
        pi_omicron_vaccinated = exposure_omicron_vaccinated_model.infection_probability()/100
        pi_omicron_vaccinated_means.append(np.mean(pi_omicron_vaccinated))

    ax.plot(viral_loads, pi_means, label='')
    ax.fill_between(viral_loads, lower_percentiles,
                    upper_percentiles, alpha=0.2)

    ax.plot(viral_loads, pi_omicron_means, label='', linestyle='dotted', )
    ax.plot(viral_loads, pi_omicron_vaccinated_means, label='', linestyle='dashed', color='violet')

    ############ Plot ############
    plt.ylabel('Probability of infection', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=['$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)

    # add vertical lines for the critical viral loads for which pi= 5 or 95
    left_index, right_index = 0, 0
    for i, pi in enumerate(pi_means):
        if pi > 0.05:
            left_index = i
            break

    for i, pi in enumerate(pi_means[::-1]):
        if pi < 0.95:
            right_index = len(viral_loads) - i
            break

    left, right = viral_loads[left_index], viral_loads[right_index]
    print('$vl_{crit, a}$ = 10^', np.round(left, 1), '\n')
    print('$vl_{crit, b}$ = 10^', np.round(right, 1), '\n')

    plt.vlines(x=(left, right), ymin=0, ymax=1,
              colors=('grey', 'grey'), linestyles='dotted')
    plt.text(left - 1.3, 0.80, '$vl_{crit, a}$', fontsize=14,color='black')
    plt.text(right + 0.1, 0.80, '$vl_{crit, b}$', fontsize=14,color='black')
    # add 3 shaded areas
    plt.axvspan(2, left, alpha=0.1, color='limegreen')
    plt.axvspan(left, right, alpha=0.1, color='orange')
    plt.axvspan(right, 12, alpha=0.1, color='tomato')

    plt.show()


######### Probability of infection vs Viral load with boxplot #########
def plot_pi_vs_viral_load_box_plot(activity, expiration, mask):

    TIMESTEP = 0.001

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    pi_means = []
    lower_percentiles = []
    upper_percentiles = []

    pi_omicron_means = []
    pi_omicron_lower_percentiles = []
    pi_omicron_upper_percentiles = []
    pi_omicron_vaccinated_means = []
    pi_omicron_vaccinated_lower_percentiles = []
    pi_omicron_vaccinated_upper_percentiles = []

    for vl in tqdm(viral_loads):
        # Nominal strain
        exposure_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=1, hi=0.)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        pi = exposure_model.infection_probability()/100
        pi_means.append(np.mean(pi))
        lower_percentiles.append(np.quantile(pi, 0.05))
        upper_percentiles.append(np.quantile(pi, 0.95))

        # Omicron
        exposure_omicron_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=0.2, hi=0.)
        exposure_omicron_model = exposure_omicron_mc.build_model(size=SAMPLE_SIZE)
        pi_omicron = exposure_omicron_model.infection_probability()/100
        pi_omicron_means.append(np.mean(pi_omicron))
        pi_omicron_lower_percentiles.append(np.quantile(pi_omicron, 0.05))
        pi_omicron_upper_percentiles.append(np.quantile(pi_omicron, 0.95))

        # nominal and vaccinated
        #TODO change exposure_omicron_vaccinated_mc to exposure_vaccinated_mc (etc.) here below
        exposure_omicron_vaccinated_mc = exposure_vl(activity, expiration, mask, vl, virus_t_factor=1, hi=0.75)
        exposure_omicron_vaccinated_model = exposure_omicron_vaccinated_mc.build_model(size=SAMPLE_SIZE)
        pi_omicron_vaccinated = exposure_omicron_vaccinated_model.infection_probability()/100
        pi_omicron_vaccinated_means.append(np.mean(pi_omicron_vaccinated))
        pi_omicron_vaccinated_lower_percentiles.append(np.quantile(pi_omicron_vaccinated, 0.05))
        pi_omicron_vaccinated_upper_percentiles.append(np.quantile(pi_omicron_vaccinated, 0.95))

    ax.plot(viral_loads, pi_means, label='Wild strain', color='royalblue')
    ax.fill_between(viral_loads, lower_percentiles,
                    upper_percentiles, color='royalblue', alpha=0.2)

    ax.plot(viral_loads, pi_omicron_vaccinated_means, linestyle='--', color='royalblue', label='Vaccination')    
    ax.plot(viral_loads, pi_omicron_means, linestyle='--', color='orange', label='Omicron VOC')


    # add vertical lines for the critical viral loads for which pi= 5 or 95
    left_index, right_index, mean_index = 0, 0, 0
    for i, pi in enumerate(pi_means):
        if pi > 0.05:
            left_index = i
            break

    for i, pi in enumerate(pi_means[::-1]):
        if pi < 0.95:
            right_index = len(viral_loads) - i
            break

    left, right = viral_loads[left_index], viral_loads[right_index]
    print('$vl_{crit, a}$ = 10^', np.round(left, 1), '\n')
    print('$vl_{crit, b}$ = 10^', np.round(right, 1), '\n')

    plt.vlines(x=(left, right), ymin=0, ymax=1,
              colors=('grey', 'grey'), linestyles='dotted')
    plt.text(left - 1.1, 0.80, '$vl_{crit, a}$', fontsize=14,color='black')
    plt.text(right + 0.1, 0.20, '$vl_{crit, b}$', fontsize=14,color='black')
    # add 3 shaded areas
    plt.axvspan(2, left, alpha=0.08, color='limegreen')
    plt.axvspan(left, right, alpha=0.08, color='orange')
    plt.axvspan(right, 12, alpha=0.08, color='tomato')
            
    # Boxplots
    ax1=ax.twinx()
    ax1.tick_params(left=False, labelleft=False, top=False, labeltop=False, right=False, labelright=False, bottom=False, labelbottom=False)
    ax1.set_ylim(ax.get_ylim())

    for t_factor, hi, means, lower_percentiles, upper_percentiles, color in zip((0.2, 1), (0, 0.75), (pi_omicron_means, pi_omicron_vaccinated_means), 
                                                        (pi_omicron_lower_percentiles, pi_omicron_vaccinated_lower_percentiles),
                                                        (pi_omicron_upper_percentiles, pi_omicron_vaccinated_upper_percentiles), ('orange', 'royalblue')):

        left_index, right_index, mean_index = 0, 0, 0
        for i, pi in enumerate(means):
            if pi > 0.05:
                left_index = i
                break

        for i, pi in enumerate(means[::-1]):
            if pi < 0.95:
                right_index = len(viral_loads) - i
                break

        mean_index = min(enumerate(means), key=lambda x: abs(x[1]-0.5))[0]

        # Boxplots def
        for box in (left_index, right_index, mean_index):
            viral_load = viral_loads[box]
            exposure_mc = exposure_vl(activity, expiration, mask, viral_load, virus_t_factor=t_factor, hi=hi)
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            pi = exposure_model.infection_probability()/100

            item = {}
            item["label"] = 'box' # not required
            item["med"] = viral_load
            item["mean"] = viral_load
            item["q1"] = viral_load
            item["q3"] = viral_load
            index1 = min(enumerate(lower_percentiles), key=lambda x: abs(x[1]-np.mean(pi)))[0]
            index2 = min(enumerate(upper_percentiles), key=lambda x: abs(x[1]-np.mean(pi)))[0]
            item["whislo"] = viral_loads[index2] # required
            item["whishi"] = viral_loads[index1] # required
            item["fliers"] = [] # required if showfliers=True

            ax1.bxp([item], positions=[np.mean(pi)], widths = 0.05, vert=False, showbox=False, showmeans=True, 
                showfliers=False, medianprops=dict(linewidth=0), 
                meanprops=dict(marker='o', markerfacecolor=color, markeredgecolor='none'),
                whiskerprops=dict(color=color), capprops=dict(color=color))

    
    ############ Plot ############
    ax.set_ylabel('Probability of infection', fontsize=14)
    ax.set_xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    ax.legend(loc='upper left', framealpha=0.5)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=['$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.show()