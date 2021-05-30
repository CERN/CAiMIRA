import typing

import numpy as np

import cara.models


# Declare a float array type of a given size.
# There is no better way to declare this currently, unfortunately.
float_array_size_n = np.ndarray


class SampleableDistribution:
    def generate_samples(self, size: int) -> float_array_size_n:
        raise NotImplementedError()


class Normal(SampleableDistribution):
    def __init__(self, mean: float, standard_deviation: float):
        self.mean = mean
        self.standard_deviation = standard_deviation

    def generate_samples(self, size: int) -> float_array_size_n:
        return np.random.normal(self.mean, self.standard_deviation, size=size)


_VectorisedFloatOrSampleable = typing.Union[
    SampleableDistribution, cara.models._VectorisedFloat,
]
