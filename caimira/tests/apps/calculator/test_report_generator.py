import concurrent.futures
from functools import partial
import os
import time

import numpy as np
import pytest

from caimira.apps.calculator import make_app
from caimira.apps.calculator.model_generator import VirusFormData
from caimira.apps.calculator.report_generator import (ReportGenerator, readable_minutes, calculate_report_data,
    manufacture_alternative_scenarios, interesting_times, comparison_report)
import caimira.apps.calculator.report_generator as rep_gen


def test_generate_report(baseline_form) -> None:
    # This is a simple test that confirms that given a model, we can actually
    # generate a report for it. Because this is what happens in the caimira
    # calculator, we confirm that the generation happens within a reasonable
    # time threshold.
    time_limit: float = float(os.environ.get("CAIMIRA_TESTS_CALCULATOR_TIMEOUT", 10.))

    start = time.perf_counter()

    generator: ReportGenerator = make_app().settings['report_generator']
    report = generator.build_report("", baseline_form, partial(
        concurrent.futures.ThreadPoolExecutor, 1,
    ))
    end = time.perf_counter()
    total = end-start
    print(f"Time limit: {time_limit} | Time taken: {end} - {start} = {total} < {time_limit}")
    assert report != ""
    assert end - start < time_limit


@pytest.mark.parametrize(
    ["test_input", "expected"],
    [
        [1, '1 minute'],
        [2, '2 minutes'],
        [60, '1 hour'],
        [120, '2 hours'],
        [150, '150 minutes'],
    ],
)
def test_readable_minutes(test_input, expected):
    assert readable_minutes(test_input) == expected


def test_fill_big_gaps():
    expected = [1, 1.75, 2, 2.75, 3.5, 4]
    assert rep_gen.fill_big_gaps([1, 2, 4], gap_size=0.75) == expected


def test_fill_big_gaps__float_tolerance():
    # Ensure that there is some float tolerance to the gap size check.
    assert rep_gen.fill_big_gaps([0, 2 + 1e-15, 4], gap_size=2) == [0, 2 + 1e-15, 4]
    assert rep_gen.fill_big_gaps([0, 2 + 1e-14, 4], gap_size=2) == [0, 2, 2 + 1e-14, 4]


def test_non_temp_transition_times(baseline_exposure_model):
    expected = [0.0, 4.0, 5.0, 8.0]
    result = rep_gen.non_temp_transition_times(baseline_exposure_model)
    assert result == expected


def test_interesting_times_many(baseline_exposure_model):
    result = rep_gen.interesting_times(baseline_exposure_model, approx_n_pts=100)
    assert 100 <= len(result) <= 120
    assert np.abs(np.diff(result)).max() < 8.1/100.


def test_interesting_times_small(baseline_exposure_model):
    expected = [0.0, 0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.0, 5.8, 6.6, 7.4, 8.0]
    # Ask for more data than there is in the transition times.
    result = rep_gen.interesting_times(baseline_exposure_model, approx_n_pts=10)

    np.testing.assert_allclose(result, expected, atol=1e-04)


def test_interesting_times_w_temp(exposure_model_w_outside_temp_changes):
    # Ensure that the state change times are returned (minus the temperature changes) by
    # requesting n_points=1.
    result = rep_gen.interesting_times(exposure_model_w_outside_temp_changes, approx_n_pts=1)
    expected = [0., 1.8, 2.2, 4., 4.4, 5., 6.2, 6.6, 8.]
    np.testing.assert_allclose(result, expected)

    # Now request more than the state-change times.
    result = rep_gen.interesting_times(exposure_model_w_outside_temp_changes, approx_n_pts=20)
    expected = [
        0., 0.4, 0.8, 1.2, 1.6, 1.8, 2.2, 2.6, 3., 3.4, 3.8, 4., 4.4, 4.8,
        5., 5.4, 5.8, 6.2, 6.6, 7., 7.4, 7.8, 8.
    ]
    np.testing.assert_allclose(result, expected)


def test_expected_new_cases(baseline_form_with_sr: VirusFormData):   
    model = baseline_form_with_sr.build_model()
    
    executor_factory = partial(
        concurrent.futures.ThreadPoolExecutor, 1,
    )

    # Short- and Long-range contributions
    report_data = calculate_report_data(baseline_form_with_sr, model, executor_factory)
    sr_lr_expected_new_cases = report_data['expected_new_cases']
    sr_lr_prob_inf = report_data['prob_inf']/100
    
    # Long-range contributions alone
    scenario_sample_times = interesting_times(model)
    alternative_scenarios = manufacture_alternative_scenarios(baseline_form_with_sr)
    alternative_statistics = comparison_report(
        baseline_form_with_sr, report_data, alternative_scenarios, scenario_sample_times, executor_factory=executor_factory,
    )

    lr_expected_new_cases = alternative_statistics['stats']['Base scenario without short-range interactions']['expected_new_cases']
    np.testing.assert_almost_equal(sr_lr_expected_new_cases, lr_expected_new_cases + sr_lr_prob_inf * baseline_form_with_sr.short_range_occupants, 2)
