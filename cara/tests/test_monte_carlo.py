import dataclasses

import numpy as np
import pytest

import cara.models
import cara.monte_carlo.models as mc_models
import cara.monte_carlo.sampleable


MODEL_CLASSES = [
    cls for cls in vars(cara.models).values()
    if dataclasses.is_dataclass(cls)
]


def test_type_annotations():
    # Check that there are appropriate type annotations for all of the model
    # classes in cara.models. Note that these must be statically defined in
    # cara.monte_carlo, rather than being dynamically generated, in order to
    # allow the type system to be able to see their definition without needing
    # runtime execution.
    missing = []
    for cls in MODEL_CLASSES:
        if not hasattr(cara.monte_carlo, cls.__name__):
            missing.append(cls.__name__)
            continue
        mc_cls = getattr(cara.monte_carlo, cls.__name__)
        assert issubclass(mc_cls, cara.monte_carlo.MCModelBase)

    if missing:
        msg = (
            'There are missing model implementations in cara.monte_carlo. '
            'The following definitions are needed:\n  ' +
            '\n  '.join([f'{model} = build_mc_model(cara.models.{model})' for model in missing])
        )
        pytest.fail(msg)


@pytest.fixture
def baseline_mc_concentration_model() -> cara.monte_carlo.ConcentrationModel:
    mc_model = cara.monte_carlo.ConcentrationModel(
        room=cara.monte_carlo.Room(volume=cara.monte_carlo.sampleable.Normal(75, 20)),
        ventilation=cara.monte_carlo.SlidingWindow(
            active=cara.models.PeriodicInterval(period=120, duration=120),
            inside_temp=cara.models.PiecewiseConstant((0., 24.), (293,)),
            outside_temp=cara.models.PiecewiseConstant((0., 24.), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=cara.models.InfectedPopulation(
            number=1,
            virus=cara.models.Virus.types['SARS_CoV_2'],
            presence=cara.models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=cara.models.Mask.types['No mask'],
            activity=cara.models.Activity.types['Light activity'],
            expiration=cara.models.Expiration.types['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc_model


@pytest.fixture
def baseline_mc_sr_model() -> cara.monte_carlo.ShortRangeModel:
    return cara.monte_carlo.ShortRangeModel(
        activities=(),
        presence=(),
        expirations=(),
        dilutions=(),
    )


@pytest.fixture
def baseline_mc_exposure_model(baseline_mc_concentration_model, baseline_mc_sr_model) -> cara.monte_carlo.ExposureModel:
    return cara.monte_carlo.ExposureModel(
        baseline_mc_concentration_model,
        baseline_mc_sr_model,
        exposed=cara.models.Population(
            number=10,
            presence=baseline_mc_concentration_model.infected.presence,
            activity=baseline_mc_concentration_model.infected.activity,
            mask=baseline_mc_concentration_model.infected.mask,
            host_immunity=0.,
        )
    )


def test_build_concentration_model(baseline_mc_concentration_model: cara.monte_carlo.ConcentrationModel):
    model = baseline_mc_concentration_model.build_model(7)
    assert isinstance(model, cara.models.ConcentrationModel)
    assert isinstance(model.concentration(time=0.), float)
    conc = model.concentration(time=1.)
    assert isinstance(conc, np.ndarray)
    assert conc.shape == (7, )


def test_build_exposure_model(baseline_mc_exposure_model: cara.monte_carlo.ExposureModel):
    model = baseline_mc_exposure_model.build_model(7)
    assert isinstance(model, cara.models.ExposureModel)
    prob = model.deposited_exposure()
    assert isinstance(prob, np.ndarray)
    assert prob.shape == (7, )
