from caimira.calculator.validators.co2.co2_validator import CO2FormData
from caimira.calculator.store.data_registry import DataRegistry


def generate_form_obj(form_data, data_registry):
    return CO2FormData.from_dict(form_data=form_data, data_registry=data_registry)


def generate_model(form_obj, data_registry):
    sample_size = data_registry.monte_carlo['sample_size']
    return form_obj.build_model(sample_size=sample_size)


def generate_report(model):
    return dict(model.CO2_fit_params())


def submit_CO2_form(form_data):
    data_registry = DataRegistry()

    form_obj = generate_form_obj(
        form_data=form_data, data_registry=data_registry)
    model = generate_model(form_obj=form_obj, data_registry=data_registry)
    report_data = generate_report(model=model)

    return report_data
