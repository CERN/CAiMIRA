from __future__ import annotations

from dataclasses import dataclass
import typing

import numpy as np
from scipy import special as sp
from scipy.stats import weibull_min

from caimira.enums import ViralLoads, InfectiousDoses, ViableToRNARatios

import caimira.monte_carlo.models as mc
from caimira.monte_carlo.sampleable import LogCustom, LogNormal, Normal, LogCustomKernel, CustomKernel, Uniform, Custom
from caimira.store.data_registry import DataRegistry


def evaluate_vl(value, data_registry: DataRegistry):
    if value == ViralLoads.COVID_OVERALL.value:
        return covid_overal_vl_data(data_registry)
    elif value == ViralLoads.SYMPTOMATIC_FREQUENCIES.value:
        return symptomatic_vl_frequencies
    else:
        raise ValueError(f"Invalid ViralLoads value {value}")


def evaluate_infectd(value, data_registry: DataRegistry):
    if value == InfectiousDoses.DISTRIBUTION.value:
        return infectious_dose_distribution(data_registry)
    else:
        raise ValueError(f"Invalid InfectiousDoses value {value}")


def evaluate_vtrr(value, data_registry: DataRegistry):
    if value == ViableToRNARatios.DISTRIBUTION.value:
        return viable_to_RNA_ratio_distribution(data_registry)
    else:
        raise ValueError(f"Invalid ViableToRNARatios value {value}")


sqrt2pi = np.sqrt(2.*np.pi)
sqrt2 = np.sqrt(2.)


def custom_distribution_lookup(dict: dict, key_part: str) -> typing.Any:
    """
    Look up a custom distribution based on a partial key.

    Args:
        dict (dict): The root to search.
        key_part (str): The distribution key to match.

    Returns:
        str: The associated distribution.
    """
    try:
        for key, value in dict.items():
            if (key_part in key):
                return value['associated_distribution']
    except KeyError:
        return f"Key '{key_part}' not found."


def evaluate_custom_distribution(dist: str, params: typing.Dict) -> typing.Any:
    """
    Evaluate a custom distribution.

    Args:
        dist (str): The type of distribution.
        params (Dict): The parameters for the distribution.

    Returns:
        Any: The generated distribution.

    Raises:
        ValueError: If the distribution type is not recognized.

    """
    if dist == 'Linear Space':
        return np.linspace(params['start'], params['stop'], params['num'])
    elif dist == 'Normal':
        return Normal(params['normal_mean_gaussian'], params['normal_standard_deviation_gaussian'])
    elif dist == 'Log-normal':
        return LogNormal(params['lognormal_mean_gaussian'], params['lognormal_standard_deviation_gaussian'])
    elif dist == 'Uniform':
        return Uniform(params['low'], params['high'])
    else:
        raise ValueError('Bad request - distribution not found.')


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

    if isinstance(value, str):
        if value == 'Custom':
            custom_distribution: typing.Dict = custom_distribution_lookup(
                root, 'custom distribution')
            for d, p in custom_distribution.items():
                return evaluate_custom_distribution(d, p)

    elif isinstance(value, dict):
        dist: str = root[param]['associated_distribution']
        params: typing.Dict = root[param]['parameters']
        return evaluate_custom_distribution(dist, params)

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


# From https://doi.org/10.1101/2021.10.14.21264988 and references therein
symptomatic_vl_frequencies = LogCustomKernel(
    np.array((2.46032, 2.67431, 2.85434, 3.06155, 3.25856, 3.47256, 3.66957, 3.85979, 4.09927, 4.27081,
              4.47631, 4.66653, 4.87204, 5.10302, 5.27456, 5.46478, 5.6533, 5.88428, 6.07281, 6.30549,
              6.48552, 6.64856, 6.85407, 7.10373, 7.30075, 7.47229, 7.66081, 7.85782, 8.05653, 8.27053,
              8.48453, 8.65607, 8.90573, 9.06878, 9.27429, 9.473, 9.66152, 9.87552)),
    np.array((0.001206885, 0.007851618, 0.008078144, 0.01502491, 0.013258014, 0.018528495, 0.020053765,
              0.021896167, 0.022047184, 0.018604005, 0.01547796, 0.018075445, 0.021503523, 0.022349217,
              0.025097721, 0.032875078, 0.030594727, 0.032573045, 0.034717482, 0.034792991,
              0.033267721, 0.042887485, 0.036846816, 0.03876473, 0.045016819, 0.040063473, 0.04883754,
              0.043944602, 0.048142864, 0.041588741, 0.048762031, 0.027921732, 0.033871788,
              0.022122693, 0.016927718, 0.008833228, 0.00478598, 0.002807662)),
    kernel_bandwidth=0.1
)


