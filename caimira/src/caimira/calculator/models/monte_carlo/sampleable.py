import typing

import numpy as np
from sklearn.neighbors import KernelDensity

from caimira.calculator.models import models

# Declare a float array type of a given size.
# There is no better way to declare this currently, unfortunately.
float_array_size_n = np.ndarray


class SampleableDistribution:
    def generate_samples(self, size: int) -> float_array_size_n:
        raise NotImplementedError()


class Normal(SampleableDistribution):
    """
    Defines a normal (i.e. Gaussian) distribution
    """
    def __init__(self, mean: float, standard_deviation: float):
        self.mean = mean
        self.standard_deviation = standard_deviation

    def generate_samples(self, size: int) -> float_array_size_n:
        return np.random.normal(self.mean, self.standard_deviation, size=size)


class Uniform(SampleableDistribution):
    """
    Defines a continuous uniform distribution
    """
    def __init__(self, low: float, high: float):
        self.low = low
        self.high = high

    def generate_samples(self, size: int) -> float_array_size_n:
        return np.random.uniform(self.low, self.high, size=size)


class LogNormal(SampleableDistribution):
    """
    Defines a lognormal distribution (i.e. Gaussian distribution vs. the
    natural logarithm of the random variable)
    """

    def __init__(self, mean_gaussian: float, standard_deviation_gaussian: float):
        # these are resp. the mean and std. deviation of the underlying
        # Gaussian distribution
        self.mean_gaussian = mean_gaussian
        self.standard_deviation_gaussian = standard_deviation_gaussian

    def generate_samples(self, size: int) -> float_array_size_n:
        return np.random.lognormal(self.mean_gaussian,
                                   self.standard_deviation_gaussian,
                                   size=size)


class Custom(SampleableDistribution):
    """
    Defines a distribution which follows a custom curve vs. the random
    variable. Uses a simple algorithm. This is appropriate for a smooth
    distribution function.
    Note: in max_function, a value slightly above the maximum of the distribution
    function should be provided.
    """
    def __init__(self, bounds: typing.Tuple[float, float],
                 function: typing.Callable, max_function: float):
        self.bounds = bounds
        self.function = function
        self.max_function = max_function

    def generate_samples(self, size: int) -> float_array_size_n:
        fvalue = np.random.uniform(0,self.max_function,size)
        x = np.random.uniform(*self.bounds,size)
        invalid = np.where(fvalue>self.function(x))[0]
        while len(invalid)>0:
            fvalue[invalid] = np.random.uniform(0,self.max_function,len(invalid))
            x[invalid] = np.random.uniform(*self.bounds,len(invalid))
            invalid = np.where(fvalue>self.function(x))[0]

        return x


class LogCustom(SampleableDistribution):
    """
    Defines a distribution which follows a custom curve vs. the log (in base 10)
    of the random variable. Uses a simple algorithm. This is appropriate for a smooth
    distribution function.
    Note: in max_function, a value slightly above the maximum of the distribution
    function should be provided.
    """
    def __init__(self, bounds: typing.Tuple[float, float],
                 function: typing.Callable, max_function: float):
        self.bounds = bounds
        self.function = function
        self.max_function = max_function

    def generate_samples(self, size: int) -> float_array_size_n:
        fvalue = np.random.uniform(0,self.max_function,size)
        x = np.random.uniform(*self.bounds,size)
        invalid = np.where(fvalue>self.function(x))[0]
        while len(invalid)>0:
            fvalue[invalid] = np.random.uniform(0,self.max_function,len(invalid))
            x[invalid] = np.random.uniform(*self.bounds,len(invalid))
            invalid = np.where(fvalue>self.function(x))[0]

        return 10 ** x


class CustomKernel(SampleableDistribution):
    """
    Defines a distribution which follows a custom curve vs. the
    random variable. Uses a Gaussian kernel density fit. This is more
    appropriate for a noisy distribution function.
    """
    def __init__(self, variable: float_array_size_n,
                 frequencies: float_array_size_n,
                 kernel_bandwidth: float):
        # these are resp. the random variable, the distribution
        # frequencies at these values, and the bandwidth of the Gaussian
        # kernel
        self.variable = variable
        self.frequencies = frequencies
        self.kernel_bandwidth = kernel_bandwidth

    def generate_samples(self, size: int) -> float_array_size_n:
        kde_model = KernelDensity(kernel='gaussian',
                                  bandwidth=self.kernel_bandwidth)
        kde_model.fit(self.variable.reshape(-1, 1),
                      sample_weight=self.frequencies)
        return kde_model.sample(n_samples=size)[:, 0]


class LogCustomKernel(SampleableDistribution):
    """
    Defines a distribution which follows a custom curve vs. the log
    (in base 10) of the random variable. Uses a Gaussian kernel density
    fit. This is more appropriate for a noisy distribution function.
    """
    def __init__(self, log_variable: float_array_size_n,
                 frequencies: float_array_size_n,
                 kernel_bandwidth: float):
        # these are resp. the log of the random variable, the distribution
        # frequencies at these values, and the bandwidth of the Gaussian
        # kernel
        self.log_variable = log_variable
        self.frequencies = frequencies
        self.kernel_bandwidth = kernel_bandwidth

    def generate_samples(self, size: int) -> float_array_size_n:
        kde_model = KernelDensity(kernel='gaussian',
                                  bandwidth=self.kernel_bandwidth)
        kde_model.fit(self.log_variable.reshape(-1, 1),
                      sample_weight=self.frequencies)
        return 10 ** kde_model.sample(n_samples=size)[:, 0]


_VectorisedFloatOrSampleable = typing.Union[
    SampleableDistribution, models._VectorisedFloat,
]
