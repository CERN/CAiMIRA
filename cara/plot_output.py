from dataclasses import field
import numpy as np
import matplotlib.pyplot as plt
import csv

import cara.monte_carlo as mc
from cara import models, data
from cara.monte_carlo.data import activity_distributions
from tqdm import tqdm

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
                expiration=models.MultipleExpiration(
                    expirations=(models.Expiration.types['Talking'],
                                 models.Expiration.types['Breathing']),
                    weights=(0.3, 0.7)),
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

coleman_etal_vl = [8.914378029, 9.140549273, 7.91276252,
                   8.688206785, 9.366720517, 9.172859451, 8.946688207]
coleman_etal_er = [127, 455.2, 281.8, 884.2, 448.4, 1100.6, 621]
plt.scatter(coleman_etal_vl, coleman_etal_er)

milton_vl = [5.62324929]
milton_er = [220]
plt.scatter(milton_vl, milton_er)

yan_vl = [9.347856705]
yan_er = [45324.55964]
plt.scatter(yan_vl, yan_er)

# Milton
boxes = [
    {
        'label': "Milton data",
        'whislo': 0,    # Bottom whisker position
        'q1': 22,    # First quartile (25th percentile)
        'med': 220,    # Median         (50th percentile)
        'q3': 1120,    # Third quartile (75th percentile)
        'whishi': 260000,    # Top whisker position
        'fliers': []        # Outliers
    }
]
# `box plot aligned with the viral load value of 5.62325
ax.bxp(boxes, showfliers=False, positions=[5.62324929])

# Yan

boxes = [
    {
        'whislo': 1424.81,    # Bottom whisker position
        'q1': 8396.78,    # First quartile (25th percentile)
        'med': 45324.6,    # Median         (50th percentile)
        'q3': 400054,    # Third quartile (75th percentile)
        'whishi': 88616200,    # Top whisker position
        'fliers': []        # Outliers
    }
]
ax.bxp(boxes, showfliers=False, positions=[9.34786])

# box plot aligned with the viral load value of 9.34786

plt.title('Exhaled virions while breathing for 1h', fontsize=14)
plt.ylabel('RNA copies', fontsize=12)
plt.xticks(ticks=[i for i in range(2, 13)], labels=[
    '$10^{' + str(i) + '}$' for i in range(2, 13)])
plt.xlabel('NP viral load (RNA copies mL$^{-1}$)', fontsize=12)
plt.show()
