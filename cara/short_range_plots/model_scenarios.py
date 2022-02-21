""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 18/02/2021
Code version: 4.0.0
"""

from cara import models, data
from cara.monte_carlo.data import activity_distributions, short_range_expiration_distributions, mask_distributions, virus_distributions, dilution_factor
import cara.monte_carlo as mc
import numpy as np
from cara.monte_carlo.sampleable import CustomKernel
from cara.monte_carlo.data import BLOmodel
import typing
from cara.apps.calculator.model_generator import build_expiration

_VectorisedFloat = typing.Union[float, np.ndarray]

scenario_activity_and_expiration = {
    'office': (
        'Seated',
        # Mostly silent in the office, but 1/3rd of time speaking.
        {'Speaking': 1, 'Breathing': 2}
    ),
    'controlroom-day': (
        'Seated',
        # Daytime control room shift, 50% speaking.
        {'Speaking': 1, 'Breathing': 1}
    ),
    'controlroom-night': (
        'Seated',
        # Nightshift control room, 10% speaking.
        {'Speaking': 1, 'Breathing': 9}
    ),
    # 'meeting': (
    #     'Seated',
    #     # Conversation of N people is approximately 1/N% of the time speaking.
    #     {'Speaking': 1, 'Breathing': self.total_people - 1}
    # ),
    'callcentre': ('Seated', 'Speaking'),
    'library': ('Seated', 'Breathing'),
    'training': ('Standing', 'Speaking'),
    'lab': (
        'Light activity',
        #Model 1/2 of time spent speaking in a lab.
        {'Speaking': 1, 'Breathing': 1}),
    'workshop': (
        'Moderate activity',
        #Model 1/2 of time spent speaking in a workshop.
        {'Speaking': 1, 'Breathing': 1}),
    'gym':('Heavy exercise', 'Breathing'),
    }

######### Standard exposure models ###########
def exposure_module_without_short_range(activity: str, expiration: str, mask: str):
    if mask == 'No mask':
        exposure_mask = models.Mask.types['No mask']
    else:
        exposure_mask = mask_distributions[mask]

    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2_OMICRON'],
                presence=mc.SpecificInterval(((8.5, 12.5),(13.5, 17.5),)),
                mask=exposure_mask,
                activity=activity_distributions[activity],
                expiration=build_expiration(expiration),
                host_immunity=0.,
            ),
        ),
        short_range=mc.ShortRangeModel(
            presence=[],
            expirations=[],
            dilutions=[]
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((8.5, 12.5),(13.5, 17.5),)),
            activity=activity_distributions[activity],
            mask=exposure_mask,
            host_immunity=0.,
        ),
    )
    return exposure_mc

def exposure_module_with_short_range(activity: str, expiration: str, mask: str, sr_presence: list, sr_activities: list):
    if mask == 'No mask':
        exposure_mask = models.Mask.types['No mask']
    else:
        exposure_mask = mask_distributions[mask]

    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2_OMICRON'],
                presence=mc.SpecificInterval(((8.5, 12.5),(13.5, 17.5),)),
                mask=exposure_mask,
                activity=activity_distributions[activity],
                expiration=build_expiration(expiration),
                host_immunity=0.,
            ),
        ),
        short_range=mc.ShortRangeModel(
            presence=[models.SpecificInterval(interval) for interval in sr_presence],
            expirations=[short_range_expiration_distributions[activity] for activity in sr_activities],
            dilutions=dilution_factor(activities=sr_activities,
                        distance=np.random.uniform(0.5, 1.5, 250000)),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((8.5, 12.5),(13.5, 17.5),)),
            activity=activity_distributions[activity],
            mask=exposure_mask,
            host_immunity=0.,
        ),
    )
    return exposure_mc

def exposure_module_with_short_range_outdoors(activity: str, expiration: str, mask: str, sr_presence: list, sr_activities: list):
    if mask == 'No mask':
        exposure_mask = models.Mask.types['No mask']
    else:
        exposure_mask = mask_distributions[mask]

    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100000, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=1000000,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2_OMICRON'],
                presence=mc.SpecificInterval(((8.5, 12.5),)),
                mask=exposure_mask,
                activity=activity_distributions[activity],
                expiration=build_expiration(expiration),
                host_immunity=0.,
            ),
        ),
        short_range=mc.ShortRangeModel(
            presence=[models.SpecificInterval(interval) for interval in sr_presence],
            expirations=[short_range_expiration_distributions[activity] for activity in sr_activities],
            dilutions=dilution_factor(activities=sr_activities,
                        distance=np.random.uniform(0.5, 1.5, 250000)),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((8.5, 12.5),)),
            activity=activity_distributions[activity],
            mask=exposure_mask,
            host_immunity=0.,
        ),
    )
    return exposure_mc


def baseline_model(activity: str, expiration: str, mask: str, sr_presence: list, sr_activities: list):
    if mask == 'No mask':
        exposure_mask = models.Mask.types['No mask']
    else:
        exposure_mask = mask_distributions[mask]

    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=10, humidity=0.5),
            ventilation=models.AirChange(
                active=models.PeriodicInterval(period=120, duration=120),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2_OMICRON'],
                presence=models.SpecificInterval(((8.5, 12.5),)),
                mask=exposure_mask,
                activity=activity_distributions[activity],
                expiration=build_expiration(expiration),
                host_immunity=0.,
            ),
        ),
        short_range=mc.ShortRangeModel(
            presence=[models.SpecificInterval(interval) for interval in sr_presence],
            expirations=[short_range_expiration_distributions[activity] for activity in sr_activities],
            dilutions=dilution_factor(activities=sr_activities,
                        distance=np.random.uniform(0.5, 1.5, 250000)),
        ),
        exposed=mc.Population(
            number=3,
            presence=models.SpecificInterval(((8.5, 12.5),)),
            activity=activity_distributions[activity],
            mask=exposure_mask,
            host_immunity=0.,
        ),
    )
    return exposure_mc