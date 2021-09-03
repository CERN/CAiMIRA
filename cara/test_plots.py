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
from model_scenarios_paper import *

# Used for testing

######### Plot material #########

SAMPLE_SIZE = 50000
viral_loads = np.linspace(2, 12, 600)

er_means = []
er_medians = []
lower_percentiles = []
upper_percentiles = []
def exposure_model_from_vl_talking_new_points():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    
    for vl in tqdm(viral_loads):
        exposure_mc = talking_exposure_vl(vl)
        exposure_model = exposure_mc.build_model(size=SAMPLE_SIZE)
        # divide by 4 to have in 15min (quarter of an hour)
        emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present(
            1.0)/4
        er_means.append((10**vl) / np.mean(emission_rate))
        er_medians.append(np.median(emission_rate))
        lower_percentiles.append(np.quantile(emission_rate, 0.01))
        upper_percentiles.append(np.quantile(emission_rate, 0.99))

    # divide by 4 to have in 15min (quarter of an hour)
    coleman_etal_er_talking_2 = [x/4 for x in coleman_etal_er_talking]

    ax.plot(viral_loads, er_means)
    ax.set_yscale('log')

    new_datapoints = [
        10**(a) / b for a, b in zip(coleman_etal_vl_talking, coleman_etal_er_talking_2)]
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
    