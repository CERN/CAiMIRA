from dataclasses import field
import numpy as np
import matplotlib.pyplot as plt
import csv

import cara.monte_carlo as mc
from cara import models,data
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
                    viral_load_in_sputum = 10**vl,
                    infectious_dose = 50.,
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
        thewriter.writerow({'viral load' : 10**vl, 'emission rate' : er_means[i]})


ax.plot(viral_loads, er_means)
ax.fill_between(viral_loads, lower_percentiles,
                upper_percentiles, alpha=0.2)
ax.set_yscale('log')
plt.title('Emission rate vs Viral Load')
plt.ylabel('ER (Virions/h)', fontsize=14)
plt.xticks(ticks=[i for i in range(2, 13)], labels=[
            '$10^{' + str(i) + '}$' for i in range(2, 13)])
plt.xlabel('Viral load (RNA copies mL$^{-1}$)', fontsize=14)
plt.show()
