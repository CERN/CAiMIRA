import cara.models
import numpy as np

# The (k, lambda) parameters for the weibull-distributions corresponding to each quantity
weibull_parameters = [((0.5951563631241763, 0.027071715346754264),  # emission_concentration
                       (15.312035476444153, 0.8433059432279654)),   # particle_diameter_breathing
                      ((2.0432559401256634, 3.3746316960164147),    # emission_rate_speaking
                       (5.9493671011143965, 1.081521101924364)),    # particle_diameter_speaking
                      ((2.317686940362959, 5.515253884170728),      # emission_rate_speaking_loudly
                       (7.348365409721486, 1.1158159287760463))]    # particle_diameter_speaking_loudly


def calculate_qr(viral_load: float, emission: float, diameter: float, mask_efficiency: float,
                 copies_per_quantum: float, breathing_rate: float = 1) -> float:
    """
    Calculates the quantum generation rate given a set of parameters.
    """
    volume = 4 * np.pi * (diameter / 2) ** 3 / 3
    return viral_load * emission * volume * (1 - mask_efficiency) * breathing_rate / copies_per_quantum
