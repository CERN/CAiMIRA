from caimira.calculator.models.dataclass_utils import nested_replace


def test_exposure_r0(baseline_exposure_model):
    infected_population = baseline_exposure_model.concentration_model.infected_populations[0]
    new_infected_populations = (
        nested_replace(
            infected_population, {'number': 3}
        ),
    )
    baseline_n3 = nested_replace(
        baseline_exposure_model, {'concentration_model.infected_populations': new_infected_populations}
    )
    # The number of new cases should be greater if there are more infecteds, but
    # the reproduction number should be the same (it is a measure of one infected case).
    assert baseline_n3.expected_new_cases() > baseline_exposure_model.expected_new_cases()
    assert baseline_n3.reproduction_number() == baseline_exposure_model.reproduction_number()
