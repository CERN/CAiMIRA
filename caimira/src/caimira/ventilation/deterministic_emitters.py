from dataclasses import dataclass
import numpy as np

from caimira.calculator.models import models

@dataclass(frozen=True)
class DeterministicActivity:
    #: Inhalation rate in m^3/h
    inhalation_rate: float

    #: Exhalation rate in m^3/h
    exhalation_rate: float


@dataclass(frozen=True)
class DeterministicPopulation(models.SimplePopulation):
    """
    Represents a group of people with deterministic breathing rate.
    """
    activity: DeterministicActivity

    
@dataclass(frozen=True)
class DeterministicCO2ConcentrationModel(models.CO2ConcentrationModel):
    """
    Class used for the computation of the expected CO2 concentration.
    Fully deterministic. No Monte Carlo sampling of the breathing rate. 
    Setting the breathing rate as the expected breathing rate calculated
    from the mean and standard deviation of the log-normal distribution 
    for the breathing rate.
    """
    #: Population in the room emitting CO2
    CO2_emitters: DeterministicPopulation


def expected_breathing_rate(lognormal_mean_gaussian, lognormal_standard_deviation_gaussian) -> float:
    """
    Calculate the expected value for the inhalantion or exhalation rate.
    """
    return np.exp(lognormal_mean_gaussian + lognormal_standard_deviation_gaussian**2 / 2)


def deterministic_activity_distributions(data_registry):
    return {
        'Seated': DeterministicActivity(
            inhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Seated']['inhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Seated']['inhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
            exhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Seated']['exhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Seated']['exhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
        ),

        'Standing': DeterministicActivity(
            inhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Standing']['inhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Standing']['inhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
            exhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Standing']['exhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Standing']['exhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
        ),

        'Light activity': DeterministicActivity(
            inhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Light activity']['inhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Light activity']['inhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
            exhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Light activity']['exhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Light activity']['exhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
        ),

        'Moderate activity': DeterministicActivity(
            inhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Moderate activity']['inhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Moderate activity']['inhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
            exhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Moderate activity']['exhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Moderate activity']['exhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
        ),

        'Heavy exercise': DeterministicActivity(
            inhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Heavy exercise']['inhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Heavy exercise']['inhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
            exhalation_rate=expected_breathing_rate(
                data_registry.activity_distributions['Heavy exercise']['exhalation_rate']["parameters"]["lognormal_mean_gaussian"],
                data_registry.activity_distributions['Heavy exercise']['exhalation_rate']["parameters"]["lognormal_standard_deviation_gaussian"]
            ),
        ),
    }