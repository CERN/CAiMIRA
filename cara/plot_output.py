from cara.model_scenarios import *
import numpy as np
import csv

viral_loads = np.linspace(2, 12, 600)

#er_means = exposure_model_from_vl_talking(viral_loads)
#er_means = exposure_model_from_vl_breathing(viral_loads)
#er_means = exposure_model_from_vl_talking_new_points(viral_loads)
#er_means = exposure_model_from_vl_talking_cn(viral_loads)
er_means = exposure_model_from_vl_breathing_cn(viral_loads)

with open('data.csv', 'w', newline='') as csvfile:
    fieldnames = ['viral load', 'emission rate']
    thewriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
    thewriter.writeheader()
    for i, vl in enumerate(viral_loads):
        thewriter.writerow(
            {'viral load': 10**vl, 'emission rate': er_means[i]})
