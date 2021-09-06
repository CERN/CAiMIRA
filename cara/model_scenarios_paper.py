from cara import models
from cara.monte_carlo.data import activity_distributions, virus_distributions
import cara.monte_carlo as mc
import numpy as np

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

######### Standard exposure models ###########

######### Breathing model ###########
def breathing_exposure():
    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2'],
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
    return exposure_mc

######### Talking model ###########
def talking_exposure():
    exposure_mc = mc.ExposureModel(
        concentration_model=mc.ConcentrationModel(
            room=models.Room(volume=100, humidity=0.5),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0, 24),)),
                air_exch=0.25,
            ),
            infected=mc.InfectedPopulation(
                number=1,
                virus=virus_distributions['SARS_CoV_2'],
                presence=mc.SpecificInterval(((0, 2),)),
                mask=models.Mask.types["No mask"],
                activity=activity_distributions['Seated'],
                expiration=models.Expiration.types['Talking'],
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=models.Activity.types['Seated'],
            mask=models.Mask.types["No mask"],
        ),
    )
    return exposure_mc

######### Breathing model for specific viral load ###########
def breathing_exposure_vl(vl):
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
    return exposure_mc

######### Talking model for specific viral load ###########
def talking_exposure_vl(vl):
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
                expiration=models.Expiration.types['Talking'],
            ),
        ),
        exposed=mc.Population(
            number=14,
            presence=mc.SpecificInterval(((0, 2),)),
            activity=models.Activity.types['Seated'],
            mask=models.Mask.types["No mask"],
        ),
    )
    return exposure_mc
