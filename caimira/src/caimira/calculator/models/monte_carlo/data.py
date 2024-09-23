from __future__ import annotations

from dataclasses import dataclass
import typing

import numpy as np
from scipy import special as sp
from scipy.stats import weibull_min

from ..enums import ViralLoads

import caimira.calculator.models.monte_carlo.models as mc
from caimira.calculator.models.monte_carlo.sampleable import LogCustom, LogNormal, Normal, LogCustomKernel, CustomKernel, Uniform, Custom
from caimira.calculator.store.data_registry import DataRegistry


def evaluate_vl(root: typing.Dict, value: str, data_registry: DataRegistry):
    if root[value] == ViralLoads.COVID_OVERALL.value:
        return covid_overal_vl_data(data_registry)
    elif root[value] == ViralLoads.SYMPTOMATIC_FREQUENCIES.value:
        return symptomatic_vl_frequencies(data_registry)
    elif root[value] == 'Custom':
        return param_evaluation(root, 'Viral load custom')
    else:
        raise ValueError(f"Invalid ViralLoads value {value}")


sqrt2pi = np.sqrt(2.*np.pi)
sqrt2 = np.sqrt(2.)


def custom_value_type_lookup(dict: dict, key_part: str) -> typing.Any:
    """
    Look up a custom value type based on a partial key.

    Args:
        dict (dict): The root to search.
        key_part (str): The value type key to match.

    Returns:
        str: The associated value.
    """
    try:
        for key, value in dict.items():
            if (key_part in key):
                return value['associated_value']
    except KeyError:
        return f"Key '{key_part}' not found."


def evaluate_custom_value_type(value_type: str, params: typing.Dict) -> typing.Any:
    """
    Evaluate a custom value type.

    Args:
        dist (str): The type of value.
        params (Dict): The parameters for the value type.

    Returns:
        Any: The generated value.

    Raises:
        ValueError: If the value type is not recognized.

    """
    if value_type == 'Constant value':
        return params
    elif value_type == 'Normal distribution':
        return Normal(
            mean=params['normal_mean_gaussian'], 
            standard_deviation=params['normal_standard_deviation_gaussian']
        )
    elif value_type == 'Log-normal distribution':
        return LogNormal(
            mean_gaussian=params['lognormal_mean_gaussian'], 
            standard_deviation_gaussian=params['lognormal_standard_deviation_gaussian']
        )
    elif value_type == 'Uniform distribution':
        return Uniform(
            low=params['low'], 
            high=params['high']
        )
    elif value_type == 'Log Custom Kernel distribution':
        return LogCustomKernel(
            log_variable=np.array(params['log_variable']), 
            frequencies=np.array(params['frequencies']), 
            kernel_bandwidth=params['kernel_bandwidth']
        )
    else:
        raise ValueError('Bad request - value type not found.')


def param_evaluation(root: typing.Dict, param: typing.Union[str, typing.Any]) -> typing.Any:
    """
    Evaluate a parameter from a nested dictionary.

    Args:
        root (dict): The root dictionary.
        param (Union[str, Any]): The parameter to evaluate.

    Returns:
        Any: The evaluated value.

    Raises:
        TypeError: If the type of the parameter is not defined.

    """
    value = root.get(param)

    if isinstance(value, dict):
        value_type: str = root[param]['associated_value']
        params: typing.Dict = root[param]['parameters']
        return evaluate_custom_value_type(value_type, params)

    elif isinstance(value, float) or isinstance(value, int):
        return value

    else:
        raise TypeError('Bad request - type not allowed.')


