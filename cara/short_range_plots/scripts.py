""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 18/02/2021
Code version: 4.0.0
"""

from tqdm import tqdm
from matplotlib.patches import Rectangle, Patch
from scipy.spatial import ConvexHull
from model_scenarios import *
from cara.models import *
import cara.monte_carlo as mc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as patches
import matplotlib as mpl
from scipy.interpolate import make_interp_spline
from mpl_toolkits.axes_grid1.inset_locator import mark_inset


######### Plot material #########
np.random.seed(2000)
SAMPLE_SIZE = 250000
TIMESTEP = 0.1
#viral_loads = np.linspace(2, 12, 600)
_VectorisedFloat = typing.Union[float, np.ndarray]


def previous_deposited_exposure_between_bounds(model: ExposureModel, time1: float, time2: float) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract
        between any two times.
        """
        emission_rate_per_aerosol = model.concentration_model.infected.emission_rate_per_aerosol_when_present()
        aerosols = model.concentration_model.infected.aerosols()
        fdep = model.long_range_fraction_deposited()
        f_inf = model.concentration_model.infected.fraction_of_infectious_virus()

        diameter = model.concentration_model.infected.particle.diameter

        if not np.isscalar(diameter) and diameter is not None:
            # we compute first the mean of all diameter-dependent quantities
            # to perform properly the Monte-Carlo integration over
            # particle diameters (doing things in another order would
            # lead to wrong results).
            dep_exposure_integrated = np.array(model._long_range_normed_exposure_between_bounds(time1, time2) *
                                               aerosols *
                                               fdep).mean()
        else:
            # in the case of a single diameter or no diameter defined,
            # one should not take any mean at this stage.
            dep_exposure_integrated = model._long_range_normed_exposure_between_bounds(time1, time2)*aerosols*fdep

        # then we multiply by the diameter-independent quantity emission_rate_per_aerosol,
        # and parameters of the vD equation (i.e. f_inf, BR_k and n_in).
        return (dep_exposure_integrated * emission_rate_per_aerosol * 
                f_inf * model.exposed.activity.inhalation_rate * 
                (1 - model.exposed.mask.inhale_efficiency()))


