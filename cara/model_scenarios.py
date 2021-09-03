from numpy.core.function_base import linspace
from cara import models
from cara.monte_carlo.data import activity_distributions
from tqdm import tqdm
import cara.monte_carlo as mc
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import pandas as pd
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle
import matplotlib as mpl

######### Plot material #########
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

SAMPLE_SIZE = 50000

er_means = []
er_medians = []
lower_percentiles = []
upper_percentiles = []

######### Scatter points (data taken: copies per hour) #########

############# Coleman #############
############# Coleman - Breathing #############
coleman_etal_vl_breathing = [np.log10(821065925.4), np.log10(1382131207), np.log10(81801735.96), np.log10(
    487760677.4), np.log10(2326593535), np.log10(1488879159), np.log10(884480386.5)]
coleman_etal_er_breathing = [127, 455.2, 281.8, 884.2, 448.4, 1100.6, 621]
############# Coleman - Talking #############
coleman_etal_vl_talking = [np.log10(70492378.55), np.log10(7565486.029), np.log10(7101877592), np.log10(1382131207),
                           np.log10(821065925.4), np.log10(1382131207), np.log10(81801735.96), np.log10(487760677.4),
                           np.log10(2326593535), np.log10(1488879159), np.log10(884480386.5)]
coleman_etal_er_talking = [1668, 938, 319.6, 3632.8, 1243.6,
                           17344, 2932, 5426, 5493.2, 1911.6, 9714.8]
############# Milton et al #############
milton_vl = [np.log10(8.30E+04), np.log10(4.20E+05), np.log10(1.80E+06)]
milton_er = [22, 220, 1120]  # removed first and last due to its dimensions
############# Milton et al #############
yann_vl = [np.log10(7.86E+07), np.log10(2.23E+09), np.log10(1.51E+10)]
yann_er = [8396.78166, 45324.55964, 400054.0827]

