from cara import models
from cara.montecarlo import *

#IGH paper

# Baseline scenarios
classroom_model_IGH_no_mask_windows_closed = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.25,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_windows_closed_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.25,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=6.43, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1c
classroom_model_IGH_no_mask_windows_open_breaks = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_windows_open_alltimes = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1d
classroom_model_IGH_no_mask_windows_open_breaks_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_windows_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_windows_fully_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1e
classroom_model_IGH_no_mask_2windows_open_breaks = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_2windows_open_alltimes = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1f
classroom_model_IGH_no_mask_2windows_open_breaks_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_2windows_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_2windows_fully_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1g
classroom_model_IGH_no_mask_6windows_open_breaks = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_6windows_open_alltimes = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1h
classroom_model_IGH_no_mask_6windows_open_breaks_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_6windows_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=6*0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_6windows_fully_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1i
classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 1j
classroom_model_IGH_no_mask_6windows_open_breaks_endOfClass_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=6*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]




#Fig 2
classroom_model_IGH_no_mask_windows_closed_1HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.AirChange(
                        active=models.PeriodicInterval(period=120, duration=120),
                        air_exch=0.25,
                         ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_windows_closed_2HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.AirChange(
                        active=models.PeriodicInterval(period=120, duration=120),
                        air_exch=0.25,
                         ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=860)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

#Fig 3
classroom_model_IGH_with_mask_windows_closed = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.25,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

#Fig 4a
classroom_model_IGH_no_mask_2windows_open_breaks_winter_bis = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_2windows_open_breaks_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2 * 0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

#Fig 4b
classroom_model_IGH_with_mask_2windows_open_breaks_winter_1HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
                    inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (278,)),
                    window_height=1.6, opening_length=2 * 0.6,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_2windows_open_breaks_winter_2HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.SpecificInterval(((1.5, 2), (3.5, 4.5), (6, 6.5))),
                    inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (278,)),
                    window_height=1.6, opening_length=2 * 0.6,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=2*430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

#Fig 4c
classroom_model_IGH_no_mask_2windows_open_alltimes_winter_bis = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_2windows_open_alltimes_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.2,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

#Fig 4d
classroom_model_IGH_with_mask_2windows_open_alltimes_winter_1HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=120),
                    inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (278,)),
                    window_height=1.6, opening_length=2 * 0.2,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_2windows_open_alltimes_winter_2HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=120),
                    inside_temp=models.PiecewiseConstant((0, 24), (295,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (278,)),
                    window_height=1.6, opening_length=2 * 0.2,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=2*430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

######


classroom_model_IGH_no_mask_windows_open_breaks_endOfClass = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_2windows_open_breaks_endOfClass = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]


classroom_model_IGH_no_mask_windows_open_breaks_endOfClass_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_IGH_no_mask_2windows_open_breaks_endOfClass_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (278,)),
            window_height=1.6, opening_length=2*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]



classroom_model_IGH_with_mask_windows_open_breaks_endOfClass = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.SpecificInterval(((0.75, 0.92), (1.5, 2), (2.75, 2.92), (3.5, 4.5), (5.25, 5.42), (6, 6.5), (7.25, 7.42))),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_windows_open_alltimes = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (295,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_windows_closed_1HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.AirChange(
                        active=models.PeriodicInterval(period=120, duration=120),
                        air_exch=0.,
                         ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=430)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

classroom_model_IGH_with_mask_windows_closed_2HEPA = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.AirChange(
                        active=models.PeriodicInterval(period=120, duration=120),
                        air_exch=0.,
                         ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=860)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 1.5), (2, 3.5), (4.5, 6), (6.5, 8))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]