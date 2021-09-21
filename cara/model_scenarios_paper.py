from cara import models
from cara.monte_carlo.data import activity_distributions, symptomatic_vl_frequencies, viable_to_RNA_ratio_distribution, infectious_dose_distribution, expiration_distributions
import cara.monte_carlo as mc
import numpy as np
from cara.monte_carlo.sampleable import Normal,LogNormal,LogCustomKernel,CustomKernel,Uniform
from cara.monte_carlo.data import BLOmodel
import typing
from cara.apps.calculator.model_generator import build_expiration

######### Scatter points (data taken: copies per hour) #########

############# Coleman #############
############# Coleman - Breathing #############
coleman_etal_vl_breathing = [np.log10(821065925.4), np.log10(1382131207), np.log10(81801735.96), np.log10(
    487760677.4), np.log10(2326593535), np.log10(1488879159), np.log10(884480386.5)]
coleman_etal_er_breathing = [127, 455.2, 281.8, 884.2, 448.4, 1100.6, 621]
############# Coleman - Talking #############
coleman_etal_vl_talking = [np.log10(70492378.55), np.log10(7565486.029), np.log10(7101877592), np.log10(1382131207),
                           np.log10(821065925.4), np.log10(1382131207), np.log10(
                               81801735.96), np.log10(487760677.4),
                           np.log10(2326593535), np.log10(1488879159), np.log10(884480386.5)]
coleman_etal_er_talking = [1668, 938, 319.6, 3632.8, 1243.6,
                           17344, 2932, 5426, 5493.2, 1911.6, 9714.8]

############# Milton et al #############
milton_vl = [np.log10(8.30E+04), np.log10(4.20E+05), np.log10(1.80E+06)]
milton_er = [22, 220, 1120]
############# Milton et al #############

yann_vl = [np.log10(7.86E+07), np.log10(2.23E+09), np.log10(1.51E+10)]
yann_er = [8396.78166, 45324.55964, 400054.0827]

def cn_expiration_distribution(BLO_factors, cn_values):
    """
    Returns an Expiration with an aerosol diameter distribution, defined
    by the BLO factors (a length-3 tuple).
    The total concentration of aerosols is computed by integrating
    the distribution between 0.1 and 30 microns - these boundaries are
    an historical choice based on previous implementations of the model
    (it limits the influence of the O-mode).
    """
    dscan = np.linspace(0.1, 30. ,3000)
    return mc.Expiration(CustomKernel(dscan,
                BLOmodel(BLO_factors, cn_values).distribution(dscan),kernel_bandwidth=0.1),
                BLOmodel(BLO_factors, cn_values).integrate(0.1, 30.))

expiration_BLO_factors = {
    'Breathing': (1., 0., 0.),
    'Talking':   (1., 1., 1.),
    'Singing':   (1., 5., 5.),
    'Shouting':  (1., 5., 5.),
}

######### Standard exposure models ###########

def exposure_module(activity: str, expiration: str, mask: str):
    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=mc.Virus(
                    viral_load_in_sputum=symptomatic_vl_frequencies,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                presence=mc.SpecificInterval(((0, 2),)),
                mask=models.Mask.types[mask],
                activity=activity_distributions[activity],
                expiration=expiration_distributions[expiration],
                host_immunity=0.,
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=activity_distributions[activity],
            mask=models.Mask.types[mask],
            host_immunity=0.,
        ),
    )
    return exposure_mc

######### Exposure model for specific viral load ###########
def exposure_vl(activity: str, expiration: str, mask: str, vl: float):
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
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                presence=mc.SpecificInterval(((0, 2),)),
                mask=models.Mask.types[mask],
                activity=activity_distributions[activity],
                expiration=expiration_distributions[expiration],
                host_immunity=0.,
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=activity_distributions[activity],
            mask=models.Mask.types[mask],
            host_immunity=0.,
        ),
    )
    return exposure_mc

######### Exposure model for specific viral load ###########
def exposure_vl_cn(activity: str, expiration: str, mask: str, vl: float, cn: typing.Tuple[float, float, float]):
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
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                presence=mc.SpecificInterval(((0, 2),)),
                mask=models.Mask.types[mask],
                activity=activity_distributions[activity],
                expiration=cn_expiration_distribution(expiration_BLO_factors[expiration], cn),
                host_immunity=0.,
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=activity_distributions[activity],
            mask=models.Mask.types[mask],
            host_immunity=0.,
        ),
    )
    return exposure_mc

########## Concentration curves for specific scenarios ###########
def office_model_no_mask_windows_closed():
    office_model_no_vent = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=160, humidity=0.3),
            ventilation=models.MultipleVentilation(
                (models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.0), 
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25))),
            infected=mc.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(present_times = ((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=symptomatic_vl_frequencies,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types["No mask"],
                activity=activity_distributions['Seated'],
                expiration=build_expiration({'Talking': 0.33, 'Breathing': 0.67}),
                host_immunity=0.,
            )
        ),
        exposed=models.Population(
            number=18,
            presence=models.SpecificInterval(present_times = ((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        )
    )
    return office_model_no_vent

def office_model_no_mask_windows_open_breaks():
    office_model_no_vent = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=160, humidity=0.3),
            ventilation = models.MultipleVentilation(
                ventilations=(
                    models.SlidingWindow(
                        active=models.SpecificInterval(present_times=((1.5, 2), (3.5, 4.5), (6, 6.5))),
                        inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                        outside_temp=models.PiecewiseConstant((0, 24), (291,)),
                        window_height=1.6, 
                        opening_length=0.6,
                    ),
                    models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
                )  
            ),
            infected=mc.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(present_times=((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=symptomatic_vl_frequencies,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types["No mask"],
                activity=activity_distributions['Seated'],
                expiration=build_expiration({'Talking': 0.33, 'Breathing': 0.67}),
                host_immunity=0.,
            )
        ),
        exposed=models.Population(
            number=18,
            presence=models.SpecificInterval(present_times=((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        )
    )
    return office_model_no_vent

def office_model_no_mask_windows_open_alltimes():
    office_model_no_vent = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=160, humidity=0.3),
            ventilation=models.MultipleVentilation(
                ventilations=(
                    models.SlidingWindow(
                        active=models.PeriodicInterval(period=120, duration=120),
                        inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                        outside_temp=models.PiecewiseConstant((0, 24), (291,)),
                        window_height=1.6, opening_length=0.6,
                    ),
                    models.AirChange(active=models.PeriodicInterval(period=120, duration=120), air_exch=0.25),
                )
            ),
            infected=mc.InfectedPopulation(
                number=1,
                presence=models.SpecificInterval(present_times=((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
                virus=mc.SARSCoV2(
                    viral_load_in_sputum=symptomatic_vl_frequencies,
                    infectious_dose=infectious_dose_distribution,
                    viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                    transmissibility_factor=1.,
                ),
                mask=models.Mask.types["No mask"],
                activity=activity_distributions['Seated'],
                expiration=build_expiration({'Talking': 0.33, 'Breathing': 0.67}),
                host_immunity=0.,
            )
        ),
        exposed=models.Population(
            number=18,
            presence=models.SpecificInterval(present_times=((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            activity=activity_distributions['Seated'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        )
    )
    return office_model_no_vent