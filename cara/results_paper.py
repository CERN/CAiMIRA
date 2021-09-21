from tqdm import tqdm
from matplotlib.patches import Rectangle, Patch
from scipy.spatial import ConvexHull
from model_scenarios_paper import *
import cara.monte_carlo as mc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.lines as mlines
import matplotlib.patches as patches
import matplotlib as mpl

######### Plot material #########
np.random.seed(2000)
SAMPLE_SIZE = 250000
viral_loads = np.linspace(2, 12, 600)

############# Markers (for legend) #############
markers = [5, 'd', 4]


def emission_rate_when_present(exposure_model: mc.ExposureModel):
    aerosols = exposure_model.concentration_model.infected.expiration.aerosols(
        exposure_model.concentration_model.infected.mask).mean()
    exhalation_rate = exposure_model.concentration_model.infected.activity.exhalation_rate
    viral_load_in_sputum = exposure_model.concentration_model.infected.virus.viral_load_in_sputum
    return (viral_load_in_sputum * exhalation_rate * 10 ** 6 * aerosols) * exposure_model.concentration_model.infected.number


def _normed_exposure_between_bounds(model: mc.ExposureModel, time1: float, time2: float):
    """The number of virions per meter^3 between any two times, normalized 
    by the emission rate of the infected population"""
    for start, stop in model.exposed.presence.boundaries():
        if start > time2:
            normed_exposure = 0.
            break
        elif time2 <= stop:
            normed_exposure = model.concentration_model.normed_integrated_concentration(
                time1, time2)
            break
        else:
            normed_exposure = model.concentration_model.normed_integrated_concentration(
                time1, time2)
    return normed_exposure


def exposure_between_bounds(model: mc.ExposureModel, time1: float, time2: float):
    """The number of virions per meter^3 between any two times."""
    return (_normed_exposure_between_bounds(model, time1, time2) *
            emission_rate_when_present(model))

######### Exhaled virions from exposure models #########


def exposure_model_from_vl(activity, expiration, mask):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    er_means = []
    er_means_1h = []
    er_medians = []
    lower_percentiles = []
    upper_percentiles = []

    for vl in tqdm(viral_loads):
        exposure_mc = exposure_vl(activity, expiration, mask, vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)

        if expiration == 'Breathing':
            # divide by 2 to have in 30min (half an hour)
            emission_rate = emission_rate_when_present(exposure_model) / 2
        elif expiration == 'Talking':
            # divide by 4 to have in 15min (quarter of an hour)
            emission_rate = emission_rate_when_present(exposure_model) / 4
        elif expiration == 'Shouting':
            emission_rate = emission_rate_when_present(exposure_model)

        er_means.append(np.mean(emission_rate))
        er_medians.append(np.median(emission_rate))
        lower_percentiles.append(np.quantile(emission_rate, 0.01))
        upper_percentiles.append(np.quantile(emission_rate, 0.99))
        emission_rate_1h = emission_rate_when_present(exposure_model)
        er_means_1h.append(np.mean(emission_rate_1h))

    if expiration == 'Breathing':
        # divide by 2 to have in 30min (half an hour)
        coleman_etal_er_breathing_2 = [x/2 for x in coleman_etal_er_breathing]
        milton_er_2 = [x/2 for x in milton_er]
        yann_er_2 = [x/2 for x in yann_er]

        ratio = np.mean(10**viral_loads / er_means)
        ratio_1h = np.mean(10**viral_loads / er_means_1h)
        print('Mean swab-to-aersol vl ratio in 30min:')
        print(format(ratio, "5.1e"))
        print('Mean swab-to-aersol vl ratio emission rate per hour:')
        print(format(ratio_1h, "5.1e"))

        ############# Coleman #############
        scatter_coleman_data(coleman_etal_vl_breathing,
                             coleman_etal_er_breathing_2)

        ############# Milton et al #############
        scatter_milton_data(milton_vl, milton_er_2)

        ############# Yan et al #############
        scatter_yann_data(yann_vl, yann_er_2)

        ############ Legend ############
        build_breathing_legend(fig)

    elif expiration == 'Talking':
        # divide by 4 to have in 15min (quarter of an hour)
        coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking]

        ratio = np.mean(10**viral_loads / er_means)
        ratio_1h = np.mean(10**viral_loads / er_means_1h)
        print('Mean swab-to-aersol vl ratio in 30min:')
        print(format(ratio, "5.1e"))
        print('Mean swab-to-aersol vl ratio emission rate per hour:')
        print(format(ratio_1h, "5.1e"))

        ############# Coleman #############
        scatter_coleman_data(coleman_etal_vl_talking,
                             coleman_etal_er_talking_2)

        ############ Legend ############
        build_talking_legend(fig)

    elif expiration == 'Shouting':
        ratio_1h = np.mean(10**viral_loads / er_means_1h)
        print('Mean swab-to-aersol vl ratio emission rate per hour:')
        print(format(ratio_1h, "5.1e"))

    ax.plot(viral_loads, er_means)
    ax.fill_between(viral_loads, lower_percentiles,
                    upper_percentiles, alpha=0.2)
    ax.set_yscale('log')

    ############ Plot ############
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()


