from cara import models
from cara.montecarlo import *


fixed_vl_exposure_models = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=45),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=100),
            expiratory_activity=1,
            samples=2000000,
            breathing_category=1,
            viral_load=float(vl)
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for vl in range(6, 11)]


large_population_baselines = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=800),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=2000.
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=1,
            samples=200000,
            breathing_category=2,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )

    ),
    exposed=models.Population(
        number=60,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Standing'],
        mask=models.Mask.types['No mask']
    )
) for qid in (100, 60)]

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
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=3,
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
) for qid in (100, 60)]

exposure_models_2 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=33),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 4), (5, 9))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=4,
            samples=2000000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.1, 0)
        )
    ),
    exposed=models.Population(
        number=2,
        presence=models.SpecificInterval(((0, 4), (5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for qid in (100, 60)]

######## Classroom exposure models ###########
classroom_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_full_open = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_summer = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_full_open_summer = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_no_vent = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_teacher_mask_full_open = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=4*0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_with_hepa = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                            active=models.PeriodicInterval(period=120, duration=10),
                            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                            window_height=1.6, opening_length=0.6,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=800)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_full_open_multi = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                            active=models.PeriodicInterval(period=120, duration=120),
                            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                            window_height=1.6, opening_length=4*0.6,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=0)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

classroom_model_full_open_multi_masks = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=160),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                            active=models.PeriodicInterval(period=120, duration=120),
                            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                            window_height=1.6, opening_length=4*0.6,
                        ),
                models.HEPAFilter(active=models.PeriodicInterval(period=120, duration=120),
                                 q_air_mech=0)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=3,
        )
    ),
    exposed=models.Population(
        number=19,
        presence=models.SpecificInterval(((0, 2), (2.5, 4), (5, 7), (7.5, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

######### Shared office exposure models ###########
shared_office_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=50),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
            masked=True,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for qid in (100, 60)]

shared_office_model_no_mask = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=50),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
            masked=False,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
) for qid in (100, 60)]

shared_office_worst_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=50),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
            masked=False,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
) for qid in (100, 60)]

shared_office_better_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=50),
        ventilation=models.MultipleVentilation(
            ventilations=(
                models.SlidingWindow(
                    active=models.PeriodicInterval(period=120, duration=10),
                    inside_temp=models.PiecewiseConstant((0, 24), (293,)),
                    outside_temp=models.PiecewiseConstant((0, 24), (283,)),
                    window_height=1.6, opening_length=0.6,
                ),
                models.AirChange(active=models.PeriodicInterval(period=120, duration=120),
                                 air_exch=5.)
            )
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
            masked=True,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 2), (2.1, 4), (5, 7), (7.1, 9))),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['Type I']
    )
) for qid in (100, 60)]

######### Ski cabine exposure models ###########
ski_cabin_model_10 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 10/60),)),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 10/60),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

ski_cabin_model_baseline_20 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 20/60),)),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 20/60),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

ski_cabin_model_25 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 25/60),)),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 25/60),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

ski_cabin_model_30 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 30/60),)),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 30/60),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

ski_cabin_model_60 = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 1),)),
            masked=True,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 1),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['Type I']
    )
)for qid in (100, 60)]

ski_cabin_model_baseline_exposure_time = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=10),
        ventilation=models.HVACMechanical(
            active=models.PeriodicInterval(period=120, duration=120),
            q_air_mech=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 20),)),
            masked=mi,
            virus=MCVirus(halflife=1.1, qID=60),
            expiratory_activity=2,
            samples=200000,
            breathing_category=4,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=3,
        presence=models.SpecificInterval(((0, 20),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types[me]
    )
)for mi, me in zip((True, False), ('Type I', 'No mask'))]

######### Gym exposure models ###########
gym_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=300),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=6.,
        ),
        infected=MCInfectedPopulation(
            number=2,
            presence=models.SpecificInterval(((0, 1),)),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=1,
            samples=200000,
            breathing_category=5,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=28,
        presence=models.SpecificInterval(((0, 1),)),
        activity=models.Activity.types['Heavy exercise'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

######### Waiting room exposure models ###########
waiting_room_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=100),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            masked=False,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=14,
        presence=models.SpecificInterval(((0, 2),)),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

waiting_room_model_full_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=100),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            masked=False,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=14,
        presence=models.SpecificInterval(((0, 2),)),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

waiting_room_model_full_summer = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=100),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=120, duration=120),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=14,
        presence=models.SpecificInterval(((0, 2),)),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

waiting_room_model_periodic_winter = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=100),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=20, duration=5),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            masked=False,
            virus=MCVirus(halflife=3.8, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=14,
        presence=models.SpecificInterval(((0, 2),)),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

waiting_room_model_periodic_summer = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=100),
        ventilation=models.SlidingWindow(
            active=models.PeriodicInterval(period=60, duration=10),
            inside_temp=models.PiecewiseConstant((0, 24), (293,)),
            outside_temp=models.PiecewiseConstant((0, 24), (291,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2),)),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=4,
            samples=200000,
            breathing_category=1,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=14,
        presence=models.SpecificInterval(((0, 2),)),
        activity=models.Activity.types['Seated'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]

######### S V Chorale exposure models ###########
chorale_model = [MCExposureModel(
    concentration_model=MCConcentrationModel(
        room=models.Room(volume=810),
        ventilation=models.AirChange(
            active=models.PeriodicInterval(period=120, duration=120),
            air_exch=0.7,
        ),
        infected=MCInfectedPopulation(
            number=1,
            presence=models.SpecificInterval(((0, 2.5),)),
            masked=False,
            virus=MCVirus(halflife=1.1, qID=qid),
            expiratory_activity=3,
            samples=20000,
            breathing_category=3,
            expiratory_activity_weights=(0.7, 0.3, 0)
        )
    ),
    exposed=models.Population(
        number=60,
        presence=models.SpecificInterval(((0, 2.5),)),
        activity=models.Activity.types['Moderate activity'],
        mask=models.Mask.types['No mask']
    )
)for qid in (100, 60)]
