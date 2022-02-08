from cara import models
import cara.data
import cara.dataclass_utils

import pytest


# Typical expirations. The aerosol diameter given is an equivalent
# diameter, chosen in such a way that the aerosol volume is
# the same as the total aerosol volume given by the full BLO model
# (integrated between 0.1 and 30 microns)
# The correspondence with the BLO coefficients is given.
expiration_types = {
    'Breathing': models.Expiration(1.3844), # corresponds to B/L/O coefficients of (1, 0, 0)
    'Speaking': models.Expiration(5.8925),   # corresponds to B/L/O coefficients of (1, 1, 1)
    'Shouting': models.Expiration(10.0411), # corresponds to B/L/O coefficients of (1, 5, 5)
    'Singing': models.Expiration(10.0411),  # corresponds to B/L/O coefficients of (1, 5, 5)
}


@pytest.fixture
def baseline_model():
    model = models.ConcentrationModel(
        room=models.Room(volume=75),
        ventilation=models.AirChange(
            active=models.SpecificInterval(((0., 24.), )),
            air_exch=30.,
        ),
        infected=models.EmittingPopulation(
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            known_individual_emission_rate=970 * 50,
            host_immunity=0.,
            # superspreading event, where ejection factor is fixed based
            # on Miller et al. (2020) - 50 represents the infectious dose.
        ),
        evaporation_factor=0.3,
    )
    return model


@pytest.fixture
def baseline_exposure_model(baseline_model):
    return models.ExposureModel(
        baseline_model,
        exposed=models.Population(
            number=1000,
            presence=baseline_model.infected.presence,
            activity=baseline_model.infected.activity,
            mask=baseline_model.infected.mask,
            host_immunity=0.,
        ),
    )


@pytest.fixture
def exposure_model_w_outside_temp_changes(baseline_exposure_model: models.ExposureModel):
    exp_model = cara.dataclass_utils.nested_replace(
        baseline_exposure_model, {
            'concentration_model.ventilation': models.SlidingWindow(
                active=models.PeriodicInterval(2.2 * 60, 1.8 * 60),
                inside_temp=models.PiecewiseConstant((0., 24.), (293,)),
                outside_temp=cara.data.GenevaTemperatures['Jan'],
                window_height=1.6,
                opening_length=0.6,
            )
        })
    return exp_model
