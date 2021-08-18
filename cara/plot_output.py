from dataclasses import field
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Rectangle
import pandas as pd
import csv

import cara.monte_carlo as mc
from cara import models
from cara.monte_carlo.data import activity_distributions
from tqdm import tqdm
from scipy.spatial import ConvexHull


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


SAMPLE_SIZE = 50000

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

points = 600
viral_loads = np.linspace(2, 12, points)

er_means = []
er_medians = []
lower_percentiles = []
upper_percentiles = []

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
    emission_rate = exposure_model.concentration_model.infected.emission_rate_when_present()
    er_means.append(np.mean(emission_rate))
    er_medians.append(np.median(emission_rate))
    lower_percentiles.append(np.quantile(emission_rate, 0.01))
    upper_percentiles.append(np.quantile(emission_rate, 0.99))

with open('data.csv', 'w', newline='') as csvfile:
    fieldnames = ['viral load', 'emission rate']
    thewriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
    thewriter.writeheader()
    for i, vl in enumerate(viral_loads):
        thewriter.writerow(
            {'viral load': 10**vl, 'emission rate': er_means[i]})

ax.plot(viral_loads, er_means)
ax.fill_between(viral_loads, lower_percentiles,
                upper_percentiles, alpha=0.2)
ax.set_yscale('log')

############# Coleman #############
coleman_etal_vl = [np.log10(821065925.4), np.log10(1382131207), np.log10(81801735.96), np.log10(
    487760677.4), np.log10(2326593535), np.log10(1488879159), np.log10(884480386.5)]
coleman_etal_er = [127, 455.2, 281.8, 884.2, 448.4, 1100.6, 621]
plt.scatter(coleman_etal_vl, coleman_etal_er)
x_hull, y_hull = get_enclosure_points(coleman_etal_vl, coleman_etal_er)
# plot shape
plt.fill(x_hull, y_hull, '--', c='orange', alpha=0.2)

############# Markers #############
markers = ['*', 'v', 's']

############# Milton et al #############
milton_vl = [np.log10(8.30E+04), np.log10(4.20E+05), np.log10(1.80E+06)]
milton_er = [22, 220, 1120]  # removed first and last due to its dimensions
plt.scatter(milton_vl[0], milton_er[0], marker=markers[0], color='red')
plt.scatter(milton_vl[1], milton_er[1], marker=markers[1], color='red')
plt.scatter(milton_vl[2], milton_er[2], marker=markers[2], color='red')
x_hull, y_hull = get_enclosure_points(milton_vl, milton_er)
# plot shape
plt.fill(x_hull, y_hull, '--', c='red', alpha=0.2)

############# Yan et al #############
# removed first and last due to its dimensions
yan_vl = [np.log10(7.86E+07), np.log10(2.23E+09), np.log10(1.51E+10)]
yan_er = [8396.78166, 45324.55964, 400054.0827]
plt.scatter(yan_vl[0], yan_er[0], marker=markers[0], color='green')
plt.scatter(yan_vl[1], yan_er[1], marker=markers[1], color='green')
plt.scatter(yan_vl[2], yan_er[2], marker=markers[2], color='green')

x_hull, y_hull = get_enclosure_points(yan_vl, yan_er)
# plot shape
plt.fill(x_hull, y_hull, '--', c='green', alpha=0.2)

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

############ Legend ############
result_from_model = mlines.Line2D(
    [], [], color='blue', marker='_', linestyle='None')
coleman = mlines.Line2D([], [], color='orange', marker='o', linestyle='None')
milton_mean = mlines.Line2D(
    [], [], color='red', marker='v', linestyle='None')  # mean
milton_25 = mlines.Line2D(
    [], [], color='red', marker='*', linestyle='None')  # 25
milton_75 = mlines.Line2D(
    [], [], color='red', marker='s', linestyle='None')  # 75
yann_mean = mlines.Line2D([], [], color='green',
                          marker='v', linestyle='None')  # mean
yann_25 = mlines.Line2D([], [], color='green',
                        marker='*', linestyle='None')  # 25
yann_75 = mlines.Line2D([], [], color='green',
                        marker='s', linestyle='None')  # 75

title_proxy = Rectangle((0, 0), 0, 0, color='w')
titles = ["$\\bf{CARA \, (SARS-CoV-2):}$", "$\\bf{Coleman \, et \, al. \, (SARS-CoV-2):}$",
          "$\\bf{Milton \, et \, al.  \,(Influenza):}$", "$\\bf{Yann \, et \, al.  \,(Influenza):}$"]
leg = plt.legend([title_proxy, result_from_model, title_proxy, coleman, title_proxy, milton_mean, milton_25, milton_75, title_proxy, yann_mean, yann_25, yann_75],
                 [titles[0], "Result from model", titles[1], "Dataset", titles[2], "Mean", "25th per.", "75th per.", titles[3], "Mean", "25th per.", "75th per."])

# Move titles to the left
for item, label in zip(leg.legendHandles, leg.texts):
    if label._text in titles:
        width = item.get_window_extent(fig.canvas.get_renderer()).width
        label.set_ha('left')
        label.set_position((-3*width, 0))


############ Plot ############
plt.title('Exhaled virions while breathing for 1h', fontsize=16, fontweight="bold")
plt.ylabel('Aerosol viral load, $\mathrm{vl_{out}}$\n(RNA copies)', fontsize=14)
plt.xticks(ticks=[i for i in range(2, 13)], labels=[
    '$10^{' + str(i) + '}$' for i in range(2, 13)])
plt.xlabel('NP viral load, $\mathrm{vl_{in}}$\n(RNA copies)', fontsize=14)
plt.show()