@dataclass(frozen=True)
class BLOmodel:
    """
    Represents the probability distribution from the BLO model.
    It is a sum of three lognormal distributions, each of the form
    A * cn * (1 / d) * (1 / (np.sqrt(2 * np.pi) * sigma)) *
            np.exp(-(np.log(d)-mu) ** 2 / (2 * sigma ** 2))
    with A the factor in front of the B, L or O mode.
    From G. Johnson et al., Modality of human
    expired aerosol size distributions, Journal of Aerosol Science,
    vol. 42, no. 12, pp. 839 – 851, 2011,
    https://doi.org/10.1016/j.jaerosci.2011.07.009).
    """
    data_registry: DataRegistry
    #: Factors assigned to resp. the B, L and O modes. They are
    # charateristics of the kind of expiratory activity (e.g. breathing,
    # speaking, singing, or shouting). These are applied on top of the
    # cn concentrations (see below), and depend on the kind of activity
    # (breathing, speaking, singing/shouting)
    BLO_factors: typing.Tuple[float, float, float]

    #: cn (cm^-3) for resp. the B, L and O modes. Corresponds to the
    # total concentration of aerosols for each mode.
    @property
    def cn(self) -> typing.Tuple[float, float, float]:
        _cn = self.data_registry.expiration_particle['BLOmodel']['cn'] # type: ignore
        return (_cn['B'],_cn['L'],_cn['O'])

    # Mean of the underlying normal distributions (represents the log of a
    # diameter in microns), for resp. the B, L and O modes.
    @property
    def mu(self) -> typing.Tuple[float, float, float]:
        _mu = self.data_registry.expiration_particle['BLOmodel']['mu'] # type: ignore
        return (_mu['B'], _mu['L'], _mu['O'])

    # Std deviation of the underlying normal distribution, for resp.
    # the B, L and O modes.
    @property
    def sigma(self) -> typing.Tuple[float, float, float]:
        _sigma = self.data_registry.expiration_particle['BLOmodel']['sigma'] # type: ignore
        return (_sigma['B'],_sigma['L'],_sigma['O'])

    def distribution(self, d):
        """
        Returns the raw value of the probability distribution for a
        given diameter d (microns).
        """
        return sum((1 / d) * (A * cn / (sqrt2pi * sigma)) *
                   np.exp(-(np.log(d) - mu) ** 2 / (2 * sigma ** 2))
                   for A, cn, mu, sigma in zip(self.BLO_factors, self.cn,
                                               self.mu, self.sigma))

    def integrate(self, dmin, dmax):
        """
        Returns the integral between dmin and dmax (in microns) of the
        probability distribution.
        """
        result = 0.
        for A, cn, mu, sigma in zip(self.BLO_factors, self.cn, self.mu, self.sigma):
            ymin = (np.log(dmin)-mu)/(sqrt2*sigma)
            ymax = (np.log(dmax)-mu)/(sqrt2*sigma)
            result += A * cn * (sp.erf(ymax)-sp.erf(ymin)) / 2.
        return result


# From https://doi.org/10.1101/2021.10.14.21264988 and references therein
def activity_distributions(data_registry):
    return {
        'Seated': mc.Activity(
            inhalation_rate=param_evaluation(
                data_registry.activity_distributions['Seated'], 'inhalation_rate'),
            exhalation_rate=param_evaluation(
                data_registry.activity_distributions['Seated'], 'exhalation_rate'),
        ),

        'Standing': mc.Activity(
            inhalation_rate=param_evaluation(
                data_registry.activity_distributions['Standing'], 'inhalation_rate'),
            exhalation_rate=param_evaluation(
                data_registry.activity_distributions['Standing'], 'exhalation_rate'),
        ),

        'Light activity': mc.Activity(
            inhalation_rate=param_evaluation(
                data_registry.activity_distributions['Light activity'], 'inhalation_rate'),
            exhalation_rate=param_evaluation(
                data_registry.activity_distributions['Light activity'], 'exhalation_rate'),
        ),

        'Moderate activity': mc.Activity(
            inhalation_rate=param_evaluation(
                data_registry.activity_distributions['Moderate activity'], 'inhalation_rate'),
            exhalation_rate=param_evaluation(
                data_registry.activity_distributions['Moderate activity'], 'exhalation_rate'),
        ),

        'Heavy exercise': mc.Activity(
            inhalation_rate=param_evaluation(
                data_registry.activity_distributions['Heavy exercise'], 'inhalation_rate'),
            exhalation_rate=param_evaluation(
                data_registry.activity_distributions['Heavy exercise'], 'exhalation_rate'),
        ),
    }


# From https://doi.org/10.1098/rsfs.2021.0076 and references therein
def symptomatic_vl_frequencies(data_registry):
    return param_evaluation(data_registry.virological_data, 'symptomatic_vl_frequencies')


