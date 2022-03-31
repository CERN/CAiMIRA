""" Title: CARA - COVID Airborne Risk Assessment
Author: A. Henriques et al
Date: 31/03/2022
Code version: 4.0.0 """

from cara import models, data
from cara.monte_carlo.data import activity_distributions, mask_distributions, virus_distributions, expiration_distributions, viable_to_RNA_ratio_distribution, infectious_dose_distribution
import cara.monte_carlo as mc
import numpy as np
import typing
from cara.apps.calculator.model_generator import build_expiration

_VectorisedFloat = typing.Union[float, np.ndarray]

######### Exposure model for specific viral load ###########
def exposure_vl(activity: str, expiration: str, mask: str, vl: float, virus_t_factor: float, hi: float):
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
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=10**vl,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=virus_t_factor,
                ),
                presence=mc.SpecificInterval(((0, 2),)),
                mask=exposure_mask,
                activity=activity_distributions[activity],
                expiration=expiration_distributions[expiration],
                host_immunity=hi,
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=activity_distributions[activity],
            mask=exposure_mask,
            host_immunity=hi,
        ),
    )
    return exposure_mc

def classroom_model_lunch_vent(mask: str, lunch_break: bool, ventilation: bool, hepa: bool):
    volume = 160

    if mask == 'No mask':
        exposure_mask = models.Mask.types['No mask']
    else:
        exposure_mask = mask_distributions[mask]

    if lunch_break:
        presence_break = models.SpecificInterval(((0, 4), (5, 9)))
    else:
        presence_break = models.SpecificInterval(((0, 9),))

    if ventilation:
        if hepa:
            vent = models.MultipleVentilation(
                ventilations= (models.SlidingWindow(
                                    active=models.PeriodicInterval(period=120, duration=60),
                                    inside_temp=models.PiecewiseConstant((0., 24.), (293,)),
                                    outside_temp=data.GenevaTemperatures['Dec'],
                                    window_height=1.6,
                                    opening_length=0.5,
                                ),
                                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
                                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                      q_air_mech=volume*5))
            )
        elif not hepa:
            vent = models.MultipleVentilation(
                ventilations= (models.SlidingWindow(
                                    active=models.PeriodicInterval(period=120, duration=120),
                                    inside_temp=models.PiecewiseConstant((0., 24.), (293,)),
                                    outside_temp=data.GenevaTemperatures['Dec'],
                                    window_height=1.6,
                                    opening_length=0.5,
                                ),
                                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25)))
    elif not ventilation:
        if hepa:
            vent = models.MultipleVentilation(
                ventilations= ( models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
                                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                      q_air_mech=volume*5))
            )
        elif not hepa:
            vent = models.MultipleVentilation(
                (models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.0),
                 models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25)))


    return mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=volume, humidity=0.3),
            ventilation = vent,
            infected=mc.InfectedPopulation(
                number=1,
                presence=presence_break,
                virus=virus_distributions['SARS_CoV_2_OMICRON'],
                mask=exposure_mask,
                activity=activity_distributions['Light activity'],
                expiration=build_expiration('Speaking'),
                host_immunity=0.,
            )
        ),
        exposed=mc.Population(
            number=19,
            presence=presence_break,
            activity=activity_distributions['Seated'],
            mask=exposure_mask,
            host_immunity=0.,
        )
    )