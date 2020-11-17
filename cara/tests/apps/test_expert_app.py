import cara.apps


def test_app():
    # To start with, let's just test that the application runs. We don't try to
    # do anything fancy to verify how it looks etc., we leave that for manual
    # testing.
    expert_app = cara.apps.ExpertApplication()
    assert expert_app.multi_model_view.scenario_names[0] == "Scenario 1"
