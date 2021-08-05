from cara import models
import monte_carlo as mc
from cara.monte_carlo.data import activity_distributions

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
exposure_model = exposure_mc.build_model(size=50000)