# Weibull distribution with a shape factor of 3.47 and a scale factor of 7.01.
# From https://elifesciences.org/articles/65774 and first line of the figure in
# https://iiif.elifesciences.org/lax:65774%2Felife-65774-fig4-figsupp3-v2.tif/full/1500,/0/default.jpg
def viral_load(data_registry):
    return np.linspace(
        weibull_min.ppf(
            data_registry.virological_data['covid_overal_vl_data']['parameters']['start'],
            c=data_registry.virological_data['covid_overal_vl_data']['parameters']['shape_factor'],
            scale=data_registry.virological_data['covid_overal_vl_data']['parameters']['scale_factor']
        ),
        weibull_min.ppf(
            data_registry.virological_data['covid_overal_vl_data']['parameters']['stop'],
            c=data_registry.virological_data['covid_overal_vl_data']['parameters']['shape_factor'],
            scale=data_registry.virological_data['covid_overal_vl_data']['parameters']['scale_factor']
        ),
        int(data_registry.virological_data['covid_overal_vl_data']['parameters']['num'])
)
def frequencies_pdf(data_registry):
    return weibull_min.pdf(
        viral_load(data_registry),
        c=data_registry.virological_data['covid_overal_vl_data']['parameters']['shape_factor'],
        scale=data_registry.virological_data['covid_overal_vl_data']['parameters']['scale_factor']
    )
def covid_overal_vl_data(data_registry):
    return LogCustom(
        bounds=(data_registry.virological_data['covid_overal_vl_data']['parameters']['min_bound'], data_registry.virological_data['covid_overal_vl_data']['parameters']['max_bound']),
        function=lambda d: np.interp(
            d,
            viral_load(data_registry),
            frequencies_pdf(data_registry),
            data_registry.virological_data['covid_overal_vl_data']['parameters']['interpolation_fp_left'],
            data_registry.virological_data['covid_overal_vl_data']['parameters']['interpolation_fp_right']
        ),
        max_function=data_registry.virological_data['covid_overal_vl_data']['parameters']['max_function']
    )


# Derived from data in doi.org/10.1016/j.ijid.2020.09.025 and
# https://iosh.com/media/8432/aerosol-infection-risk-hospital-patient-care-full-report.pdf (page 60)
def viable_to_RNA_ratio_distribution():
    return Uniform(0.01, 0.6)


# From discussion with virologists
def infectious_dose_distribution():
    return Uniform(10., 100.)


# From https://doi.org/10.1101/2021.10.14.21264988 and references therein
def virus_distributions(data_registry):
    vd = data_registry.virological_data['virus_distributions']
    return {
        'SARS_CoV_2': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2']['infectiousness_days']['value'],
        ),
        'SARS_CoV_2_ALPHA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_ALPHA'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2_ALPHA'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2_ALPHA'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2_ALPHA']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2_ALPHA']['infectiousness_days']['value'],
        ),
        'SARS_CoV_2_BETA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_BETA'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2_BETA'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2_BETA'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2_BETA']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2_BETA']['infectiousness_days']['value'],
        ),
        'SARS_CoV_2_GAMMA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_GAMMA'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2_GAMMA'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2_GAMMA'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2_GAMMA']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2_GAMMA']['infectiousness_days']['value'],
        ),
        'SARS_CoV_2_DELTA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_DELTA'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2_DELTA'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2_DELTA'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2_DELTA']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2_DELTA']['infectiousness_days']['value'],
        ),
        'SARS_CoV_2_OMICRON': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_OMICRON'], 'viral_load_in_sputum', data_registry),
            infectious_dose=param_evaluation(vd['SARS_CoV_2_OMICRON'], 'infectious_dose'),
            viable_to_RNA_ratio=param_evaluation(vd['SARS_CoV_2_OMICRON'], 'viable_to_RNA_ratio'),
            transmissibility_factor=vd['SARS_CoV_2_OMICRON']['transmissibility_factor']['value'],
            infectiousness_days=vd['SARS_CoV_2_OMICRON']['infectiousness_days']['value'],
        ),
    }


# From:
# https://doi.org/10.1080/02786826.2021.1890687
# https://doi.org/10.1016/j.jhin.2013.02.007
# https://doi.org/10.4209/aaqr.2020.08.0531
# https://doi.org/10.1080/02786826.2021.1890687
def mask_distributions(data_registry):
    return {
        'Type I': mc.Mask(
            η_inhale=param_evaluation(
                data_registry.mask_distributions['Type I'], 'η_inhale'),
            η_exhale=param_evaluation(
                data_registry.mask_distributions['Type I'], 'η_exhale')
            if data_registry.mask_distributions['Type I'].get('η_exhale') is not None else None,
            factor_exhale=data_registry.mask_distributions['Type I']['factor_exhale']['value']
        ),
        'FFP2': mc.Mask(
            η_inhale=param_evaluation(
                data_registry.mask_distributions['FFP2'], 'η_inhale'),
            η_exhale=param_evaluation(
                data_registry.mask_distributions['FFP2'], 'η_exhale')
            if data_registry.mask_distributions['FFP2'].get('η_exhale') is not None else None,
            factor_exhale=data_registry.mask_distributions['FFP2']['factor_exhale']['value']
        ),
        'Cloth': mc.Mask(
            η_inhale=param_evaluation(
                data_registry.mask_distributions['Cloth'], 'η_inhale'),
            η_exhale=param_evaluation(
                data_registry.mask_distributions['Cloth'], 'η_exhale')
            if data_registry.mask_distributions['Cloth'].get('η_exhale') is not None else None,
            factor_exhale=data_registry.mask_distributions['Cloth']['factor_exhale']['value']
        ),
    }


