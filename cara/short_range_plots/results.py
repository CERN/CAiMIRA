""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 18/02/2021
Code version: 4.0.0
"""

from email.mime import base
from cara.models import ExposureModel, InfectedPopulation
from model_scenarios import *
from scripts import *
from itertools import product
from dataclasses import dataclass
from cara.monte_carlo.data import symptomatic_vl_frequencies

# print('\n<<<<<<<<<<< Peak viral concentration without short range for baseline scenarios >>>>>>>>>>>')
# concentration_curve(models = [exposure_module_without_short_range(activity='Seated', expiration='Breathing', mask='No mask')],
#                             labels = ['Baseline'],
#                             colors = ['royalblue'],
# )

# print('\n<<<<<<<<<<< Peak viral concentration with short range interactions for baseline scenarios >>>>>>>>>>>')
# concentration_curve(models=[exposure_module_with_short_range(
#                                     activity='Seated', 
#                                     expiration={"Speaking": 1, "Breathing": 2}, 
#                                     mask='No mask',
#                                     sr_presence=[(10.5, 11.0), (15.5, 16.0)],
#                                     sr_activities=['Breathing', 'Shouting']),
#                             exposure_module_without_short_range(
#                                 activity='Seated', 
#                                 expiration={"Speaking": 1, "Breathing": 2}, 
#                                 mask='No mask',
#                             )],
#                             labels = ['Mean concentration with short range interactions', 'Mean concentration without short range interactions'],
#                             colors = ['royalblue', 'darkviolet'],
#                             linestyles = ['-', '-'],
#                             thickness = [2, 2.5])

# print('\n<<<<<<<<<<< Probability of infections vs exposure time >>>>>>>>>>>')
# Always assume 1h for the short range interactions.
# Always assume that in each model there is only ONE short range interaction.
# plot_pi_vs_exposure_time(exp_models = [
#                             baseline_model(
#                                 activity='Seated', 
#                                 expiration={"Speaking": 2, "Breathing": 1}, 
#                                 mask='No mask',
#                                 sr_presence=[(10.0, 11.0)],
#                                 sr_activities=['Breathing']),
#                             baseline_model(
#                                 activity='Seated', 
#                                 expiration={"Shouting": 2, "Breathing": 1}, 
#                                 mask='No mask',
#                                 sr_presence=[(10.0, 11.0)],
#                                 sr_activities=['Shouting'])],
#                          labels = ['Baseline model breathing', 'Baseline model shouting'],
#                          colors=['royalblue', 'darkviolet'],
#                          linestyles=['solid', 'solid'],
#                          points=20,
#                          time_in_minutes=True,
#                          normalize_y_axis=True)

