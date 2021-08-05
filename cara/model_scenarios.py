from cara import models

exposure_models = models.ExposureModel(
    concentration_model=models.ConcentrationModel(
        room=models.Room(volume=45, humidity=0.5),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293, )),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.2,
        ),
        infected=models.InfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            mask=False,
            mask=models.Mask.types['Type I'],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2_B117'],
            expiration=models.Expiration.types['Breathing']
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    ),
    
)