from caimira.calculator.models import models
from caimira.calculator.store.data_registry import DataRegistry
import caimira.calculator.models.monte_carlo.models as mc

from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions
from caimira.calculator.validators.virus.virus_validator import build_expiration, expiration_distributions

data_registry = DataRegistry()

############ Shared office scenario #############
def shared_office():
    room = mc.Room(volume=50, humidity=0.6, inside_temp=mc.PiecewiseConstant(
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((8.5, 12.5), (13.5, 17.5))),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types['No mask'],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Speaking': 1/3, 'Breathing': 2/3}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(
                number=3,
                presence=mc.SpecificInterval(
                    present_times=((8.5, 12.5), (13.5, 17.5))),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types['No mask'],
                host_immunity=0.,
            )
    return room, infected, exposed

############ Classroom scenario #############
def classroom():
    room = mc.Room(volume=160, humidity=0.4, inside_temp=mc.PiecewiseConstant((0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(
                    data_registry=data_registry,
                    number=1,
                    presence=models.SpecificInterval(
                        present_times=((8.5, 10), (10.25, 12.5), (13.5, 15.), (15.25, 17.5),)),
                    virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                    mask=models.Mask.types['No mask'],
                    activity=activity_distributions(data_registry)['Light activity'],
                    expiration=expiration_distributions(data_registry)['Speaking'],
                    host_immunity=0.,
                )

    exposed = mc.Population(
                number=19,
                presence=mc.SpecificInterval(
                    present_times=((8.5, 10), (10.25, 12.5), (13.5, 15.), (15.25, 17.5),)),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types['No mask'],
                host_immunity=0.,
            )
    return room, infected, exposed

############ Patient ward scenario #############
def patient_ward():
    room = mc.Room(volume=48, humidity=0.3, inside_temp=mc.PiecewiseConstant((0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(
                    data_registry=data_registry,
                    number=4,
                    presence=models.SpecificInterval(
                        present_times=((0, 24), ),
                    ),
                    virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                    mask=models.Mask.types['No mask'],
                    activity=activity_distributions(data_registry)['Seated'],
                    expiration=build_expiration(data_registry,
                        {'Speaking': 0.5, 'Breathing': 0.5}),
                    host_immunity=0.,
                )

    exposed = mc.Population(
                number=1,
                presence=mc.SpecificInterval(
                    # 4 * 30min over a full shift
                    present_times=((8, 8.5), (11, 11.5), (14, 14.5), (17, 17.5), ),
                ),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types['No mask'],
                host_immunity=0.,
            )
    return room, infected, exposed

def ICU():
    room=mc.Room(volume=64, humidity=0.3, inside_temp=mc.PiecewiseConstant(
        (0, 24), (20+273.15, )))
    infected=mc.InfectedPopulation(
        data_registry=data_registry,
        number=6,
        presence=models.SpecificInterval(
            present_times=((0, 24), ),
        ),
        virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
        mask=models.Mask.types['No mask'],
        activity=activity_distributions(data_registry)['Seated'],
        expiration=expiration_distributions(data_registry)['Breathing'],
        host_immunity=0.,
    )
    exposed=mc.Population(
        number=6, # 1 nurse per patient 
        presence=mc.SpecificInterval(
            present_times=((8, 12), (13, 17), ), # 8h shift with 1 h break 
        ),
        activity=activity_distributions(data_registry)['Light activity'],
        mask=models.Mask.types['No mask'],
        host_immunity=0.,
    )
    return room, infected, exposed

############ Ski cabin #############
def ski():
    room=mc.Room(volume=10, humidity=0.3)

    infected=mc.InfectedPopulation(
        data_registry=data_registry,
        number=1,
        presence=models.SpecificInterval(present_times=((10, 10.333),)),
        virus=virus_distributions(data_registry)['SARS_CoV_2'],
        mask=models.Mask.types['No mask'],
        activity=activity_distributions(data_registry)['Moderate activity'],
        expiration=expiration_distributions(data_registry)['Speaking'],
        host_immunity=0.,
    )

    exposed=mc.Population(
            number=3,
            presence=models.SpecificInterval(present_times=((10, 10.333),)),
            activity=activity_distributions(data_registry)['Moderate activity'],
            mask=models.Mask.types['No mask'],
            host_immunity=0.,
        )
    return room, infected, exposed

############ Chorale scenario #############
def chorale():
    room=mc.Room(volume=810, humidity=0.5)


    infected=mc.InfectedPopulation(
        data_registry=data_registry,
        number=1,
        presence=models.SpecificInterval(((0, 2.5), )),
        virus=virus_distributions(data_registry)['SARS_CoV_2'],
        mask=models.Mask.types['No mask'],
        activity=activity_distributions(data_registry)['Moderate activity'],
        expiration=expiration_distributions(data_registry)['Shouting'],
        host_immunity=0.,
    )

    exposed=mc.Population(
        number=60,
        presence=models.SpecificInterval(((0, 2.5), )),
        activity=activity_distributions(data_registry)['Moderate activity'],
        mask=models.Mask.types['No mask'],
        host_immunity=0.,
    )
    return room, infected, exposed