""" Variation according to the BLO model """


def exposure_model_from_vl_cn(activity, expiration, mask):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    n_lines = 30
    cns = np.linspace(0.01, 0.5, n_lines)

    cmap = define_colormap(cns)

    for cn in tqdm(cns):
        er_means = np.array([])
        for vl in tqdm(viral_loads):
            exposure_mc = exposure_vl_cn(
                activity, expiration, mask, vl, (cn, 0.2, 0.0010008))
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            # divide by 2 to have in 30min (half an hour)
            emission_rate = emission_rate_when_present(exposure_model) / 2
            er_means = np.append(er_means, np.mean(emission_rate))
        # divide by 2 to have in 30min (half an hour)
        coleman_etal_er_breathing_2 = [x/2 for x in coleman_etal_er_breathing]
        milton_er_2 = [x/2 for x in milton_er]
        yann_er_2 = [x/2 for x in yann_er]
        ax.plot(viral_loads, er_means, color=cmap.to_rgba(
            cn, alpha=0.75), linewidth=0.5)

    # The dashed line for the chosen Cn,B
    er_means = np.array([])
    for vl in viral_loads:
        exposure_mc = exposure_vl_cn(
            activity, expiration, mask, vl, (0.06, 0.2, 0.0010008))
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 2 to have in 30min (half an hour)
        emission_rate = emission_rate_when_present(exposure_model) / 2
        er_means = np.append(er_means, np.mean(emission_rate))
    ax.plot(viral_loads, er_means, color=cmap.to_rgba(
        cn, alpha=0.75), linewidth=1, ls='--')

    plt.text(viral_loads[int(len(viral_loads)*0.9)], 10**4.2, r"$\mathbf{c_{n,B}=0.06}$", color=cmap.to_rgba(cn), fontsize=12) if activity == 'Breathing' else plt.text(
        viral_loads[int(len(viral_loads)*0.93)], 10**5.5, r"$\mathbf{c_{n,L}=0.2}$", color=cmap.to_rgba(cn), fontsize=12)

    cmap = fig.colorbar(cmap, ticks=[0.01, 0.1, 0.25, 0.5])
    cmap.set_label(
        label='Particle emission concentration, ${c_{n,B}}$', fontsize=12)
    ax.set_yscale('log')

    ############# Coleman #############
    scatter_coleman_data(coleman_etal_vl_breathing,
                         coleman_etal_er_breathing_2)

    ############# Milton et al #############
    scatter_milton_data(milton_vl, milton_er_2)

    ############# Yan et al #############
    scatter_yann_data(yann_vl, yann_er_2)

    ############ Legend ############
    build_breathing_legend(fig)

    ############ Plot ############
    plt.title('',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()


############ Plots with viral loads and emission rates ############
############ Statistical Data ############


def get_statistical_data(activity: str, mask: str):

    log10_ers = {}
    for expiration in ('Breathing', 'Talking', 'Shouting'):
        exposure_mc = exposure_module(activity, expiration, mask)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        emission_rate = emission_rate_when_present(exposure_model)
        log10_ers[expiration] = [np.log10(er) for er in emission_rate]
        print('\n<<<<<<<<<<< ' + expiration + ' model statistics >>>>>>>>>>>')
        print_er_info(emission_rate, log10_ers[expiration])

    viral_load_in_sputum = exposure_model.concentration_model.infected.virus.viral_load_in_sputum
    return viral_load_in_sputum, log10_ers['Breathing'], log10_ers['Talking'], log10_ers['Shouting']


def present_vl_er_histograms(activity: str, mask: str):
    viral_load_in_sputum, breathing_er, speaking_er, shouting_er = get_statistical_data(
        activity, mask)

    fig, axs = plt.subplots(1, 2, sharex=False, sharey=False)
    fig.set_figheight(5)
    fig.set_figwidth(10)
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.2)
    plt.subplots_adjust(top=0.9)
    plt.subplots_adjust(bottom=0.15)

    viral_loads = [np.log10(vl) for vl in viral_load_in_sputum]

    axs[0].hist(viral_loads, bins=300, color='lightgrey')
    axs[0].set_xlabel('vl$_{\mathrm{in}}$ (log$_{10}$ RNA copies mL$^{-1}$)')

    mean = np.mean(viral_loads)
    axs[0].vlines(x=(mean), ymin=0, ymax=axs[0].get_ylim()[
                  1], colors=('grey'), linestyles=('dashed'))

    breathing_mean_er = np.mean(breathing_er)
    speaking_mean_er = np.mean(speaking_er)
    shouting_mean_er = np.mean(shouting_er)

    axs[1].hist(breathing_er, bins=300, color='lightsteelblue')
    axs[1].hist(speaking_er, bins=300, color='wheat')
    axs[1].hist(shouting_er, bins=300, color='darkseagreen')
    axs[1].set_xlabel('vR (log$_{10}$ virions h$^{-1}$)')

    axs[1].vlines(x=(breathing_mean_er, speaking_mean_er, shouting_mean_er), ymin=0, ymax=axs[1].get_ylim()[1], colors=(
        'cornflowerblue', 'goldenrod', 'olivedrab'), alpha=(0.75, 0.75, 0.75), linestyles=('dashed', 'dashed', 'dashed'))

    labels = [Patch([], [], color=color, label=label)
              for color, label in zip(['lightgrey', 'lightsteelblue', 'wheat', 'darkseagreen'],
                                      ['Viral Load', 'Breathing', 'Speaking', 'Shouting'])]
    labels.append(mlines.Line2D([], [], color='black',
                                marker='', linestyle='dashed', label='Mean'))

    for x in (0, 1):
        axs[x].set_yticklabels([])
        axs[x].set_yticks([])

    plt.legend(handles=labels, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()

############ CDFs for comparing the QR-Values in different scenarios ############


def generate_cdf_curves():
    fig, axs = plt.subplots(3, 1, sharex='all')

    ############ Breathing models ############
    br_seated = exposure_module('Seated', 'Breathing', 'No mask')
    br_seated_model = br_seated.build_model(size=SAMPLE_SIZE)

    br_light_activity = exposure_module(
        'Light activity', 'Breathing', 'No mask')
    br_light_activity_model = br_light_activity.build_model(size=SAMPLE_SIZE)

    br_heavy_exercise = exposure_module(
        'Heavy exercise', 'Breathing', 'No mask')
    br_heavy_exercise_model = br_heavy_exercise.build_model(size=SAMPLE_SIZE)

    ############ Speaking models ############
    sp_seated = exposure_module('Seated', 'Talking', 'No mask')
    sp_seated_model = sp_seated.build_model(size=SAMPLE_SIZE)

    sp_light_activity = exposure_module('Light activity', 'Talking', 'No mask')
    sp_light_activity_model = sp_light_activity.build_model(size=SAMPLE_SIZE)

    sp_heavy_exercise = exposure_module('Heavy exercise', 'Talking', 'No mask')
    sp_heavy_exercise_model = sp_heavy_exercise.build_model(size=SAMPLE_SIZE)

    ############ Shouting models ############
    sh_seated = exposure_module('Seated', 'Shouting', 'No mask')
    sh_seated_model = sh_seated.build_model(size=SAMPLE_SIZE)

    sh_light_activity = exposure_module(
        'Light activity', 'Shouting', 'No mask')
    sh_light_activity_model = sh_light_activity.build_model(size=SAMPLE_SIZE)

    sh_heavy_exercise = exposure_module(
        'Heavy exercise', 'Shouting', 'No mask')
    sh_heavy_exercise_model = sh_heavy_exercise.build_model(size=SAMPLE_SIZE)

    er_values = [np.log10(emission_rate_when_present(scenario)) for scenario in (br_seated_model, br_light_activity_model,
                                                                                 br_heavy_exercise_model, sp_seated_model,
                                                                                 sp_light_activity_model, sp_heavy_exercise_model,
                                                                                 sh_seated_model, sh_light_activity_model,
                                                                                 sh_heavy_exercise_model)]

    # Colors can be changed here
    colors_breathing = ['lightsteelblue', 'cornflowerblue', 'royalblue']
    colors_speaking = ['wheat', 'tan', 'orange']
    colors_shouting = ['palegreen', 'darkseagreen', 'forestgreen']
    colors = [colors_breathing, colors_speaking, colors_shouting]

    breathing_rates = ['Seated', 'Light activity', 'Heavy activity']
    activities = ['Breathing', 'Speaking', 'Shouting']
    lines_breathing = [mlines.Line2D([], [], color=color, markersize=15, label=label)
                       for color, label in zip(colors_breathing, breathing_rates)]
    lines_speaking = [mlines.Line2D([], [], color=color, markersize=15, label=label)
                      for color, label in zip(colors_speaking, breathing_rates)]
    lines_shouting = [mlines.Line2D([], [], color=color, markersize=15, label=label)
                      for color, label in zip(colors_shouting, breathing_rates)]
    lines = [lines_breathing, lines_speaking, lines_shouting]

    for i in range(3):
        axs[i].hist(er_values[3 * i:3 * (i + 1)], bins=2000,
                    histtype='step', cumulative=True, range=(-7, 6), color=colors[i])
        axs[i].set_xlim(-6, 6)
        axs[i].set_yticks([0, SAMPLE_SIZE / 2, SAMPLE_SIZE])
        axs[i].set_yticklabels(['0.0', '0.5', '1.0'])
        axs[i].yaxis.set_label_position("right")
        axs[i].set_ylabel(activities[i], fontsize=14)
        axs[i].grid(linestyle='--')
        axs[i].legend(handles=lines[i], loc='upper left')

    plt.xlabel('$\mathrm{vR}$', fontsize=16)
    tick_positions = np.arange(-6, 6, 2)
    plt.xticks(ticks=tick_positions, labels=[
               '$\;10^{' + str(i) + '}$' for i in tick_positions])

    fig.text(0.02, 0.5, 'Cumulative Distribution Function',
             va='center', rotation='vertical', fontsize=14)
    fig.set_figheight(8)
    fig.set_figwidth(5)
    plt.show()

############ Deposition Fraction Graph #############


def calculate_deposition_factor():

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    diameters = np.linspace(0.001, 0.01, 1000)  # particle diameter (μm)
    diameters = np.append(diameters, np.linspace(0.01, 0.1, 1000))
    diameters = np.append(diameters, np.linspace(0.1, 1., 1000))
    diameters = np.append(diameters, np.linspace(1., 10., 1000))
    diameters = np.append(diameters, np.linspace(10, 100, 1000))

    fractions_et = []
    fractions_tb = []
    fractions_al = []
    fractions_df = []
    for d in diameters:

        IF = 1 - 0.5 * (1 - (1 / (1 + (0.00076*(d**2.8)))))
        DF_et = IF * (
            (1 / (1 + np.exp(6.84 + 1.183 * np.log(d)))) +
            (1 / (1 + np.exp(0.924 - 1.885 * np.log(d))))
        )
        fractions_et.append(DF_et)

        DF_tb = (0.00352/d) * (np.exp(-0.234*((np.log(d) + 3.40)**2)
                                      ) + (63.9 * np.exp(-0.819*((np.log(d) - 1.61)**2))))
        fractions_tb.append(DF_tb)

        DF_al = (0.0155/d) * (np.exp(-0.416*((np.log(d) + 2.84)**2)) +
                              (19.11*np.exp(-0.482 * ((np.log(d) - 1.362)**2))))
        fractions_al.append(DF_al)

        DF = IF * (0.0587 + (0.911/(1 + np.exp(4.77 + 1.485 * np.log(d)))
                             ) + (0.943/(1 + np.exp(0.508 - 2.58 * np.log(d)))))
        fractions_df.append(DF)

    ax.plot(diameters, fractions_df, label='Total Deposition', color='k')
    ax.plot(diameters, fractions_et, label='Extrathoracic',
            ls='-.', lw=0.9, color='grey')
    ax.plot(diameters, fractions_tb, label='Tracheobronchial',
            ls='--', lw=0.9, color='darkgray')
    ax.plot(diameters, fractions_al, label='Alveolar',
            ls=(0, (1, 1)), lw=0.9, color='darkgray')

    ax.grid(linestyle='--')
    ax.set_xscale('log')
    ax.margins(x=0, y=0)
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

    y_ticks = [0., 0.2, 0.4, 0.6, 0.8, 1]
    x_ticks = [0.001, 0.01, 0.1, 1, 10, 100]
    plt.yticks(ticks=y_ticks, labels=[
               str(i) for i in y_ticks])
    plt.xticks(ticks=x_ticks, labels=[
               str(i) for i in x_ticks])
    plt.xlabel('Particle diameter (μm)', fontsize=14)
    plt.ylabel('Deposition fraction\nf$_{dep}$', fontsize=14)

    fig.set_figwidth(10)
    plt.tight_layout()
    plt.show()

############ Compare concentration curves ############


def compare_concentration_curves():

    exp_models = [office_model_no_mask_windows_closed().build_model(size=SAMPLE_SIZE),
                  office_model_no_mask_windows_open_breaks().build_model(size=SAMPLE_SIZE),
                  office_model_no_mask_windows_open_alltimes().build_model(size=SAMPLE_SIZE)]

    labels = ['Windows closed', 'Window open during breaks',
              'Window open at all times']
    colors = ['tomato', 'lightskyblue', 'limegreen',
              '#1f77b4', 'seagreen', 'lightskyblue', 'deepskyblue']

    start = min(min(model.concentration_model.infected.presence.transition_times())
                for model in exp_models)
    stop = max(max(model.concentration_model.infected.presence.transition_times())
               for model in exp_models)

    TIMESTEP = 0.01
    times = np.arange(start, stop, TIMESTEP)

    concentrations = [[np.mean(model.concentration_model.concentration(
        t)) for t in times] for model in exp_models]
    fig, ax = plt.subplots()
    for c, label, color in zip(concentrations, labels, colors):
        ax.plot(times, c, label=label, color=color)

    ax.legend(loc='upper left')
    ax.set_ylim(ax.get_ylim()[0], ax.get_ylim()[1] * 1.2)
    ax.spines["right"].set_visible(False)

    cumulative_doses = [np.cumsum([
        np.array(exposure_between_bounds(model,
            float(time1), float(time2))).mean()
        for time1, time2 in zip(times[:-1], times[1:])
    ]) for model in exp_models]

    plt.xlabel("Exposure time ($h$)", fontsize=14)
    plt.ylabel("Mean concentration (virions m$^{-3}$)", fontsize=14)

    ax1 = ax.twinx()
    for qd, label, color in zip(cumulative_doses, labels, colors):
        ax1.plot(times[:-1], qd, label='qD - ' + label,
                 color=color, linestyle='dotted')
    ax1.spines["right"].set_linestyle("--")
    ax1.spines["right"].set_linestyle((0, (1, 5)))
    ax1.set_ylabel('Mean cumulative dose (virions)', fontsize=14)
    ax1.set_ylim(ax1.get_ylim()[0], ax1.get_ylim()[1] * 1.2)

    plt.show()


def compare_viruses_vr():

    # Represented as tuples of three numbers on the interval [0, 1] (e.g. (1, 0, 0)) (R, G, B)
    colors = [(0., 0.5, 0.5), (0, 0, 0.5), (0.5, 0, 0), (0., 0.78, 0.)]
    colors_violin=['lightsteelblue', 'wheat', 'darkseagreen']
    colors_violin_lines = ['royalblue', 'orange', 'forestgreen']

    # The colors of the borders surrounding the violin plots
    border_colors = [(0, 0, 0), (0, 0, 0), (0, 0, 0)]
    
    whisker_width = 0.8
    positions = [1, 2, 3, 12]

    exposure_modules = [exposure_module('Light activity', expiration, 'No mask').build_model(size=SAMPLE_SIZE) for expiration in ('Breathing', 'Talking', 'Shouting')]
    
    vrs = [np.log10(emission_rate_when_present(module)) for module in exposure_modules]

    fig, ax = plt.subplots()
    ax.set_xlim((0, 11))

    parts = ax.violinplot(vrs, quantiles=[(0.05, 0.95) for _ in vrs], showextrema=False)
    means = [np.log10(np.mean(10 ** vr)) for vr in vrs]
    ax.hlines(y=means,
                xmin=[pos - whisker_width / 2 for pos in positions[:3]],
                xmax=[pos + whisker_width / 2 for pos in positions[:3]],
                colors=colors_violin_lines,
                alpha=0.8)


    for pc, color, bc in zip(parts['bodies'], colors_violin, border_colors):
        pc.set_facecolor(color)
        pc.set_edgecolor(bc)
        pc.set_alpha(0.5)
    parts['cquantiles'].set_color([c for c in colors_violin_lines[:3] for _ in range(2)])
    parts['cquantiles'].set_alpha(1)

    positions=np.linspace(4.5, 11.5, 20)

    ######### SARS-CoV #########
    lower_bound = [418]
    higher_bound = [4176]

    for i in range(len(lower_bound)):
        data = np.random.uniform(lower_bound[i], higher_bound[i], size=200000)
        ax.boxplot(np.log10(data), positions=[positions[i]], medianprops=dict(color=colors[3] + (0.5,)),
                   whiskerprops=dict(color=colors[3] + (0.5,)), boxprops=dict(color=colors[3] + (0.5,)))

    ######### SARS-CoV-2 #########
    lower_bound = [216, 216, 518, 648, 878, 893, 1670, 1872, 1915, 2002, 2002, 2189, 3341, 9835, 13968, 60667]
    higher_bound = [2160, 2160, 5184, 6480, 8784, 8928, 16704, 18720, 19152, 20016, 20016, 21888, 33408, 98352, 139680, 606672]
    
    for i in range(len(lower_bound)):
        data = np.random.uniform(lower_bound[i], higher_bound[i], size=200000)
        ax.boxplot(np.log10(data), positions=[positions[i+1]], medianprops=dict(color=colors[0]+ (0.5,)),
                   whiskerprops=dict(color=colors[0]+ (0.5,)), boxprops=dict(color=colors[0]+ (0.5,)))

    ######### Measles #########
    lower_bound = [259, 8640, 39816, 124416]
    higher_bound = [2592, 86400, 398160, 1244160]
    
    for i in range(len(lower_bound)):
        data = np.random.uniform(lower_bound[i], higher_bound[i], size=200000)
        ax.boxplot(np.log10(data), positions=[positions[i+5]], medianprops=dict(color=colors[1]+ (0.5,)),
                   whiskerprops=dict(color=colors[1]+ (0.5,)), boxprops=dict(color=colors[1]+ (0.5,)))

    ######### Influenza #########
    lower_bound = [2, 114, 1138]
    higher_bound = [16, 1145, 11376]
    
    for i in range(len(lower_bound)):
        data = np.random.uniform(lower_bound[i], higher_bound[i], size=200000)
        ax.boxplot(np.log10(data), positions=[positions[i+12]], medianprops=dict(color=colors[2]+ (0.5,)),
                   whiskerprops=dict(color=colors[2]+ (0.5,)), boxprops=dict(color=colors[2]+ (0.5,)))

    ######### Rhinovirus #########
    lower_bound = [45]
    higher_bound = [446]
    
    for i in range(len(lower_bound)):
        data = np.random.uniform(lower_bound[i], higher_bound[i], size=200000)
        ax.boxplot(np.log10(data), positions=[positions[i+8]], medianprops=dict(color=(0.5, 0.5, 0.5, 0.5, )),
                   whiskerprops=dict(color=(0.5, 0.5, 0.5, 0.5,)), boxprops=dict(color=(0.5, 0.5, 0.5, 0.5,)))
    
    handles = [patches.Patch(edgecolor=c, facecolor='none', label=l)
               for c, l in zip([p + (0.5,) for p in [(0., 0.78, 0.), (0., 0.5, 0.5), (0, 0, 0.5), (0.5, 0, 0), (0.5, 0.5, 0.5)]],
                               ('SARS-CoV', 'SARS-CoV-2', 'Measles', 'Influenza', 'Rhinovirus'))]
    boxplot_legend = plt.legend(handles=handles, loc='lower right')

    ax.annotate("Bus ride", xy=(6, np.log10(5500)), color='k', fontsize=8,
                xycoords='data',
                xytext=(-50, 50), textcoords='offset points',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=-0.2", color='lightgrey'))

    ax.annotate("S V Chorale", xy=(10, np.log10(110000)), color='k', fontsize=8,
                xycoords='data',
                xytext=(-50, 40), textcoords='offset points',
                arrowprops=dict(arrowstyle="->",
                                connectionstyle="arc3,rad=-0.2", color='lightgrey'))
    
    handles = [patches.Patch(color=c, label=l) for c, l in zip([p  for p in colors_violin], ('Breathing', 'Speaking', 'Shouting'))]
    plt.legend(handles=handles, loc='lower left', bbox_to_anchor=(0.12, 0.))
    plt.gca().add_artist(boxplot_legend)

    ax.hlines(y=[-2, 0, 2, 4, 6], xmin=ax.get_xlim()[0], xmax=ax.get_xlim()[1], colors=(0.8, 0.8, 0.8), linestyles='--', alpha=0.3)
    ax.vlines(x=4, ymin=ax.get_ylim()[0], ymax=ax.get_ylim()[1], colors=(0.8, 0.8, 0.8))
    ax.set_yticks([i for i in range(-4, 7, 2)])
    ax.set_yticklabels(['$10^{' + str(i) + '}$' for i in range(-4, 7, 2)])
    ax.set_xticks([2, 7])
    ax.set_xticklabels(['SARS-CoV-2\n(model)', 'Literature Data\n(recorded outbreaks) '])
    ax.set_ylabel('Emission rate (virions h$^{-1}$)', fontsize=12)

    plt.tight_layout()
    plt.show()

######### Auxiliar functions #########


def get_enclosure_points(x_coordinates, y_coordinates):
    df = pd.DataFrame({'x': x_coordinates, 'y': y_coordinates})

    points = df[['x', 'y']].values
    # get convex hull
    hull = ConvexHull(points)
    # get x and y coordinates
    # repeat last point to close the polygon
    x_hull = np.append(points[hull.vertices, 0],
                       points[hull.vertices, 0][0])
    y_hull = np.append(points[hull.vertices, 1],
                       points[hull.vertices, 1][0])
    return x_hull, y_hull


def define_colormap(cns):
    min_val, max_val = 0.25, 0.85
    n = 10
    orig_cmap = plt.cm.Blues
    colors = orig_cmap(np.linspace(min_val, max_val, n))

    norm = mpl.colors.Normalize(vmin=cns.min(), vmax=cns.max())
    cmap = mpl.cm.ScalarMappable(
        norm=norm, cmap=mpl.colors.LinearSegmentedColormap.from_list("mycmap", colors))
    cmap.set_array([])

    return cmap


def scatter_coleman_data(coleman_etal_vl_breathing, coleman_etal_er_breathing):
    plt.scatter(coleman_etal_vl_breathing,
                coleman_etal_er_breathing, marker='x', c='orange')
    x_hull, y_hull = get_enclosure_points(
        coleman_etal_vl_breathing, coleman_etal_er_breathing)
    # plot shape
    plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)


def scatter_milton_data(milton_vl, milton_er):
    try:
        for index, m in enumerate(markers):
            plt.scatter(milton_vl[index], milton_er[index],
                        marker=m, color='red')
        x_hull, y_hull = get_enclosure_points(milton_vl, milton_er)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='red', alpha=0.2)
    except:
        print("No data for Milton et al")


