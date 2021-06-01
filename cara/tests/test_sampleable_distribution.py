import numpy as np
import numpy.testing as npt
import pytest

from cara.monte_carlo import sampleable

@pytest.mark.parametrize(
    "mean, std",[
        [1., 0.5],
    ]
)
def test_normal(mean, std):
    # test that the sample has approximately the right mean,
    # std deviation and distribution function.
    sample_size = 2000000
    samples = sampleable.Normal(mean, std).generate_samples(sample_size)
    histogram, bins = np.histogram(samples,bins=100, density=True)
    x = (bins[1:]+bins[:-1])/2
    exact_dist = 1/(np.sqrt(2*np.pi)*std) * np.exp(-((x-mean)/std)**2/2)

    assert len(samples) == sample_size
    npt.assert_allclose([samples.mean(), samples.std()], [mean, std], atol=mean/100)
    npt.assert_allclose(histogram, exact_dist, atol=exact_dist.mean()/20)


@pytest.mark.parametrize(
    "mean_gaussian, std_gaussian",[
        [-0.6872121723362303, 0.10498338229297108],
    ]
)
def test_lognormal(mean_gaussian, std_gaussian):
    # test that the sample has approximately the right mean,
    # std deviation and distribution function.
    sample_size = 2000000
    samples = sampleable.LogNormal(mean_gaussian, std_gaussian
                                ).generate_samples(sample_size)
    histogram, bins = np.histogram(samples,bins=50, density=True)
    x = (bins[1:]+bins[:-1])/2
    exact_dist = ( 1/(x*np.sqrt(2*np.pi)*std_gaussian) * 
                   np.exp(-((np.log(x)-mean_gaussian)/std_gaussian)**2/2) )
    exact_mean = np.exp(mean_gaussian + std_gaussian**2/2)
    exact_std = np.sqrt( (np.exp(std_gaussian**2)-1) *
                         np.exp(2*mean_gaussian + std_gaussian**2) )

    assert len(samples) == sample_size
    npt.assert_allclose([samples.mean(), samples.std()],
                        [exact_mean, exact_std], atol=exact_mean/100)
    npt.assert_allclose(histogram, exact_dist, atol=exact_dist.mean()/20)


@pytest.mark.parametrize(
    "use_kernel",
    [False, True],
)
def test_custom(use_kernel):
    # test that the sample has approximately the right distribution
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
        tolerance = max_function/10
    else:
        samples = sampleable.Custom((0, 10), function, max_function
                                    ).generate_samples(sample_size)
        tolerance = max_function/50

    histogram, bins = np.histogram(samples, bins=100, density=True)
    correct_dist = function((bins[1:]+bins[:-1])/2)
    assert len(samples) == sample_size
    npt.assert_allclose(histogram, correct_dist, atol=tolerance)