def concentration_curve(models, labels, labelsDose, colors, linestyles, thickness):

    exp_models = [model.build_model(size=SAMPLE_SIZE) for model in models]

    start = min(min(model.concentration_model.infected.presence.transition_times())
                for model in exp_models)
    stop = max(max(model.concentration_model.infected.presence.transition_times())
               for model in exp_models)

    times = np.arange(start, stop, TIMESTEP)

    concentrations = [[np.mean(model.concentration(
        t)) for t in times] for model in tqdm(exp_models)]
    
    fig, ax = plt.subplots()
    
    for c, color, linestyle, width in zip(concentrations, colors, linestyles, thickness):
        ax.plot(times, c, color=color, ls=linestyle, lw=width)

    ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] * 1.2)
    ax.spines["right"].set_visible(False)

    cumulative_doses = [np.cumsum([
        np.array(model.deposited_exposure_between_bounds(
            float(time1), float(time2))).mean()
        for time1, time2 in tqdm(zip(times[:-1], times[1:]))
    ]) for model in exp_models]

    quantile_05 = [np.cumsum([
        np.quantile(np.array(model.deposited_exposure_between_bounds(
            float(time1), float(time2))), 0.05)
        for time1, time2 in tqdm(zip(times[:-1], times[1:]))
    ]) for model in exp_models]

    quantile_95 = [np.cumsum([
        np.quantile(np.array(model.deposited_exposure_between_bounds(
            float(time1), float(time2))), 0.95)
        for time1, time2 in tqdm(zip(times[:-1], times[1:]))
    ]) for model in exp_models]

    plt.xlabel("Time of day", fontsize=14)
    plt.ylabel("Mean concentration\n(virions m$^{-3}$)", fontsize=14)

    ax1 = ax.twinx()
    for vd, color, width in tqdm(zip(cumulative_doses, colors, thickness)):
        ax1.plot(times[:-1], vd,
                 color=color, linestyle='dotted', lw=1)
        ax1.scatter([times[-1]], [vd[-1]], marker='.', color=color)

    # # Plot presence of exposed person
    # for i, model in enumerate(models):
    #     for i, (presence_start, presence_finish) in enumerate(model.exposed.presence.boundaries()):
    #         plt.fill_between(
    #             times, quantile_95[i], 0,
    #             where=(np.array(times) > presence_start) & (np.array(times) < presence_finish),
    #             color=color[i], alpha=0.1,
    #         )

    # # Plot short range interaction area
    # for i, model in enumerate(models):
    #     for presence in model.short_range.presence:
    #         (presence_start, presence_finish) = presence.boundaries()
    #         plt.fill_between(
    #             times, quantile_95[i],
    #             where=(np.array(times) > presence_start) & (np.array(times) < presence_finish),
    #             color='#1f77b4', alpha=0.1,
    #         )

    
    ax1.spines["right"].set_linestyle((0, (1, 5)))
    ax1.set_ylabel('Mean cumulative dose\n(infectious virus)', fontsize=14)
    ax1.set_ylim(ax1.get_ylim()[0], ax1.get_ylim()[1] * 1.3)
    
    complete_labels = labels + [label for label in labelsDose]
    complete_colors = colors + [color for color in colors]
    complete_linestyles = linestyles + ['dotted' for linestyle in linestyles]

    labels_legend = [mlines.Line2D([], [], color=color, label=label, linestyle=linestyle)
              for color, label, linestyle in zip(complete_colors, complete_labels, complete_linestyles)]

    for i in range(len(models)):
        print('Scenario: ', labels[i])
        print(
            f"MEAN vD = {cumulative_doses[i][-1]}\n"
            f"5th per = {quantile_05[i][-1]}\n"
            f"95th per = {quantile_95[i][-1]}\n")
    
    plt.legend(handles=labels_legend, loc='upper left')
    plt.show()

def plot_vD_vs_exposure_time(exp_models: typing.List[mc.ExposureModel], labels, colors, linestyles, points: int = 20, time_in_minutes: bool = False, normalize_y_axis: bool = False) -> None:
    
    TIMESTEP = 0.01

    concentration_models = [model.concentration_model for model in exp_models]
    exposed_models = [model.exposed for model in exp_models]
    
    vDs: typing.List[typing.List[float]] = [[] for _ in exp_models]
    
    presence_intervals = [model.short_range.presence[0].boundaries() for model in exp_models]
    start, final = presence_intervals[0]
    times = np.linspace(start, final, points)
    for finish in tqdm(times):
        current_models = [mc.ExposureModel(
            concentration_model=cm,
            short_range=mc.ShortRangeModel(
                presence=[models.SpecificInterval((start, finish), ),],
                expirations=em.short_range.expirations,
                dilutions=em.short_range.dilutions,
            ),
            exposed=exposed,
        ) for cm, exposed, em in zip(concentration_models, exposed_models, exp_models)]

        for i, m in enumerate(current_models):
            vDs[i].append(np.mean(m.build_model(SAMPLE_SIZE).deposited_exposure()))

    times = np.linspace(0, 60, points)
    for i, vD in enumerate(vDs):
        plt.plot(times, vD, color=colors[i], label=labels[i])

    # plt.xlim((0, 60))
    #if normalize_y_axis:
    #    plt.ylim((0, 1))
        
    for m in exp_models:
        print(np.mean(m.build_model(SAMPLE_SIZE).deposited_exposure()))

    plt.xlabel(f'Duration of close-proximity encounter\n(min)', fontsize=12)
    plt.ylabel('Mean cumulative dose\n(infectious virus)', fontsize=12)
    plt.legend()
    plt.show()
