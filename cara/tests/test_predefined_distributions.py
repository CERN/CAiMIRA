import numpy as np
import numpy.testing as npt
import pytest

from cara.monte_carlo.data import activity_distributions, virus_distributions

# TODO: seed better the random number generators
np.random.seed(2000)


# mean & std deviations from https://doi.org/10.1101/2021.10.14.21264988 (Table 3)
# NOTE: a mistake was corrected for the std deviation of the
# "Moderate exercise" case (0.37 in the report, but should be 0.34)
@pytest.mark.parametrize(
    "distribution, mean, std",[
        ['Seated', 0.51, 0.053],

        ['Standing', 0.57, 0.053],

        ['Light activity', 1.24, 0.12],

        ['Moderate activity', 1.77, 0.34],

        ['Heavy exercise', 3.28, 0.72,],
    ]
)
def test_activity_distributions(distribution, mean, std):
    activity = activity_distributions[distribution].build_model(size=1000000)
    npt.assert_allclose(activity.inhalation_rate.mean(), mean, atol=0.01)
    npt.assert_allclose(activity.inhalation_rate.std(), std, atol=0.01)


# mean & std deviations from https://doi.org/10.1101/2021.10.14.21264988 (Table 3) 
# - with a refined precision on the values
@pytest.mark.parametrize(
    "distribution, mean, std",[
        ['SARS_CoV_2', 6.59, 1.74],

        ['SARS_CoV_2_ALPHA', 6.59, 1.74],

        ['SARS_CoV_2_GAMMA', 6.59, 1.74],
    ]
)
def test_viral_load_logdistribution(distribution, mean, std):
    virus = virus_distributions[distribution].build_model(size=1000000)
    npt.assert_allclose(np.log10(virus.viral_load_in_sputum).mean(), mean, atol=0.01)
    npt.assert_allclose(np.log10(virus.viral_load_in_sputum).std(), std, atol=0.01)
