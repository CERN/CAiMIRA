from dataclasses import dataclass
from cara import models
import numpy as np
import scipy.stats as sct
import typing
import matplotlib.pyplot as plt


# The (k, lambda) parameters for the weibull-distributions corresponding to each quantity
weibull_parameters = [((0.5951563631241763, 0.027071715346754264),          # emission_concentration
                       (15.312035476444153, 0.8433059432279654 * 3.33)),    # particle_diameter_breathing
                      ((2.0432559401256634, 3.3746316960164147),            # emission_rate_speaking
                       (5.9493671011143965, 1.081521101924364 * 3.33)),     # particle_diameter_speaking
                      ((2.317686940362959, 5.515253884170728),              # emission_rate_speaking_loudly
                       (7.348365409721486, 1.1158159287760463 * 3.33))]     # particle_diameter_speaking_loudly


def calculate_qr(viral_load: float, emission: float, diameter: float, mask_efficiency: float,
                 copies_per_quantum: float, breathing_rate: typing.Optional[float] = None) -> float:
    """
    Calculates the quantum generation rate given a set of parameters.
    """
    # Unit conversions
    diameter *= 1e-4
    viral_load = 10 ** viral_load
    emission = (emission * 3600) if breathing_rate is None else (emission * 1e6)

    volume = (4 * np.pi * (diameter / 2)**3) / 3
    if breathing_rate is None:
        breathing_rate = 1
    return viral_load * emission * volume * (1 - mask_efficiency) * breathing_rate / copies_per_quantum


def generate_qr_values(samples: int, expiratory_activity: int, masked: bool, qid: int = 100) -> np.ndarray:
    """
    Randomly samples values for the quantum generation rate
    :param samples: The total number of samples to be generated
    :param expiratory_activity: An integer signifying the expiratory activity of the infected subject
    (1 = breathing, 2 = speaking, 3 = speaking loudly)
    :param masked: True if infected subject is wearing a mask, False otherwise
    :param qid: The quantum infectious dose to be used in the calculations
    :return: A numpy array of length = samples, containing randomly generated qr-values
    """
    (e_k, e_lambda), (d_k, d_lambda) = weibull_parameters[expiratory_activity]
    emissions = sct.weibull_min.isf(sct.norm.sf(np.random.normal(size=samples)), e_k, loc=0, scale=e_lambda)
    diameters = sct.weibull_min.isf(sct.norm.sf(np.random.normal(size=samples)), d_k, loc=0, scale=d_lambda)
    viral_loads = np.random.normal(size=samples, loc=7.8, scale=1.7)

    mask_efficiency = [0.75, 0.81, 0.81][expiratory_activity] if masked else 0
    qr_func = np.vectorize(calculate_qr)

    # TODO: Add distributions for parameters
    breathing_rate = 1

    return qr_func(viral_loads, emissions, diameters, mask_efficiency, qid)


def logscale_hist(x: typing.Iterable, bins: int) -> None:
    """
    Plots the data of x as a log-scale histogram
    :param x: An array containing the data to be plotted
    :param bins: The number of bins to be used in the histogram (number of bars)
    :return: Nothing
    """
    hist, bins = np.histogram(x, bins=bins)
    logscale_bins = np.logspace(np.log10(bins[0]), np.log10(bins[-1]), len(bins))
    plt.hist(x, bins=logscale_bins)
    plt.xscale('log')
    plt.show()


def print_qr_info(qr_values: np.ndarray) -> None:
    log_qr = np.log10(qr_values)
    print(f"MEAN of log_10(qR) = {np.mean(log_qr)}\n"
          f"MEAN of qR = {np.mean(qr_values)}")

    for quantile in (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99):
        print(f"qR_{quantile} = {np.quantile(qr_values, quantile)}")
