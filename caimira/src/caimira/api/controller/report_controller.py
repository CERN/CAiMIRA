import concurrent.futures
import functools

from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.store.data_registry import DataRegistry
import caimira.calculator.report.report_generator as rg


def generate_form_obj(form_data, data_registry):
    return VirusFormData.from_dict(form_data, data_registry)


def generate_model(form_obj):
    return form_obj.build_model(250_000)


def generate_report_results(form_obj, model):
    return rg.calculate_report_data(form=form_obj, model=model, executor_factory=functools.partial(
        concurrent.futures.ThreadPoolExecutor, None,  # TODO define report_parallelism
    ),)


def submit_virus_form(form_data):
    data_registry = DataRegistry

    form_obj = generate_form_obj(form_data, data_registry)
    model = generate_model(form_obj)
    report_data = generate_report_results(form_obj, model=model)

    return report_data
