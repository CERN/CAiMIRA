from numpy.core.function_base import linspace
from cara import models
from cara.monte_carlo.data import activity_distributions
from tqdm import tqdm
from matplotlib.patches import Rectangle
from scipy.spatial import ConvexHull
from model_scenarios_paper import *
import cara.monte_carlo as mc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.lines as mlines
import matplotlib as mpl


######### Plot material #########
SAMPLE_SIZE = 50000
viral_loads = np.linspace(2, 12, 600)

############# Markers (for legend) #############
markers = [5, 'd', 4]

""" Exhaled virions from exposure models """

######### Breathing #########


def exposure_model_from_vl_breathing():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    er_means = []
    er_medians = []
    lower_percentiles = []
    upper_percentiles = []

    for vl in tqdm(viral_loads):
        exposure_mc = breathing_exposure_vl(vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 2 to have in 30min (half an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2) / 2
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
    scatter_coleman_data(coleman_etal_vl_breathing,
                         coleman_etal_er_breathing_2)

    ############# Milton et al #############
    scatter_milton_data(milton_vl, milton_er_2)

    ############# Yan et al #############
    scatter_yann_data(yann_vl, yann_er_2)

    ############ Legend ############
    build_breathing_legend(fig)

    ############ Plot ############
    plt.title('Exhaled virions while breathing for 30 min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()


""" Variation according to the BLO model """
############ Breathing ############


def exposure_model_from_vl_breathing_cn():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    n_lines = 30
    cns = np.linspace(0.01, 0.5, n_lines)

    cmap = define_colormap(cns)

    for cn in tqdm(cns):
        er_means = []
        for vl in viral_loads:
            exposure_mc = breathing_exposure_vl(vl)
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            # divide by 2 to have in 30min (half an hour)
            emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(
                cn_B=cn, cn_L=0.2) / 2
            er_means.append(np.mean(emission_rate))

        # divide by 2 to have in 30min (half an hour)
        coleman_etal_er_breathing_2 = [x/2 for x in coleman_etal_er_breathing]
        milton_er_2 = [x/2 for x in milton_er]
        yann_er_2 = [x/2 for x in yann_er]
        ax.plot(viral_loads, er_means, color=cmap.to_rgba(
            cn, alpha=0.75), linewidth=0.5)

    # The dashed line for the chosen Cn,B
    er_means = []
    for vl in viral_loads:
        exposure_mc = breathing_exposure_vl(vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 2 to have in 30min (half an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(
            cn_B=0.06, cn_L=0.2) / 2
        er_means.append(np.mean(emission_rate))

    ax.plot(viral_loads, er_means, color=cmap.to_rgba(
        cn, alpha=0.75), linewidth=1, ls='--')
    plt.text(viral_loads[int(len(viral_loads)*0.9)], 10**4.2,
             r"$\mathbf{c_{n,B}=0.06}$", color=cmap.to_rgba(cn), size='small')

    fig.colorbar(cmap, ticks=[0.01, 0.1, 0.25, 0.5],
                 label="Particle emission concentration, ${c_{n,B}}$")
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
    plt.title('Exhaled virions while breathing for 30 min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
    plt.show()

############ Talking ############

def exposure_model_from_vl_talking():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    er_means = []
    er_medians = []
    lower_percentiles = []
    upper_percentiles = []

    for vl in tqdm(viral_loads):
        exposure_mc = talking_exposure_vl(vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min (quarter of an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(cn_B=0.06, cn_L=0.2)/4
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
    scatter_coleman_data(coleman_etal_vl_talking, coleman_etal_er_talking_2)

    ############ Legend ############
    build_talking_legend(fig)

    ############ Plot ############
    plt.title('Exhaled virions while talking for 15min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)

    plt.show()

def exposure_model_from_vl_talking_cn():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    n_lines = 30
    cns = np.linspace(0.01, 2, n_lines)
    cmap = define_colormap(cns)

    for cn in tqdm(cns):
        er_means = []
        for vl in viral_loads:
            exposure_mc = talking_exposure_vl(vl)
            exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
            # divide by 4 to have in 15min (quarter of an hour)
            emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(
                cn_B=0.1, cn_L=cn) / 4
            er_means.append(np.mean(emission_rate))

        # divide by 4 to have in 15min (quarter of an hour)
        coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking]
        ax.plot(viral_loads, er_means, color=cmap.to_rgba(
            cn, alpha=0.75), linewidth=0.5)

    # The dashed line for the chosen Cn,L
    er_means = []
    for vl in viral_loads:
        exposure_mc = talking_exposure_vl(vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(
            cn_B=0.06, cn_L=0.2) / 4
        er_means.append(np.mean(emission_rate))
    ax.plot(viral_loads, er_means, color=cmap.to_rgba(
        cn, alpha=0.75), linewidth=1, ls='--')
    plt.text(viral_loads[int(len(viral_loads)*0.93)], 10**5.5,
             r"$\mathbf{c_{n,L}=0.2}$", color=cmap.to_rgba(cn), size='small')

    fig.colorbar(cmap, ticks=[0.01, 0.5, 1.0, 2.0],
                 label="Particle emission concentration, ${c_{n,L}}$")
    ax.set_yscale('log')

    ############# Coleman #############
    scatter_coleman_data(coleman_etal_vl_talking, coleman_etal_er_talking_2)

    ############ Legend ############
    build_talking_legend(fig)

    ############ Plot ############
    plt.title('Exhaled virions while talking for 15min',
              fontsize=16, fontweight="bold")
    plt.ylabel(
        'Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
    plt.xticks(ticks=[i for i in range(2, 13)], labels=[
        '$10^{' + str(i) + '}$' for i in range(2, 13)])
    plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
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
                     [titles[0], "Result from model", titles[1], "Dataset"])

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
