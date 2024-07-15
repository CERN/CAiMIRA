import dataclasses

import numpy as np
import pytest

import caimira.calculator.models
import caimira.calculator.models.models
import caimira.calculator.models.monte_carlo.sampleable

MODEL_CLASSES = [
    cls for cls in vars(caimira.calculator.models).values()
    if dataclasses.is_dataclass(cls)
]


def test_type_annotations():
    # Check that there are appropriate type annotations for all of the model
    # classes in caimira.models. Note that these must be statically defined in
    # caimira.monte_carlo, rather than being dynamically generated, in order to
    # allow the type system to be able to see their definition without needing
    # runtime execution.
    missing = []
    for cls in MODEL_CLASSES:
        if not hasattr(caimira.calculator.models.monte_carlo, cls.__name__):
            missing.append(cls.__name__)
            continue
        mc_cls = getattr(caimira.calculator.models.monte_carlo, cls.__name__)
        assert issubclass(mc_cls, caimira.calculator.models.monte_carlo.MCModelBase)

    if missing:
        msg = (
            'There are missing model implementations in caimira.monte_carlo. '
            'The following definitions are needed:\n  ' +
            '\n  '.join([f'{model} = build_mc_model(caimira.models.{model})' for model in missing])
        )
        pytest.fail(msg)


@pytest.fixture
def baseline_mc_concentration_model(data_registry) -> caimira.calculator.models.monte_carlo.ConcentrationModel:
    mc_model = caimira.calculator.models.monte_carlo.ConcentrationModel(
        data_registry=data_registry,
        room=caimira.calculator.models.monte_carlo.Room(volume=caimira.calculator.models.monte_carlo.sampleable.Normal(75, 20),
                        inside_temp=caimira.calculator.models.models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=caimira.calculator.models.monte_carlo.SlidingWindow(
            data_registry=data_registry,
            active=caimira.calculator.models.models.PeriodicInterval(period=120, duration=120),
            outside_temp=caimira.calculator.models.models.PiecewiseConstant((0., 24.), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=caimira.calculator.models.models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            virus=caimira.calculator.models.models.Virus.types['SARS_CoV_2'],
            presence=caimira.calculator.models.models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=caimira.calculator.models.models.Mask.types['No mask'],
            activity=caimira.calculator.models.models.Activity.types['Light activity'],
            expiration=caimira.calculator.models.models.Expiration.types['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc_model


@pytest.fixture
def baseline_mc_sr_model() -> caimira.calculator.models.monte_carlo.ShortRangeModel:
    return ()


@pytest.fixture
def baseline_mc_exposure_model(data_registry, baseline_mc_concentration_model, baseline_mc_sr_model) -> caimira.calculator.models.monte_carlo.ExposureModel:
    return caimira.calculator.models.monte_carlo.ExposureModel(
        data_registry,
        baseline_mc_concentration_model,
        baseline_mc_sr_model,
        exposed=caimira.calculator.models.models.Population(
            number=10,
            presence=baseline_mc_concentration_model.infected.presence,
            activity=baseline_mc_concentration_model.infected.activity,
            mask=baseline_mc_concentration_model.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=caimira.calculator.models.models.Cases(),
    )


def test_build_concentration_model(baseline_mc_concentration_model: caimira.calculator.models.monte_carlo.ConcentrationModel):
    model = baseline_mc_concentration_model.build_model(7)
    assert isinstance(model, caimira.calculator.models.models.ConcentrationModel)
    assert isinstance(model.concentration(time=0.), float)
    conc = model.concentration(time=1.)
    assert isinstance(conc, np.ndarray)
    assert conc.shape == (7, )


def test_build_exposure_model(baseline_mc_exposure_model: caimira.calculator.models.monte_carlo.ExposureModel):
    model = baseline_mc_exposure_model.build_model(7)
    assert isinstance(model, caimira.calculator.models.models.ExposureModel)
    prob = model.deposited_exposure()
    assert isinstance(prob, np.ndarray)
    assert prob.shape == (7, )
