from cara import models
from cara.montecarlo import *

######### Standard exposure models ###########
exposure_models = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=45),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=100),
            expiratory_activity=a,
            samples=2000000,
            breathing_category=3,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for a in (1, 2, 3)]