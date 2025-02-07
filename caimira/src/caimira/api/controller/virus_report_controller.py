import concurrent.futures
import functools
import typing

from caimira.calculator.validators.virus.virus_validator import VirusFormData
from caimira.calculator.store.data_registry import DataRegistry
import caimira.calculator.report.virus_report_data as rg


def generate_form_obj(form_data: typing.Dict, data_registry: DataRegistry) -> VirusFormData:
    return VirusFormData.from_dict(
        form_data=form_data,
        data_registry=data_registry,
    )


def generate_report(form_obj: VirusFormData, report_generation_parallelism: typing.Optional[int]) -> typing.Dict:
    return rg.calculate_report_data(
        form=form_obj,
        executor_factory=functools.partial(
            concurrent.futures.ThreadPoolExecutor,
            report_generation_parallelism,
        ),
    )


def submit_virus_form(form_data: typing.Dict, report_generation_parallelism: typing.Optional[int]) -> typing.Dict:
    data_registry: DataRegistry = DataRegistry()

    form_obj: VirusFormData = generate_form_obj(form_data=form_data, data_registry=data_registry)
    report_data: typing.Dict = generate_report(form_obj=form_obj, report_generation_parallelism=report_generation_parallelism)

    # Handle model representation
    if report_data['model']: report_data['model'] = repr(report_data['model'])

    return report_data