def expiration_distribution(
        data_registry,
        BLO_factors,
        d_min=0.1,
        d_max=30.,
):
    """
    Returns an Expiration with an aerosol diameter distribution, defined
    by the BLO factors (a length-3 tuple).
    The total concentration of aerosols, cn, is computed by integrating
    the distribution between 0.1 and 30 microns - these boundaries are
    an historical choice based on previous implementations of the model
    (it limits the influence of the O-mode).
    """
    dscan = np.linspace(d_min, d_max, 3000)
    return mc.Expiration(
        CustomKernel(
            dscan,
            BLOmodel(data_registry, BLO_factors).distribution(dscan),
            kernel_bandwidth=0.1,
        ),
        cn=BLOmodel(data_registry, BLO_factors).integrate(d_min, d_max),
    )


def expiration_BLO_factors(data_registry):
    breathing = data_registry.expiration_particle['expiration_BLO_factors']['Breathing']
    speaking = data_registry.expiration_particle['expiration_BLO_factors']['Speaking']
    singing = data_registry.expiration_particle['expiration_BLO_factors']['Singing']
    shouting = data_registry.expiration_particle['expiration_BLO_factors']['Shouting']
    return {
        'Breathing': (
            param_evaluation(breathing, 'B'),
            param_evaluation(breathing, 'L'),
            param_evaluation(breathing, 'O')
        ),
        'Speaking': (
            param_evaluation(speaking, 'B'),
            param_evaluation(speaking, 'L'),
            param_evaluation(speaking, 'O')
        ),
        'Singing': (
            param_evaluation(singing, 'B'),
            param_evaluation(singing, 'L'),
            param_evaluation(singing, 'O')
        ),
        'Shouting': (
            param_evaluation(shouting, 'B'),
            param_evaluation(shouting, 'L'),
            param_evaluation(shouting, 'O')
        ),
    }


def expiration_distributions(data_registry):
    return {
        exp_type: expiration_distribution(
            data_registry=data_registry,
            BLO_factors=BLO_factors,
            d_min=param_evaluation(data_registry.expiration_particle['particle_size_range']['long_range'], 'minimum_diameter'),
            d_max=param_evaluation(data_registry.expiration_particle['particle_size_range']['long_range'], 'maximum_diameter')
        )
        for exp_type, BLO_factors in expiration_BLO_factors(data_registry).items()
    }


def short_range_expiration_distributions(data_registry):
    return {
        exp_type: expiration_distribution(
            data_registry=data_registry,
            BLO_factors=BLO_factors,
            d_min=param_evaluation(data_registry.expiration_particle['particle_size_range']['short_range'], 'minimum_diameter'),
            d_max=param_evaluation(data_registry.expiration_particle['particle_size_range']['short_range'], 'maximum_diameter')
        )
        for exp_type, BLO_factors in expiration_BLO_factors(data_registry).items()
    }


# Derived from Fig 8 a) "stand-stand" in https://www.mdpi.com/1660-4601/17/4/1445/htm
distances = np.array((0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2,
                     1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2))
frequencies = np.array((0.0598036, 0.0946154, 0.1299152, 0.1064905, 0.1099066, 0.0998209, 0.0845298,
                       0.0479286, 0.0406084, 0.039795, 0.0205997, 0.0152316, 0.0118155, 0.0118155, 0.018485, 0.0205997))
def short_range_distances(data_registry):
    return Custom(
        bounds=(
            param_evaluation(data_registry.short_range_model['conversational_distance'], 'minimum_distance'),
            param_evaluation(data_registry.short_range_model['conversational_distance'], 'maximum_distance')
        ),
        function=lambda x: np.interp(x, distances, frequencies, left=0., right=0.),
        max_function=0.13
    )
