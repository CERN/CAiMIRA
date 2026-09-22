import pytest

import caimira.calculator.models.monte_carlo as mc
import caimira.calculator.models as models
from caimira.calculator.store.data_registry import DataRegistry

@pytest.fixture
def data_registry():
    return DataRegistry()


def dynamic_mask_exposure_model_group(data_registry):
    mask_types = ['Type I', 'No mask']

    exposed_populations = tuple(
        mc.Population(
            identifier="",
            number=5,
            presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
            mask=models.Mask.types[mask_type],
            activity=models.Activity.types['Seated'],
            host_immunity=0.,
        ) for mask_type in mask_types
    )
    
    infected_populations = tuple(
        mc.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            presence=models.SpecificInterval(((8, 12.5), (13.5, 17), )),
            mask=models.Mask.types[mask_type],
            activity=models.Activity.types['Seated'],
            virus=models.Virus.types['SARS_CoV_2'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ) for mask_type in mask_types
    )

    conc_models = tuple(
        mc.ConcentrationModel(
            data_registry=data_registry,
            room=models.Room(volume=75, inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
            ventilation=models.AirChange(
                active=models.SpecificInterval(((0., 24.), )),
                air_exch=30.,
            ),
            infected=infected_population,
            evaporation_factor=0.3,
            short_range=(),
        ) for infected_population in infected_populations
    )

    exposure_models = tuple(
        mc.ExposureModel(
            data_registry=data_registry,
            concentration_model=conc_models,
            exposed=exposed_population, # TODO: add name
            geographical_data=models.Cases(),
            exposed_to_short_range=exposed_population.number,
        ) for exposed_population in exposed_populations
    )
    return mc.ExposureModelGroup(
            data_registry=data_registry,
            exposure_models = exposure_models,
        )