######### Standard exposure models ###########
def exposure_model_from_vl_talking_new_points(viral_loads):
    for vl in tqdm(viral_loads):
        exposure_mc = mc.ExposureModel(
            concentration_model=mc.ConcentrationModel(
                room=models.Room(volume=100, humidity=0.5),
                ventilation=models.AirChange(
                    active=models.SpecificInterval(((0, 24),)),
                    air_exch=0.25,
                ),
                infected=mc.InfectedPopulation(
                    number=1,
                    virus=models.Virus(
                        viral_load_in_sputum=10**vl,
                        infectious_dose=50.,
                    ),
                    presence=mc.SpecificInterval(((0, 2),)),
                    mask=models.Mask.types["No mask"],
                    activity=activity_distributions['Seated'],
                    expiration=models.Expiration.types['Talking'],
                ),
            ),
            exposed=mc.Population(
                number=14,
                presence=mc.SpecificInterval(((0, 2),)),
                activity=models.Activity.types['Seated'],
                mask=models.Mask.types["No mask"],
            ),
        )
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min (quarter of an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(1.0)/4
        er_means.append((10**vl) / np.mean(emission_rate))
        er_medians.append(np.median(emission_rate))
        lower_percentiles.append(np.quantile(emission_rate, 0.01))
        upper_percentiles.append(np.quantile(emission_rate, 0.99))

    # divide by 4 to have in 15min (quarter of an hour)
    coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking]

    ax.plot(viral_loads, er_means)
    ax.set_yscale('log')

    new_datapoints = [10**(a) / b for a, b in zip(coleman_etal_vl_talking, coleman_etal_er_talking_2)]
    print(new_datapoints)

    ############# Coleman #############
    plt.scatter(coleman_etal_vl_talking, new_datapoints, marker='x')

    ############# Markers #############
    markers = [5, 'd', 4]

    ############ Legend ############
    result_from_model = mlines.Line2D(
        [], [], color='blue', marker='_', linestyle='None')
    coleman = mlines.Line2D([], [], color='orange',
                            marker='x', linestyle='None')

    title_proxy = Rectangle((0, 0), 0, 0, color='w')
    titles = ["$\\bf{CARA \, \\it{(SARS-CoV-2)}:}$", "$\\bf{Coleman \, et \, al. \, \\it{(SARS-CoV-2)}:}$"]
    leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman],
                     [titles[0], "Result from model", titles[1], "Dataset"])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))

    ############ Plot ############
    plt.title('Exhaled virions while talking for 15min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.ylim([10**0, 10**10])
    plt.show()

    return er_means

def exposure_model_from_vl_talking(viral_loads):

    for vl in tqdm(viral_loads):
        exposure_mc = mc.ExposureModel(
            concentration_model=mc.ConcentrationModel(
                room=models.Room(volume=100, humidity=0.5),
                ventilation=models.AirChange(
                    active=models.SpecificInterval(((0, 24),)),
                    air_exch=0.25,
                ),
                infected=mc.InfectedPopulation(
                    number=1,
                    virus=models.Virus(
                        viral_load_in_sputum=10**vl,
                        infectious_dose=50.,
                    ),
                    presence=mc.SpecificInterval(((0, 2),)),
                    mask=models.Mask.types["No mask"],
                    activity=activity_distributions['Seated'],
                    expiration=models.Expiration.types['Talking'],
                ),
            ),
            exposed=mc.Population(
                number=14,
                presence=mc.SpecificInterval(((0, 2),)),
                activity=models.Activity.types['Seated'],
                mask=models.Mask.types["No mask"],
            ),
        )
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min (quarter of an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(1.0)/4
        er_means.append(np.mean(emission_rate))
        er_medians.append(np.median(emission_rate))
        lower_percentiles.append(np.quantile(emission_rate, 0.01))
        upper_percentiles.append(np.quantile(emission_rate, 0.99))

    # divide by 4 to have in 15min (quarter of an hour)
    coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking]

    ax.plot(viral_loads, er_means)
    ax.fill_between(viral_loads, lower_percentiles,
                    upper_percentiles, alpha=0.2)
    ax.set_yscale('log')

    ############# Coleman #############
    plt.scatter(coleman_etal_vl_talking, coleman_etal_er_talking_2, marker='x')
    x_hull, y_hull = get_enclosure_points(
        coleman_etal_vl_talking, coleman_etal_er_talking_2)
    # plot shape
    plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)

    ############# Markers #############
    markers = [5, 'd', 4]

    ############ Legend ############
    result_from_model = mlines.Line2D(
        [], [], color='blue', marker='_', linestyle='None')
    coleman = mlines.Line2D([], [], color='orange',
                            marker='x', linestyle='None')

    title_proxy = Rectangle((0, 0), 0, 0, color='w')
    titles = ["$\\bf{CARA \, \\it{(SARS-CoV-2)}:}$", "$\\bf{Coleman \, et \, al. \, \\it{(SARS-CoV-2)}:}$"]
    leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman],
                     [titles[0], "Result from model", titles[1], "Dataset"])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))

    ############ Plot ############
    plt.title('Exhaled virions while talking for 15min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)

    plt.show()

    return er_means

def exposure_model_from_vl_talking_cn(viral_loads):
    
    n_lines = 30
    cns = np.linspace(0.01, 2, n_lines)
    
    cmap = define_colormap(cns)

    for cn in tqdm(cns):
        er_means = []
        for vl in viral_loads:
            exposure_mc = model_scenario("Talking", vl)
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            # divide by 4 to have in 15min (quarter of an hour)
            emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B = 0.1, cn_L = cn) /4
            er_means.append(np.mean(emission_rate))

        # divide by 4 to have in 15min (quarter of an hour)
        coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking] 
        ax.plot(viral_loads, er_means, color=cmap.to_rgba(cn, alpha=0.75), linewidth=0.5)

    er_means = []
    for vl in viral_loads:
        exposure_mc = model_scenario("Talking", vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min 
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B = 0.06, cn_L = 0.2) / 4
        er_means.append(np.mean(emission_rate))
    ax.plot(viral_loads, er_means, color=cmap.to_rgba(cn, alpha=0.75), linewidth=1, ls='--')
    plt.text(viral_loads[int(len(viral_loads)*0.93)], 10**5.5, r"$\mathbf{C_{n,B}=0.2}$", color='black', size='small')

    fig.colorbar(cmap, ticks=[0.01, 0.5, 1.0, 2.0], label="Particle emission concentration for talking.")
    ax.set_yscale('log')

    ############# Coleman #############
    plt.scatter(coleman_etal_vl_talking, coleman_etal_er_talking_2, marker='x', c = 'orange')
    x_hull, y_hull = get_enclosure_points(
        coleman_etal_vl_talking, coleman_etal_er_talking_2)
    # plot shape
    plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)

    ############# Markers #############
    markers = [5, 'd', 4]

    ############ Legend ############
    result_from_model = mlines.Line2D(
        [], [], color='blue', marker='_', linestyle='None')
    coleman = mlines.Line2D([], [], color='orange',
                            marker='x', linestyle='None')

    title_proxy = Rectangle((0, 0), 0, 0, color='w')
    titles = ["$\\bf{CARA \, \\it{(SARS-CoV-2)}:}$", "$\\bf{Coleman \, et \, al. \, \\it{(SARS-CoV-2)}:}$"]
    leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman],
                     [titles[0], "Result from model", titles[1], "Dataset"])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))

    ############ Plot ############
    plt.title('Exhaled virions while talking for 15min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()

    return er_means

def exposure_model_from_vl_breathing(viral_loads):

    for vl in tqdm(viral_loads):
        exposure_mc = mc.ExposureModel(
            concentration_model=mc.ConcentrationModel(
                room=models.Room(volume=100, humidity=0.5),
                ventilation=models.AirChange(
                    active=models.SpecificInterval(((0, 24),)),
                    air_exch=0.25,
                ),
                infected=mc.InfectedPopulation(
                    number=1,
                    virus=models.Virus(
                        viral_load_in_sputum=10**vl,
                        infectious_dose=50.,
                    ),
                    presence=mc.SpecificInterval(((0, 2),)),
                    mask=models.Mask.types["No mask"],
                    activity=activity_distributions['Seated'],
                    expiration=models.Expiration.types['Breathing'],
                ),
            ),
            exposed=mc.Population(
                number=14,
                presence=mc.SpecificInterval(((0, 2),)),
                activity=models.Activity.types['Seated'],
                mask=models.Mask.types["No mask"],
            ),
        )
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 2 to have in 30min (half an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(1.0) / 2
        er_means.append(np.mean(emission_rate))
        er_medians.append(np.median(emission_rate))
        lower_percentiles.append(np.quantile(emission_rate, 0.01))
        upper_percentiles.append(np.quantile(emission_rate, 0.99))

    # divide by 2 to have in 30min (half an hour)
    coleman_etal_er_breathing_2 = [x/2 for x in coleman_etal_er_breathing]
    milton_er_2 = [x/2 for x in milton_er]
    yann_er_2 = [x/2 for x in yann_er]

    ax.plot(viral_loads, er_means)
    ax.fill_between(viral_loads, lower_percentiles,
                    upper_percentiles, alpha=0.2)
    ax.set_yscale('log')

    ############# Coleman #############
    plt.scatter(coleman_etal_vl_breathing,
                coleman_etal_er_breathing_2, marker='x')
    x_hull, y_hull = get_enclosure_points(
        coleman_etal_vl_breathing, coleman_etal_er_breathing_2)
    # plot shape
    plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)

    ############# Markers #############
    markers = [5, 'd', 4]

    ############# Milton et al #############
    try:
        for index, m in enumerate(markers):
            plt.scatter(milton_vl[index], milton_er_2[index],
                        marker=m, color='red')
        x_hull, y_hull = get_enclosure_points(milton_vl, milton_er_2)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='red', alpha=0.2)
    except:
        print("No data for Milton et al")

    ############# Yan et al #############
    try:
        plt.scatter(yann_vl[0], yann_er_2[0], marker=markers[0], color='green')
        plt.scatter(yann_vl[1], yann_er_2[1],
                    marker=markers[1], color='green', s=50)
        plt.scatter(yann_vl[2], yann_er_2[2], marker=markers[2], color='green')

        x_hull, y_hull = get_enclosure_points(yann_vl, yann_er_2)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='green', alpha=0.2)
    except:
        print("No data for Yan et al")

    ############ Legend ############
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
                     [titles[0], "Result from model", titles[1], "Dataset", titles[2], "Mean", "25th per.", "75th per.", titles[3], "Mean", "25th per.", "75th per."])

    # Move titles to the left
    for item, label in zip(leg.legendHandles, leg.texts):
        if label._text in titles:
            width = item.get_window_extent(fig.canvas.get_renderer()).width
            label.set_ha('left')
            label.set_position((-3*width, 0))

    ############ Plot ############
    plt.title('Exhaled virions while breathing for 30 min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()

    return er_means


def exposure_model_from_vl_breathing_cn(viral_loads):

    n_lines = 30
    cns = np.linspace(0.01, 0.5, n_lines)

    cmap = define_colormap(cns) 
    
    for cn in tqdm(cns):
        er_means = []
        for vl in viral_loads:
            exposure_mc = model_scenario("Breathing", vl)
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            # divide by 2 to have in 30min (half an hour)
            emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B = cn, cn_L = 0.2) / 2
            er_means.append(np.mean(emission_rate))

        # divide by 2 to have in 30min (half an hour)
        coleman_etal_er_breathing_2 = [x/2 for x in coleman_etal_er_breathing]
        milton_er_2 = [x/2 for x in milton_er]
        yann_er_2 = [x/2 for x in yann_er]
        ax.plot(viral_loads, er_means, color=cmap.to_rgba(cn, alpha=0.75), linewidth=0.5)

    er_means = []
    for vl in viral_loads:
        exposure_mc = model_scenario("Breathing", vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 2 to have in 30min (half an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B = 0.06, cn_L = 0.2) / 2
        er_means.append(np.mean(emission_rate))
    
    ax.plot(viral_loads, er_means, color=cmap.to_rgba(cn, alpha=0.75), linewidth=1, ls='--')
    plt.text(viral_loads[int(len(viral_loads)*0.9)], 10**4, r"$\mathbf{C_{n,B}=0.06}$", color='black', size='small')
    
    fig.colorbar(cmap, ticks=[0.01, 0.1, 0.5], label="Particle emission concentration for breathing.")
    ax.set_yscale('log')

    ############# Coleman #############
    plt.scatter(coleman_etal_vl_breathing,
                coleman_etal_er_breathing_2, marker='x', c='orange')
    x_hull, y_hull = get_enclosure_points(
        coleman_etal_vl_breathing, coleman_etal_er_breathing_2)
    # plot shape
    plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)

    ############# Markers #############
    markers = [5, 'd', 4]

    ############# Milton et al #############
    try:
        for index, m in enumerate(markers):
            plt.scatter(milton_vl[index], milton_er_2[index],
                        marker=m, color='red')
        x_hull, y_hull = get_enclosure_points(milton_vl, milton_er_2)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='red', alpha=0.2)
    except:
        print("No data for Milton et al")

    ############# Yan et al #############
    try:
        plt.scatter(yann_vl[0], yann_er_2[0], marker=markers[0], color='green')
        plt.scatter(yann_vl[1], yann_er_2[1],
                    marker=markers[1], color='green', s=50)
        plt.scatter(yann_vl[2], yann_er_2[2], marker=markers[2], color='green')

        x_hull, y_hull = get_enclosure_points(yann_vl, yann_er_2)
        # plot shape
        plt.fill(x_hull, y_hull, '--', c='green', alpha=0.2)
    except:
        print("No data for Yan et al")

    ############ Legend ############
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

    ############ Plot ############
    plt.title('Exhaled virions while breathing for 30 min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()

    return er_means


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
    cmap = mpl.cm.ScalarMappable(norm=norm, cmap=mpl.colors.LinearSegmentedColormap.from_list("mycmap", colors))
    cmap.set_array([])

    return cmap

def model_scenario(activity, vl):
    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=models.Virus(
                    viral_load_in_sputum=10**vl,
                    infectious_dose=50.,
                ),
                presence=mc.SpecificInterval(((0, 2),)),
                mask=models.Mask.types["No mask"],
                activity=activity_distributions['Seated'],
                expiration=models.Expiration.types[activity],
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=models.Activity.types['Seated'],
            mask=models.Mask.types["No mask"],
        ),
    )
    return exposure_mc


# # Milton
    # boxes = [
    #     {
    #         'label': "Milton data",
    #         'whislo': 0,    # Bottom whisker position
    #         'q1': 22,    # First quartile (25th percentile)
    #         'med': 220,    # Median         (50th percentile)
    #         'q3': 1120,    # Third quartile (75th percentile)
    #         'whishi': 260000,    # Top whisker position
    #         'fliers': []        # Outliers
    #     }
    # ]
    # # `box plot aligned with the viral load value of 5.62325
    # ax.bxp(boxes, showfliers=False, positions=[5.62324929])

    # # Yan

    # boxes = [
    #     {
    #         'whislo': 1424.81,    # Bottom whisker position
    #         'q1': 8396.78,    # First quartile (25th percentile)
    #         'med': 45324.6,    # Median         (50th percentile)
    #         'q3': 400054,    # Third quartile (75th percentile)
    #         'whishi': 88616200,    # Top whisker position
    #         'fliers': []        # Outliers
    #     }
    # ]
    # ax.bxp(boxes, showfliers=False, positions=[9.34786])
    # box plot aligned with the viral load value of 9.34786
