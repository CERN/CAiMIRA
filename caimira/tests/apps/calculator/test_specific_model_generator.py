from typing import Type
import numpy as np
import pytest

from caimira.apps.calculator import model_generator


@pytest.mark.parametrize(
    ["break_input", "error"],
    [
        [["exposed_breaks", [], "infected_breaks", []], "The specific breaks should be in a dictionary."],
        [{"eposed_breaks": [], "infected_breaks": []}, 'Unable to fetch "exposed_breaks" key. Got "eposed_breaks".'],
        [{"exposed_breaks": [], "ifected_breaks": []}, 'Unable to fetch "infected_breaks" key. Got "ifected_breaks".'],
    ]
)
def test_specific_break_structure(break_input, error, baseline_form: model_generator.VirusFormData):
    baseline_form.specific_breaks = break_input
    with pytest.raises(TypeError, match=error):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["population_break_input", "error"],
    [
        [{"start_time": "10:00", "finish_time": "11:00"}, "All breaks should be in a list. Got <class 'dict'>."],
        [[["start_time", "10:00", "finish_time", "11:00"]], "Each break should be a dictionary. Got <class 'list'>."],
        [[{"art_time": "10:00", "finish_time": "11:00"}], 'Unable to fetch "start_time" key. Got "art_time".'],
        [[{"start_time": "10:00", "ish_time": "11:00"}], 'Unable to fetch "finish_time" key. Got "ish_time".'],
        [[{"start_time": "10", "finish_time": "11:00"}], 'Wrong time format - "HH:MM". Got "10".'],
        [[{"start_time": "10:00", "finish_time": "11"}], 'Wrong time format - "HH:MM". Got "11".'],
    ]
)
def test_specific_population_break_data_structure(population_break_input, error, baseline_form: model_generator.VirusFormData):
    baseline_form.specific_breaks = {'exposed_breaks': population_break_input, 'infected_breaks': population_break_input}
    with pytest.raises(TypeError, match=error):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["break_input", "error"],
    [
        [[{"start_time": "07:00", "finish_time": "11:00"}, ], "All breaks should be within the simulation time. Got 07:00."],
        [[{"start_time": "17:00", "finish_time": "18:00"}, ], "All breaks should be within the simulation time. Got 18:00."],
        [[{"start_time": "10:00", "finish_time": "11:00"}, {"start_time": "17:00", "finish_time": "20:00"}, ], "All breaks should be within the simulation time. Got 20:00."],
        [[{"start_time": "08:00", "finish_time": "11:00"}, {"start_time": "14:00", "finish_time": "15:00"}, ], "All breaks should be within the simulation time. Got 08:00."],
    ]
)
def test_specific_break_time(break_input, error, baseline_form: model_generator.VirusFormData):
    with pytest.raises(ValueError, match=error):
        baseline_form.generate_specific_break_times(break_input)


@pytest.mark.parametrize(
    ["precise_activity_input", "error"],
    [
        [["physical_activity", "Light activity", "respiratory_activity", [{"type": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 50}]], "The precise activities should be in a dictionary."],
        [{"pysical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 50}]}, 'Unable to fetch "physical_activity" key. Got "pysical_activity".'],
        [{"physical_activity": "Light activity", "rspiratory_activity": [{"type": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 50}]}, 'Unable to fetch "respiratory_activity" key. Got "rspiratory_activity".'],
        [{"physical_activity": ["Light activity"], "respiratory_activity": [{"type": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 50}]}, "The physical activities should be a single string."],
        [{"physical_activity": "Light activity", "respiratory_activity": {"type": "Breathing", "percentage": 100}}, 'The respiratory activities should be in a list.'],
        [{"physical_activity": "Light activity", "respiratory_activity": [["type", "Speaking", "percentage", 100]]}, 'Each respiratory activity should be defined in a dictionary.'],
        [{"physical_activity": "Light activity", "respiratory_activity": [{"tpe": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 50}]}, 'Unable to fetch "type" key. Got "tpe".'],
        [{"physical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentag": 50}, {"type": "Speaking", "percentage": 50}]}, 'Unable to fetch "percentage" key. Got "percentag".'],
    ]
)
def test_precise_activity_structure(precise_activity_input, error, baseline_form: model_generator.VirusFormData):
    baseline_form.precise_activity = precise_activity_input
    with pytest.raises(TypeError, match=error):
        baseline_form.validate()


@pytest.mark.parametrize(
    ["precise_activity_input", "error"],
    [
        [{"physical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentage": 10}, {"type": "Speaking", "percentage": 50}]}, 'The sum of all respiratory activities should be 100. Got 60.'],
        [{"physical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentage": 50}, {"type": "Speaking", "percentage": 10}]}, 'The sum of all respiratory activities should be 100. Got 60.'],
        [{"physical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentage": 10}, {"type": "Speaking", "percentage": 50}, {"type": "Shouting", "percentage": 50}]}, 'The sum of all respiratory activities should be 100. Got 110.'],
        [{"physical_activity": "Light activity", "respiratory_activity": [{"type": "Breathing", "percentage": 50}]}, 'The sum of all respiratory activities should be 100. Got 50.'],
    ]
)
def test_sum_precise_activity(precise_activity_input, error, baseline_form: model_generator.VirusFormData):
    baseline_form.precise_activity = precise_activity_input
    with pytest.raises(ValueError, match=error):
        baseline_form.validate()