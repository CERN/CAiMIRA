import pytest

import cern_caimira.apps.expert_apps as exp


@pytest.fixture
def expert_app():
    return exp.ExpertApplication()


@pytest.mark.skip(reason="ExpertApplication is deactivated")
def test_app(expert_app):
    # To start with, let's just test that the application runs. We don't try to
    # do anything fancy to verify how it looks etc., we leave that for manual
    # testing.
    assert expert_app._model_scenarios[0][0] == "Scenario 1"


@pytest.mark.skip(reason="ExpertApplication is deactivated")
def test_new_scenario_changes_tab(expert_app):
    # Adding a new scenario should change the tab index of the multi-model view.
    assert expert_app.multi_model_view.widget.selected_index == 0
    expert_app.add_scenario("Another scenario")
    assert expert_app.multi_model_view.widget.selected_index == 1
