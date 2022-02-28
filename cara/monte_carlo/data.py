from dataclasses import dataclass
import typing

import numpy as np
from scipy import special as sp

import cara.monte_carlo as mc
from cara.monte_carlo.sampleable import Normal,LogNormal,LogCustomKernel,CustomKernel,Uniform

sqrt2pi = np.sqrt(2.*np.pi)
sqrt2 = np.sqrt(2.)


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
    #: factors assigned to resp. the B, L and O modes. They are
    # charateristics of the kind of expiratory activity (e.g. breathing,
    # speaking, singing, or shouting). These are applied on top of the
    # cn concentrations (see below), and depend on the kind of activity
    # (breathing, speaking, singing/shouting)
    BLO_factors: typing.Tuple[float, float, float]

    #: cn (cm^-3) for resp. the B, L and O modes. Corresponds to the
    # total concentration of aerosols for each mode.
    cn: typing.Tuple[float, float, float] = (0.06, 0.2, 0.0010008)

    # mean of the underlying normal distributions (represents the log of a
    # diameter in microns), for resp. the B, L and O modes.
    mu: typing.Tuple[float, float, float] = (0.989541, 1.38629, 4.97673)

    # std deviation of the underlying normal distribution, for resp.
    # the B, L and O modes.
    sigma: typing.Tuple[float, float, float] = (0.262364, 0.506818, 0.585005)

    def distribution(self, d):
        """
        Returns the raw value of the probability distribution for a
        given diameter d (microns).
        """
        return sum( (1 / d) * (A * cn / (sqrt2pi * sigma)) *
                    np.exp(-(np.log(d) - mu) ** 2 / (2 * sigma ** 2))
                    for A,cn,mu,sigma in zip(self.BLO_factors, self.cn,
                                             self.mu, self.sigma) )

    def integrate(self, dmin, dmax):
        """ 
        Returns the integral between dmin and dmax (in microns) of the 
        probability distribution.
        """
        result = 0.
        for A,cn,mu,sigma in zip(self.BLO_factors, self.cn, self.mu, self.sigma):
            ymin = (np.log(dmin)-mu)/(sqrt2*sigma)
            ymax = (np.log(dmax)-mu)/(sqrt2*sigma)
            result += A * cn * (sp.erf(ymax)-sp.erf(ymin)) / 2.
        return result


# From https://doi.org/10.1101/2021.10.14.21264988 and references therein
activity_distributions = {
    'Seated': mc.Activity(LogNormal(-0.6872121723362303, 0.10498338229297108),
                          LogNormal(-0.6872121723362303, 0.10498338229297108)),

    'Standing': mc.Activity(LogNormal(-0.5742377578494785, 0.09373162411398223),
                            LogNormal(-0.5742377578494785, 0.09373162411398223)),

    'Light activity': mc.Activity(LogNormal(0.21380242785625422,0.09435378091059601),
                                  LogNormal(0.21380242785625422,0.09435378091059601)),

    'Moderate activity': mc.Activity(LogNormal(0.551771330362601, 0.1894616357138137),
                                     LogNormal(0.551771330362601, 0.1894616357138137)),

    'Heavy exercise': mc.Activity(LogNormal(1.1644665696723049, 0.21744554768657565),
                                  LogNormal(1.1644665696723049, 0.21744554768657565)),
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

# Derived from data in doi.org/10.1016/j.ijid.2020.09.025 and
# https://iosh.com/media/8432/aerosol-infection-risk-hospital-patient-care-full-report.pdf (page 60)
viable_to_RNA_ratio_distribution = Uniform(0.01, 0.6)

# From discussion with virologists
infectious_dose_distribution = Uniform(10., 100.)

# From https://doi.org/10.1101/2021.10.14.21264988 and refererences therein
virus_distributions = {
    'SARS_CoV_2': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=1.,
                ),
    'SARS_CoV_2_ALPHA': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=0.78,
                ),
    'SARS_CoV_2_BETA': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=0.8,
                ),
    'SARS_CoV_2_GAMMA': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=0.72,
                ),
    'SARS_CoV_2_DELTA': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=0.51,
                ),
    'SARS_CoV_2_OMICRON': mc.SARSCoV2(
                viral_load_in_sputum=symptomatic_vl_frequencies,
                infectious_dose=infectious_dose_distribution,
                viable_to_RNA_ratio=viable_to_RNA_ratio_distribution,
                transmissibility_factor=0.2,
                ),            
}


# From:
# https://doi.org/10.1080/02786826.2021.1890687
# https://doi.org/10.1016/j.jhin.2013.02.007
# https://doi.org/10.4209/aaqr.2020.08.0531
mask_distributions = {
    'Type I': mc.Mask(Uniform(0.25, 0.80)),
    'FFP2': mc.Mask(Uniform(0.83, 0.91)),
}


def expiration_distribution(
        BLO_factors: typing.Tuple[float, float, float],
        d_max=30.,
) -> mc.Expiration:
    """
    Returns an Expiration with an aerosol diameter distribution, defined
    by the BLO factors (a length-3 tuple).
    The total concentration of aerosols, cn, is computed by integrating
    the distribution between 0.1 and 30 microns - these boundaries are
    an historical choice based on previous implementations of the model
    (it limits the influence of the O-mode).
    """
    dscan = np.linspace(0.1, d_max, 3000)
    return mc.Expiration(
        CustomKernel(
            dscan,
            BLOmodel(BLO_factors).distribution(dscan),
            kernel_bandwidth=0.1,
        ),
        cn=BLOmodel(BLO_factors).integrate(0.1, d_max),
    )


def dilution_factor(activities, distance, D=0.02):
    factors = []
    for activity in activities:
        u0 = 0.98 if activity == "Breathing" else 3.9
        tstar = 2.0
        Cr1 = 0.18
        Cr2 = 0.2
        Cx1 = 2.4
        # The expired flow rate during the expiration period, m^3/s
        Q0 = u0 * np.pi/4*D**2 
        # Parameters in the jet-like stage
        x01 = D/2/Cr1
        # Time of virtual origin
        t01 = (x01/Cx1)**2 * (Q0*u0)**(-0.5)
        # The transition point, m
        xstar = Cx1*(Q0*u0)**0.25*(tstar + t01)**0.5 - x01
        # Dilution factor at the transition point xstar
        Sxstar = 2*Cr1*(xstar+x01)/D
        factors.append(
            np.piecewise(
                distance,
                [distance < xstar, distance >= xstar],
                [
                    lambda distance: 2*Cr1*(distance + x01)/D,
                    lambda distance: Sxstar*(1 + Cr2*(distance - xstar)/Cr1/(xstar + x01))**3
                ]
            )
        )
    return factors


expiration_BLO_factors = {
    'Breathing': (1., 0., 0.),
    'Speaking':   (1., 1., 1.),
    'Singing':   (1., 5., 5.),
    'Shouting':  (1., 5., 5.),
}


expiration_distributions = {
    exp_type: expiration_distribution(BLO_factors)
    for exp_type, BLO_factors in expiration_BLO_factors.items()
}


short_range_expiration_distributions = {
    exp_type: expiration_distribution(BLO_factors, d_max=100)
    for exp_type, BLO_factors in expiration_BLO_factors.items()
}
