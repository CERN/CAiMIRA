from caimira.calculator.models import models
import caimira.calculator.models.monte_carlo.models as mc
from caimira.calculator.store.data_registry import DataRegistry

from caimira.calculator.models.monte_carlo.data import activity_distributions, virus_distributions
from caimira.calculator.validators.virus.virus_validator import build_expiration, expiration_distributions

data_registry = DataRegistry()
ScenarioVar = tuple[models.Room, models.InfectedPopulation, models.Population] # (room, infected, exposed)

############ Airborne Control Levels (ACL) inspired by Luca Fontana #############

def acl_1(mask_infected: str, mask_exposed: str) -> tuple[ScenarioVar, str]:
    """Low-density community · residential · private offices"""
    room = mc.Room(volume=100, humidity=0.5, inside_temp=mc.PiecewiseConstant(               # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                        # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((10, 17), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_infected],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Speaking': 1/3, 'Breathing': 2/3}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                                 # type: ignore
                number=20,
                presence=models.SpecificInterval(
                                present_times=((10, 17), )),
                activity=activity_distributions(data_registry)['Seated'],
                mask=models.Mask.types[mask_exposed],
                host_immunity=0.,
            )
    pi_max = 0.05
    scenario_name = "ACL-1: " + "Infected " + mask_infected + ", Exposed " + mask_exposed
    return (room, infected, exposed), pi_max, scenario_name

def acl_2(mask_infected: str, mask_exposed: str) -> tuple[ScenarioVar, str]:
    """General public spaces · offices · classrooms · retail """
    room = mc.Room(volume=150, humidity=0.5, inside_temp=mc.PiecewiseConstant(               # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                        # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((10, 17), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_exposed],
                            activity=activity_distributions(data_registry)['Light activity'],
                            expiration=build_expiration(data_registry,
                                {'Speaking': 2/10, 'Breathing': 7/10, 'Shouting': 1/10}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                                 # type: ignore
                number=40,
                presence=models.SpecificInterval(
                                present_times=((10, 17), )),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.02
    scenario_name = "ACL-2: " + "Infected " + mask_infected + ", Exposed " + mask_exposed
    return (room, infected, exposed), pi_max, scenario_name

def acl_3(mask_infected: str, mask_exposed: str) -> tuple[ScenarioVar, str]:
    """Healthcare-adjacent · vulnerable populations · congregate """
    room = mc.Room(volume=150, humidity=0.3, inside_temp=mc.PiecewiseConstant(              # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                       # type: ignore
                            data_registry=data_registry,
                            number=5,
                            presence=models.SpecificInterval(
                                present_times=((10, 15), )),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_exposed],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=build_expiration(data_registry,
                                {'Speaking': 1/2, 'Breathing': 1/2}),
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                               # type: ignore
                number=50,
                presence=models.SpecificInterval(
                    present_times=((10, 15),)),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.01
    scenario_name = "ACL-3: " + "Infected " + mask_infected + ", Exposed " + mask_exposed
    return (room, infected, exposed), pi_max, scenario_name

def acl_4(mask_infected: str, mask_exposed: str) -> tuple[ScenarioVar, str]:
    """Confirmed source · isolation rooms · AGP suites """
    room = mc.Room(volume=40, humidity=0.3, inside_temp=mc.PiecewiseConstant(              # type: ignore
        (0, 24), (20+273.15, )))

    infected = mc.InfectedPopulation(                                                      # type: ignore
                            data_registry=data_registry,
                            number=1,
                            presence=models.SpecificInterval(
                                present_times=((10, 12),)),
                            virus=virus_distributions(data_registry)['SARS_CoV_2_OMICRON'],
                            mask=models.Mask.types[mask_exposed],
                            activity=activity_distributions(data_registry)['Seated'],
                            expiration=expiration_distributions(data_registry)['Breathing'],
                            host_immunity=0.,
                        )

    exposed = mc.Population(                                                             # type: ignore
                number=2,
                presence=models.SpecificInterval(
                    present_times=((10, 12),)),
                activity=activity_distributions(data_registry)['Light activity'],
                mask=models.Mask.types[mask_infected],
                host_immunity=0.,
            )
    pi_max = 0.001
    scenario_name = "ACL-4: " + "Infected " + mask_infected + ", Exposed " + mask_exposed
    return (room, infected, exposed), pi_max, scenario_name