import pytest

from cara.apps.calculator import report_generator


def test_generate_report(baseline_form):
    model = baseline_form.build_model()

    report = report_generator.build_report("", model, baseline_form)
    assert report != ""


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