def scatter_yann_data(yann_vl, yann_er):
    try:
        plt.scatter(yann_vl[0], yann_er[0], marker=markers[0], color='green')
        plt.scatter(yann_vl[1], yann_er[1],
                    marker=markers[1], color='green', s=50)
        plt.scatter(yann_vl[2], yann_er[2], marker=markers[2], color='green')

        x_hull, y_hull = get_enclosure_points(yann_vl, yann_er)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='green', alpha=0.2)
    except:
        print("No data for Yan et al")


def build_talking_legend(fig):
    result_from_model = mlines.Line2D(
        [], [], color='blue', marker='_', linestyle='None')
    coleman = mlines.Line2D([], [], color='orange',
                            marker='x', linestyle='None')

    title_proxy = Rectangle((0, 0), 0, 0, color='w')
    titles = ["$\\bf{CARA \, \\it{(SARS-CoV-2)}:}$",
              "$\\bf{Coleman \, et \, al. \, \\it{(SARS-CoV-2)}:}$"]
    leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman],
                     [titles[0], "Results from model", titles[1], "Dataset"])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))


def build_breathing_legend(fig):
    result_from_model = mlines.Line2D(
        [], [], color='blue', marker='_', linestyle='None')
    coleman = mlines.Line2D([], [], color='orange',
                            marker='x', linestyle='None')
    milton_mean = mlines.Line2D(
        [], [], color='red', marker='d', linestyle='None')  # mean
    milton_25 = mlines.Line2D(
        [], [], color='red', marker=5, linestyle='None')  # 25
    milton_75 = mlines.Line2D(
        [], [], color='red', marker=4, linestyle='None')  # 75
    yann_mean = mlines.Line2D([], [], color='green',
                              marker='d', linestyle='None')  # mean
    yann_25 = mlines.Line2D([], [], color='green',
                            marker=5, linestyle='None')  # 25
    yann_75 = mlines.Line2D([], [], color='green',
                            marker=4, linestyle='None')  # 75

    title_proxy = Rectangle((0, 0), 0, 0, color='w')
    titles = ["$\\bf{CARA \, \\it{(SARS-CoV-2)}:}$", "$\\bf{Coleman \, et \, al. \, \\it{(SARS-CoV-2)}:}$",
              "$\\bf{Milton \, et \, al.  \,\\it{(Influenza)}:}$", "$\\bf{Yann \, et \, al.  \,\\it{(Influenza)}:}$"]
    leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman, title_proxy, milton_mean, milton_25, milton_75, title_proxy, yann_mean, yann_25, yann_75],
                     [titles[0], "Results from model", titles[1], "Dataset", titles[2], "Mean", "25th per.", "75th per.", titles[3], "Mean", "25th per.", "75th per."])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))


def print_er_info(er: np.array, log_er: np.array):
    """
    Prints statistical parameters of a given distribution of ER-values
    """
    print(f"MEAN of ER = {np.mean(er)}\n"
          f"MEAN of log ER = {np.mean(log_er)}\n"
          f"SD of ER = {np.std(er)}\n"
          f"SD of log ER = {np.std(log_er)}\n"
          f"Median of ER = {np.quantile(er, 0.5)}\n")

    print(f"Percentiles of ER:")
    for quantile in (0.01, 0.05, 0.25, 0.50, 0.55, 0.65, 0.75, 0.95, 0.99):
        print(f"ER_{quantile} = {np.quantile(er, quantile)}")

    return
