from dataclasses import dataclass
import pytest
from unittest.mock import Mock

import cara.apps
from cara import models
import cara.state


@pytest.fixture
def expert_app():
    return cara.apps.ExpertApplication()


def test_app(expert_app):
    # To start with, let's just test that the application runs. We don't try to
    # do anything fancy to verify how it looks etc., we leave that for manual
    # testing.
    assert expert_app._model_scenarios[0][0] == "Scenario 1"


def test_new_scenario_changes_tab(expert_app):
    # Adding a new scenario should change the tab index of the multi-model view.
    assert expert_app.multi_model_view.widget.selected_index == 0
    expert_app.add_scenario("Another scenario")
    assert expert_app.multi_model_view.widget.selected_index == 1


def test_observe_instance_MultipleVentilation():
    top_level = Mock()

    @dataclass
    class VentilationContainer:
        multiple_ventilation: models.MultipleVentilation

    builder = cara.apps.expert.CARAStateBuilder()
    state = cara.state.DataclassInstanceState(VentilationContainer, builder)
    instance = VentilationContainer(multiple_ventilation=models.MultipleVentilation(
        (
            models.HVACMechanical(active=models.PeriodicInterval(30, 15), q_air_mech=15.),
            models.HEPAFilter(active=models.PeriodicInterval(20, 10), q_air_mech=15.),
        ),
    ))
    state.dcs_update_from(instance)

    state.dcs_observe(top_level)

    top_level.assert_not_called()
    state.multiple_ventilation.ventilations[0].q_air_mech = 10
    top_level.assert_called_with()