# Weibull distribution with a shape factor of 3.47 and a scale factor of 7.01.
# From https://elifesciences.org/articles/65774 and first line of the figure in
# https://iiif.elifesciences.org/lax:65774%2Felife-65774-fig4-figsupp3-v2.tif/full/1500,/0/default.jpg
def viral_load(data_registry):
    return np.linspace(
        weibull_min.ppf(
            data_registry.virological_data['covid_overal_vl_data']['start'],
            c=data_registry.virological_data['covid_overal_vl_data']['shape_factor'],
            scale=data_registry.virological_data['covid_overal_vl_data']['scale_factor']
        ),
        weibull_min.ppf(
            data_registry.virological_data['covid_overal_vl_data']['stop'],
            c=data_registry.virological_data['covid_overal_vl_data']['shape_factor'],
            scale=data_registry.virological_data['covid_overal_vl_data']['scale_factor']
        ),
        int(data_registry.virological_data['covid_overal_vl_data']['num'])
)
def frequencies_pdf(data_registry):
    return weibull_min.pdf(
        viral_load(data_registry),
        c=data_registry.virological_data['covid_overal_vl_data']['shape_factor'],
        scale=data_registry.virological_data['covid_overal_vl_data']['scale_factor']
    )
def covid_overal_vl_data(data_registry):
    return LogCustom(
        bounds=(data_registry.virological_data['covid_overal_vl_data']['min_bound'], data_registry.virological_data['covid_overal_vl_data']['max_bound']),
        function=lambda d: np.interp(
            d,
            viral_load(data_registry),
            frequencies_pdf(data_registry),
            data_registry.virological_data['covid_overal_vl_data']['interpolation_fp_left'],
            data_registry.virological_data['covid_overal_vl_data']['interpolation_fp_right']
        ),
        max_function=data_registry.virological_data['covid_overal_vl_data']['max_function']
    )


# Derived from data in doi.org/10.1016/j.ijid.2020.09.025 and
# https://iosh.com/media/8432/aerosol-infection-risk-hospital-patient-care-full-report.pdf (page 60)
def viable_to_RNA_ratio_distribution(data_registry):
    return Uniform(data_registry.virological_data['viable_to_RNA_ratio_distribution']['low'], data_registry.virological_data['viable_to_RNA_ratio_distribution']['high'])


# From discussion with virologists
def infectious_dose_distribution(data_registry):
    return Uniform(data_registry.virological_data['infectious_dose_distribution']['low'], data_registry.virological_data['infectious_dose_distribution']['high'])


# From https://doi.org/10.1101/2021.10.14.21264988 and references therein
def virus_distributions(data_registry):
    vd = data_registry.virological_data['virus_distributions']
    return {
        'SARS_CoV_2': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2']['transmissibility_factor'],
        ),
        'SARS_CoV_2_ALPHA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_ALPHA']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2_ALPHA']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2_ALPHA']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2_ALPHA']['transmissibility_factor'],
        ),
        'SARS_CoV_2_BETA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_BETA']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2_BETA']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2_BETA']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2_BETA']['transmissibility_factor'],
        ),
        'SARS_CoV_2_GAMMA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_GAMMA']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2_GAMMA']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2_GAMMA']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2_GAMMA']['transmissibility_factor'],
        ),
        'SARS_CoV_2_DELTA': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_DELTA']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2_DELTA']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2_DELTA']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2_DELTA']['transmissibility_factor'],
        ),
        'SARS_CoV_2_OMICRON': mc.SARSCoV2(
            viral_load_in_sputum=evaluate_vl(vd['SARS_CoV_2_OMICRON']['viral_load_in_sputum'], data_registry),
            infectious_dose=evaluate_infectd(vd['SARS_CoV_2_OMICRON']['infectious_dose'], data_registry),
            viable_to_RNA_ratio=evaluate_vtrr(vd['SARS_CoV_2_OMICRON']['viable_to_RNA_ratio'], data_registry),
            transmissibility_factor=vd['SARS_CoV_2_OMICRON']['transmissibility_factor'],
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
            if data_registry.mask_distributions['Type I']['Known filtration efficiency of masks when exhaling?'] == 'Yes' else None,
        ),
        'FFP2': mc.Mask(
            η_inhale=param_evaluation(
                data_registry.mask_distributions['FFP2'], 'η_inhale'),
            η_exhale=param_evaluation(
                data_registry.mask_distributions['FFP2'], 'η_exhale')
            if data_registry.mask_distributions['FFP2']['Known filtration efficiency of masks when exhaling?'] == 'Yes' else None,
        ),
        'Cloth': mc.Mask(
            η_inhale=param_evaluation(
                data_registry.mask_distributions['Cloth'], 'η_inhale'),
            η_exhale=param_evaluation(
                data_registry.mask_distributions['Cloth'], 'η_exhale')
            if data_registry.mask_distributions['Cloth']['Known filtration efficiency of masks when exhaling?'] == 'Yes' else None,
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
            d_min=param_evaluation(data_registry.expiration_particle['long_range_expiration_distributions'], 'minimum_diameter'),
            d_max=param_evaluation(data_registry.expiration_particle['long_range_expiration_distributions'], 'maximum_diameter')
        )
        for exp_type, BLO_factors in expiration_BLO_factors(data_registry).items()
    }


def short_range_expiration_distributions(data_registry):
    return {
        exp_type: expiration_distribution(
            data_registry=data_registry,
            BLO_factors=BLO_factors,
            d_min=param_evaluation(data_registry.expiration_particle['short_range_expiration_distributions'], 'minimum_diameter'),
            d_max=param_evaluation(data_registry.expiration_particle['short_range_expiration_distributions'], 'maximum_diameter')
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
