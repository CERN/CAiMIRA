import time

import pytest

from cara.apps.calculator import model_generator
from cara.apps.calculator import report_generator


@pytest.fixture
def baseline_form_data():
    return model_generator.baseline_raw_form_data()


@pytest.fixture
def baseline_form(baseline_form_data):
    return model_generator.FormData.from_dict(baseline_form_data)


def test_generate_report(baseline_form):
    # This is a simple test that confirms that given a model, we can actually
    # generate a report for it. Because this is what happens in the cara
    # calculator, we confirm that the generation happens within a reasonable
    # time threshold.
    time_limit: float = 1.5  # seconds

    start = time.perf_counter()
    model = baseline_form.build_model()
    report = report_generator.build_report("", model, baseline_form)
    end = time.perf_counter()
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
    assert report_generator.readable_minutes(test_input) == expected