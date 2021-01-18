import cara.models
import numpy as np


def calculate_qr(viral_load: float, emission_concentration: float, diameter: float, mask_efficiency: float,
                 copies_per_quantum: float, breathing_rate: float = 1) -> float:
    """
    Calculates the quantum generation rate given a set of parameters.
    """
    volume = 4 * np.pi * (diameter / 2) ** 3 / 3
    return viral_load * emission_concentration * volume * (1 - mask_efficiency) * breathing_rate / copies_per_quantum
