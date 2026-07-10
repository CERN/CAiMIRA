from caimira.calculator.models.dataclass_utils import nested_replace


def test_exposure_r0(baseline_exposure_model):
    infected_populations = tuple(
            nested_replace(
                infected,
                {"number": 3},
            )
            for infected in baseline_exposure_model.infected_populations
        )
    baseline_n3 = nested_replace(
            baseline_exposure_model,
            {"infected_populations": infected_populations},
        )
    # The number of new cases should be greater if there are more infecteds, but
    # the reproduction number should be the same (it is a measure of one infected case).
    assert baseline_n3.expected_new_cases() > baseline_exposure_model.expected_new_cases()
    assert baseline_n3.reproduction_number() == baseline_exposure_model.reproduction_number()
