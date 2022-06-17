import numpy as np
import numpy.testing as npt
import pytest
from retry import retry

from cara.monte_carlo import sampleable


@retry(tries=10)
@pytest.mark.parametrize(
    "mean, std",[
        [1., 0.5],
    ]
)
def test_normal(mean, std):
    # Test that the sample has approximately the right mean,
    # std deviation and distribution function.
    sample_size = 2000000
    samples = sampleable.Normal(mean, std).generate_samples(sample_size)
    histogram, bins = np.histogram(samples,bins=100, density=True)
    selected_bins,selected_histogram = zip(*[(b,h) for b,h in zip(
                (bins[1:]+bins[:-1])/2,histogram) if b>=0.25 and b<=1.75])
    exact_dist = 1/(np.sqrt(2*np.pi)*std) * np.exp(
                    -((np.array(selected_bins)-mean)/std)**2/2)

    assert len(samples) == sample_size
    npt.assert_allclose([samples.mean(), samples.std()], [mean, std], rtol=0.01)
    npt.assert_allclose(selected_histogram, exact_dist, rtol=0.02)


@pytest.mark.parametrize(
    "mean_gaussian, std_gaussian",[
        [-0.6872121723362303, 0.10498338229297108],
    ]
)
def test_lognormal(mean_gaussian, std_gaussian):
    # Test that the sample has approximately the right mean,
    # std deviation and distribution function.
    sample_size = 2000000
    samples = sampleable.LogNormal(mean_gaussian, std_gaussian
                                ).generate_samples(sample_size)
    histogram, bins = np.histogram(samples,bins=50, density=True)
    selected_bins,selected_histogram = zip(*[(b,h) for b,h in zip(
                (bins[1:]+bins[:-1])/2,histogram) if b>=0.4 and b<=0.6])
    selected_bins = np.array(selected_bins)
    exact_dist = ( 1/(selected_bins*np.sqrt(2*np.pi)*std_gaussian) *
            np.exp(-((np.log(selected_bins)-mean_gaussian)/std_gaussian)**2/2) )
    exact_mean = np.exp(mean_gaussian + std_gaussian**2/2)
    exact_std = np.sqrt( (np.exp(std_gaussian**2)-1) *
                         np.exp(2*mean_gaussian + std_gaussian**2) )

    assert len(samples) == sample_size
    npt.assert_allclose([samples.mean(), samples.std()],
                        [exact_mean, exact_std], rtol=0.01)
    npt.assert_allclose(selected_histogram, exact_dist, rtol=0.03)


@pytest.mark.parametrize(
    "use_kernel",
    [False, True],
)
def test_custom(use_kernel):
    # Test that the sample has approximately the right distribution
    # function, with both Custom and CustomKernel method. The latter
    # is less accurate for smooth functions.
    # the distribution function is an inverted parabola, with maximum 0.15,
    # which is 0 at the bounds (0,10) (normalized)
    norm = 500/3.
    function = lambda x: (-(5 - x)**2 + 25)/norm
    max_function = 0.15
    sample_size = 2000000

    if use_kernel:
        variable = np.linspace(0.1,9.9,100) 
        frequencies = function(variable)
        samples = sampleable.CustomKernel(variable, frequencies,
                                    kernel_bandwidth=0.1
                                    ).generate_samples(sample_size)
    else:
        samples = sampleable.Custom((0, 10), function, max_function
                                    ).generate_samples(sample_size)

    histogram, bins = np.histogram(samples, bins=100, density=True)
    selected_bins,selected_histogram = zip(*[(b,h) for b,h in zip(
                (bins[1:]+bins[:-1])/2,histogram) if b>=1 and b<=9])
    correct_dist = function(np.array(selected_bins))
    assert len(samples) == sample_size
    npt.assert_allclose(selected_histogram, correct_dist, rtol=0.05)


def test_logcustomkernel():
    # Test that the sample has approximately the right distribution
    # function, for the LogCustomKernel.
    # the distribution function is an inverted parabola vs. the log of
    # the variable (normalized)
    norm = 500/3.
    function = lambda x: (-(5 - x)**2 + 25)/norm
    sample_size = 2000000

    log_variable = np.linspace(0.1,9.9,100)
    frequencies = function(log_variable)
    samples = sampleable.LogCustomKernel(log_variable, frequencies,
                                kernel_bandwidth=0.1
                                ).generate_samples(sample_size)

    histogram, bins = np.histogram(np.log10(samples), bins=100, density=True)
    selected_bins,selected_histogram = zip(*[(b,h) for b,h in zip(
                (bins[1:]+bins[:-1])/2,histogram) if b>=1 and b<=9])
    correct_dist = function(np.array(selected_bins))
    assert len(samples) == sample_size
    npt.assert_allclose(selected_histogram, correct_dist, rtol=0.05)
