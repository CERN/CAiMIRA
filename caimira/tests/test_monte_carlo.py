import dataclasses

import numpy as np
import pytest

import caimira.calculator.models.models as models
import caimira.calculator.models.monte_carlo as mc

MODEL_CLASSES = [
    cls for cls in vars(models).values()
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
        if not hasattr(mc, cls.__name__):
            missing.append(cls.__name__)
            continue
        mc_cls = getattr(mc, cls.__name__)
        assert issubclass(mc_cls, mc.MCModelBase)

    if missing:
        msg = (
            'There are missing model implementations in caimira.monte_carlo. '
            'The following definitions are needed:\n  ' +
            '\n  '.join([f'{model} = build_mc_model(caimira.models.{model})' for model in missing])
        )
        pytest.fail(msg)


@pytest.fixture
def baseline_mc_concentration_model(data_registry) -> mc.ConcentrationModel:
    mc_model = mc.ConcentrationModel(
        data_registry=data_registry,
        room=mc.Room(volume=mc.sampleable.Normal(75, 20),
                        inside_temp=models.PiecewiseConstant((0., 24.), (293,))),
        ventilation=mc.SlidingWindow(
            data_registry=data_registry,
            active=models.PeriodicInterval(period=120, duration=120),
            outside_temp=models.PiecewiseConstant((0., 24.), (283,)),
            window_height=1.6, opening_length=0.6,
        ),
        infected=models.InfectedPopulation(
            data_registry=data_registry,
            number=1,
            virus=models.Virus.types['SARS_CoV_2'],
            presence=models.SpecificInterval(((0., 4.), (5., 8.))),
            mask=models.Mask.types['No mask'],
            activity=models.Activity.types['Light activity'],
            expiration=models.Expiration.types['Breathing'],
            host_immunity=0.,
        ),
        evaporation_factor=0.3,
    )
    return mc_model


@pytest.fixture
def baseline_mc_sr_model() -> mc.ShortRangeModel:
    return ()


@pytest.fixture
def baseline_mc_exposure_model(data_registry, baseline_mc_concentration_model, baseline_mc_sr_model) -> mc.ExposureModel:
    return mc.ExposureModel(
        data_registry,
        baseline_mc_concentration_model,
        baseline_mc_sr_model,
        exposed=models.Population(
            number=10,
            presence=baseline_mc_concentration_model.infected.presence,
            activity=baseline_mc_concentration_model.infected.activity,
            mask=baseline_mc_concentration_model.infected.mask,
            host_immunity=0.,
        ),
        geographical_data=models.Cases(),
    )


def test_build_concentration_model(baseline_mc_concentration_model: mc.ConcentrationModel):
    model = baseline_mc_concentration_model.build_model(7)
    assert isinstance(model, models.ConcentrationModel)
    assert isinstance(model.concentration(time=0.), float)
    conc = model.concentration(time=1.)
    assert isinstance(conc, np.ndarray)
    assert conc.shape == (7, )


def test_build_exposure_model(baseline_mc_exposure_model: mc.ExposureModel):
    model = baseline_mc_exposure_model.build_model(7)
    assert isinstance(model, mc.ExposureModel)
    prob = model.deposited_exposure()
    assert isinstance(prob, np.ndarray)
    assert prob.shape == (7, )
