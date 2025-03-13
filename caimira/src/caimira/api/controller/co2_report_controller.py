import typing

from caimira.calculator.validators.co2.co2_validator import CO2FormData
from caimira.calculator.store.data_registry import DataRegistry
from caimira.calculator.models.models import CO2DataModel


def generate_form_obj(form_data: typing.Dict, data_registry: DataRegistry) -> CO2FormData:
    return CO2FormData.from_dict(form_data=form_data, data_registry=data_registry)


def generate_model(form_obj: CO2FormData) -> CO2DataModel:
    return form_obj.build_model()


def generate_report(model: CO2DataModel) -> typing.Dict:
    return dict(model.CO2_fit_params())


def request_CO2_transition_times(form_data: dict) -> dict:
    """
    Calculate and return the transition times related to CO2 levels including
    the ventilation transition times (identified from the change point algorithm)
    and relevant occupancy transition times (first and last occurrences).
    """
    data_registry = DataRegistry()

    form_obj = generate_form_obj(form_data=form_data, data_registry=data_registry)
    CO2model = generate_model(form_obj=form_obj)
    
    # Occupancy transition times
    occupancy_transition_times = list(CO2model.occupancy.transition_times)
    relevant_occupancy_times = [occupancy_transition_times[0]] + [occupancy_transition_times[-1]]
    # Ventilation transition times
    vent_transition_times = form_obj.find_change_points()
    ventilation_times = sorted(vent_transition_times)
    # Total transition times
    total_times = sorted(relevant_occupancy_times + ventilation_times)
    
    return {
        "occupancy_times": occupancy_transition_times,
        "ventilation_times": ventilation_times,
        "total_times": total_times
    }


def request_CO2_report(form_data: typing.Dict) -> typing.Dict:
    data_registry: DataRegistry = DataRegistry()

    form_obj: CO2FormData = generate_form_obj(form_data=form_data, data_registry=data_registry)
    model: CO2DataModel = generate_model(form_obj=form_obj)
    report_data: typing.Dict = generate_report(model=model)

    return report_data
