from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo.models as mc
from caimira.calculator.store.data_registry import DataRegistry

from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions
from caimira.calculator.validators.virus.virus_validator import build_expiration, expiration_distributions

data_registry = DataRegistry()
ScenarioVar = tuple[models.Room, models.InfectedPopulation, models.Population] # (room, infected, exposed)

############ Airborne Control Levels (ACL) inspired by Luca Fontana #############

def acl_1(mask_infected: str) -> tuple[ScenarioVar, float, str]:
    """Low-density community · residential · private offices"""
    room = mc.Room(volume=252, humidity=0.5, inside_temp=mc.PiecewiseConstant(               # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                        # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((0, 7), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Breathing': 2/3, 'Speaking': 1/3}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                                 # type: ignore
                number=20,
                presence=models.SpecificInterval(
                                present_times=((0, 7), )),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.1
    scenario_name = "ACL-1: " + "Infected " + mask_infected
    return (room, infected, exposed), pi_max, scenario_name

def acl_2(mask_infected) -> tuple[ScenarioVar, float, str]:
    """General public spaces · offices · classrooms · retail """
    room = mc.Room(volume=492, humidity=0.5, inside_temp=mc.PiecewiseConstant(               # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                        # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((0, 7), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Moderate activity'],
                            expiration=build_expiration(data_registry,
                                {'Breathing': 2/3, 'Speaking': 1/3}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                                 # type: ignore
                number=40,
                presence=models.SpecificInterval(
                                present_times=((0, 7), )),
                activity=activity_distributions(data_registry)['Moderate activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.02
    scenario_name = "ACL-2: " + "Infected " + mask_infected
    return (room, infected, exposed), pi_max, scenario_name

def acl_3a(mask_infected) -> tuple[ScenarioVar, float, str]:
    """Healthcare-adjacent · vulnerable populations · congregate """
    room = mc.Room(volume=660, humidity=0.3, inside_temp=mc.PiecewiseConstant(              # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                       # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((0, 5), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Breathing': 1/2, 'Speaking': 1/2}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                               # type: ignore
                number=50,
                presence=models.SpecificInterval(
                    present_times=((0, 5),)),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.01
    scenario_name = "ACL-3: " + "Infected " + mask_infected
    return (room, infected, exposed), pi_max, scenario_name

def acl_3b(mask_infected) -> tuple[ScenarioVar, float, str]:
    """Healthcare-adjacent · vulnerable populations · congregate """
    room = mc.Room(volume=660, humidity=0.3, inside_temp=mc.PiecewiseConstant(              # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                       # type: ignore
                            data_registry=data_registry,
                            number=5,
                            presence=models.SpecificInterval(
                                present_times=((0, 5), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Breathing': 1/2, 'Speaking': 1/2}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                               # type: ignore
                number=50,
                presence=models.SpecificInterval(
                    present_times=((0, 5),)),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.01
    scenario_name = "ACL-3: " + "Infected " + mask_infected
    return (room, infected, exposed), pi_max, scenario_name

def acl_4(mask_infected) -> tuple[ScenarioVar, float, str]:
    """Confirmed source · isolation rooms · AGP suites """
    room = mc.Room(volume=60, humidity=0.3, inside_temp=mc.PiecewiseConstant(              # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                      # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((0, 2),)),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Breathing': 3/4, 'Speaking': 1/4}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                             # type: ignore
                number=2,
                presence=models.SpecificInterval(
                    present_times=((0, 2),)),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types['FFP2'],
                host_immunity=0.,
            )
    pi_max = 0.001
    scenario_name = "ACL-4: " + "Infected " + mask_infected
    return (room, infected, exposed), pi_max, scenario_name