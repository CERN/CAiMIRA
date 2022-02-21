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
#                                     activity='Light activity',
#                                     expiration={"Speaking": 1, "Breathing": 2},
#                                     mask='No mask',
#                                     sr_presence=[(10.5, 11.0), (15.0, 16.0)],
#                                     sr_activities=['Breathing', 'Speaking']),
#                             exposure_module_without_short_range(
#                                 activity='Light activity',
#                                 expiration={"Speaking": 1, "Breathing": 2},
#                                 mask='No mask',)
#                             ],
#                             labels = ['Concentration with short range interactions', 'Background (long-range) concentration'],
#                             labelsDose = ['Dose (full)', 'Dose (long-range)'],
#                             colors = ['salmon', 'royalblue'],
#                             linestyles = ['-', '--'],
#                             thickness = [2, 2])

print('\n<<<<<<<<<<< Dose vs SR exposure time >>>>>>>>>>>')
#Always assume 1h for the short range interactions.
#Always assume that in each model there is only ONE short range interaction.
plot_vD_vs_exposure_time(exp_models = [
                            baseline_model(
                                activity='Light activity',
                                expiration={"Speaking": 2, "Breathing": 1},
                                mask='No mask',
                                sr_presence=[(8.5, 9.5)],
                                sr_activities=['Breathing']),
                            baseline_model(
                                activity='Light activity',
                                expiration={"Speaking": 2, "Breathing": 1},
                                mask='No mask',
                                sr_presence=[(8.5, 9.5)],
                                sr_activities=['Speaking'])],
                         labels = ['Baseline model breathing', 'Baseline model speaking'],
                         colors=['royalblue', 'darkviolet'],
                         linestyles=['solid', 'solid'],
                         points=20,
                         time_in_minutes=True,
                         normalize_y_axis=True)

