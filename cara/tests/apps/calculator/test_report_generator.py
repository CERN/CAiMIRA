import concurrent.futures
from functools import partial
import time

import pytest

from cara.apps.calculator.report_generator import ReportGenerator, readable_minutes
from cara.apps.calculator import make_app


def test_generate_report(baseline_form):
    # This is a simple test that confirms that given a model, we can actually
    # generate a report for it. Because this is what happens in the cara
    # calculator, we confirm that the generation happens within a reasonable
    # time threshold.
    time_limit: float = 20.0  # seconds

    start = time.perf_counter()

    generator: ReportGenerator = make_app().settings['report_generator']
    report = generator.build_report("", baseline_form, partial(
        concurrent.futures.ThreadPoolExecutor, 1,
    ))
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
    assert readable_minutes(test_input) == expected
