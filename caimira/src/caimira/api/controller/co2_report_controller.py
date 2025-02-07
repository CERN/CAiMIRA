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


def generate_transition_times(CO2model: CO2DataModel, vent_transition_times: list) -> list:
    # The entire ventilation changes consider the initial and final occupancy state change
    occupancy_transition_times = list(CO2model.occupancy.transition_times)
    all_vent_transition_times: list = sorted(
        [occupancy_transition_times[0]] +
        [occupancy_transition_times[-1]] +
        vent_transition_times)
    return all_vent_transition_times


def request_CO2_transition_times(form_data: typing.Dict) -> list:
    data_registry: DataRegistry = DataRegistry()

    form_obj: CO2FormData = generate_form_obj(form_data=form_data, data_registry=data_registry)
    CO2model: CO2DataModel = generate_model(form_obj=form_obj)
    vent_transition_times: list = form_obj.find_change_points()
    all_vent_transition_times: list = generate_transition_times(CO2model, vent_transition_times)
    
    return all_vent_transition_times


def request_CO2_report(form_data: typing.Dict) -> typing.Dict:
    data_registry: DataRegistry = DataRegistry()

    form_obj: CO2FormData = generate_form_obj(form_data=form_data, data_registry=data_registry)
    model: CO2DataModel = generate_model(form_obj=form_obj)
    report_data: typing.Dict = generate_report(model=model)

    return report_data
