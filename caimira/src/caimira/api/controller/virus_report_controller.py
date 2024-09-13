import concurrent.futures
import functools

from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.store.data_registry import DataRegistry
import caimira.calculator.report.virus_report_data as rg


def generate_form_obj(form_data, data_registry):
    return VirusFormData.from_dict(
        form_data=form_data,
        data_registry=data_registry,
    )


def generate_model(form_obj, data_registry):
    sample_size = data_registry.monte_carlo['sample_size']
    return form_obj.build_model(sample_size=sample_size)


def generate_report_results(form_obj):
    return rg.calculate_report_data(
        form=form_obj,
        executor_factory=functools.partial(
            concurrent.futures.ThreadPoolExecutor, None,  # TODO define report_parallelism
        ),
    )


def submit_virus_form(form_data):
    data_registry = DataRegistry

    form_obj = generate_form_obj(form_data=form_data, data_registry=data_registry)
    model = generate_model(form_obj=form_obj, data_registry=data_registry)
    report_data = generate_report_results(form_obj=form_obj, model=model)

    return report_data
