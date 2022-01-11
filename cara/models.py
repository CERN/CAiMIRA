# This module is part of CARA. Please see the repository at
# https://gitlab.cern.ch/cara/cara for details of the license and terms of use.
"""
This module implements the core CARA models.

The CARA model is a flexible, object-oriented numerical model. It is designed
to allow the user to swap-out and extend its various components. One of the
major abstractions of the model is the distinction between virus concentration
(:class:`ConcentrationModel`) and virus exposure (:class:`ExposureModel`).

The concentration component is a recursive (on model time) model and therefore in order
to optimise its execution certain layers of caching are implemented. This caching
mandates that the models in this module, once instantiated, are immutable and
deterministic (i.e. running the same model twice will result in the same answer).

In order to apply stochastic / non-deterministic analyses therefore you must
introduce the randomness before constructing the models themselves; the
:mod:`cara.monte_carlo` module is a good example of doing this - that module uses
the models defined here to allow you to construct a ConcentrationModel containing
parameters which are expressed as probability distributions. Under the hood the
``cara.monte_carlo.ConcentrationModel`` implementation simply samples all of those
probability distributions to produce many instances of the deterministic model.

The models in this module have been designed for flexibility above performance,
particularly in the single-model case. By using the natural expressiveness of
Python we benefit from a powerful, readable and extendable implementation. A
useful feature of the implementation is that we are able to benefit from numpy
vectorisation in the case of wanting to run multiple-parameterisations of the model
at the same time. In order to benefit from this feature you must construct the models
with an array of parameter values. The values must be either scalar, length 1 arrays,
or length N arrays, where N is the number of parameterisations to run; N must be
the same for all parameters of a single model.

"""
from dataclasses import dataclass
import typing

import numpy as np
from scipy.interpolate import interp1d
import scipy.integrate
import scipy.stats as sct

if not typing.TYPE_CHECKING:
    from memoization import cached
else:
    # Workaround issue https://github.com/lonelyenvoy/python-memoization/issues/18
    # by providing a no-op cache decorator when type-checking.
    cached = lambda *cached_args, **cached_kwargs: lambda function: function  # noqa

from .utils import method_cache

from .dataclass_utils import nested_replace

oneoverln2 = 1 / np.log(2)
# Define types for items supporting vectorisation. In the future this may be replaced
# by ``np.ndarray[<type>]`` once/if that syntax is supported. Note that vectorization
# implies 1d arrays: multi-dimensional arrays are not supported.
_VectorisedFloat = typing.Union[float, np.ndarray]
_VectorisedInt = typing.Union[int, np.ndarray]


@dataclass(frozen=True)
class Room:
    #: The total volume of the room
    volume: _VectorisedFloat

    #: The humidity in the room (from 0 to 1 - e.g. 0.5 is 50% humidity)
    humidity: _VectorisedFloat = 0.5


Time_t = typing.TypeVar('Time_t', float, int)
BoundaryPair_t = typing.Tuple[Time_t, Time_t]
BoundarySequence_t = typing.Union[typing.Tuple[BoundaryPair_t, ...], typing.Tuple]


@dataclass(frozen=True)
class Interval:
    """
    Represents a collection of times in which a "thing" happens.

    The "thing" may be when an action is taken, such as opening a window, or
    entering a room.

    Note that all intervals are open at the start, and closed at the end. So a
    simple start, stop interval follows::

        start < t <= end

    """
    def boundaries(self) -> BoundarySequence_t:
        return ()

    def transition_times(self) -> typing.Set[float]:
        transitions = set()
        for start, end in self.boundaries():
            transitions.update([start, end])
        return transitions

    def triggered(self, time: float) -> bool:
        """Whether the given time falls inside this interval."""
        for start, end in self.boundaries():
            if start < time <= end:
                return True
        return False

@dataclass(frozen=True)
class SpecificInterval(Interval):
    #: A sequence of times (start, stop), in hours, that the infected person
    #: is present. The flattened list of times must be strictly monotonically
    #: increasing.
    present_times: BoundarySequence_t

    def boundaries(self) -> BoundarySequence_t:
        return self.present_times


@dataclass(frozen=True)
class PeriodicInterval(Interval):
    #: How often does the interval occur (minutes).
    period: float

    #: How long does the interval occur for (minutes).
    #: A value greater than :data:`period` signifies the event is permanently
    #: occurring, a value of 0 signifies that the event never happens.
    duration: float

    #: Time at which the first person (infected or exposed) arrives at the enclosed space.
    start: float = 0.0

    def boundaries(self) -> BoundarySequence_t:
        if self.period == 0 or self.duration == 0:
            return tuple()
        result = []
        for i in np.arange(self.start, 24, self.period / 60):
            # NOTE: It is important that the time type is float, not np.float, in
            # order to allow hashability (for caching).
            result.append((float(i), float(i+self.duration/60)))
        return tuple(result)


@dataclass(frozen=True)
class PiecewiseConstant:

    # TODO: implement rather a periodic version (24-hour period), where
    # transition_times and values have the same length.

    #: transition times at which the function changes value (hours).
    transition_times: typing.Tuple[float, ...]

    #: values of the function between transitions
    values: typing.Tuple[_VectorisedFloat, ...]

    def __post_init__(self):
        if len(self.transition_times) != len(self.values)+1:
            raise ValueError("transition_times must contain one more element than values")
        if tuple(sorted(set(self.transition_times))) != self.transition_times:
            raise ValueError("transition_times must not contain duplicated elements and must be sorted")
        shapes = [np.array(v).shape for v in self.values]
        if not all(shapes[0] == shape for shape in shapes):
            raise ValueError("All values must have the same shape")

    def value(self, time) -> _VectorisedFloat:
        if time <= self.transition_times[0]:
            return self.values[0]
        elif time > self.transition_times[-1]:
            return self.values[-1]

        for t1, t2, value in zip(self.transition_times[:-1],
                                 self.transition_times[1:], self.values):
            if t1 < time <= t2:
                break
        return value

    def interval(self) -> Interval:
        # build an Interval object
        present_times = []
        for t1, t2, value in zip(self.transition_times[:-1],
                                 self.transition_times[1:], self.values):
            if value:
                present_times.append((t1, t2))
        return SpecificInterval(present_times=tuple(present_times))

    def refine(self, refine_factor=10) -> "PiecewiseConstant":
        # build a new PiecewiseConstant object with a refined mesh,
        # using a linear interpolation in-between the initial mesh points
        refined_times = np.linspace(self.transition_times[0], self.transition_times[-1],
                                    (len(self.transition_times)-1) * refine_factor+1)
        interpolator = interp1d(
            self.transition_times,
            np.concatenate([self.values, self.values[-1:]], axis=0),
            axis=0)
        return PiecewiseConstant(
            # NOTE: It is important that the time type is float, not np.float, in
            # order to allow hashability (for caching).
            tuple(float(time) for time in refined_times),
            tuple(interpolator(refined_times)[:-1]),
        )


@dataclass(frozen=True)
class _VentilationBase:
    """
    Represents a mechanism by which air can be exchanged (replaced/filtered)
    in a time dependent manner.

    The nature of the various air exchange schemes means that it is expected
    for subclasses of Ventilation to exist. Known subclasses include
    WindowOpening for window based air exchange, and HEPAFilter, for
    mechanical air exchange through a filter.

    """
    def transition_times(self) -> typing.Set[float]:
        raise NotImplementedError("Subclass must implement")

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        """
        Returns the rate at which air is being exchanged in the given room
        at a given time (in hours).

        Note that whilst the time is known inside this function, it may not
        be used to vary the result unless the specific time used is declared
        as part of a state change in the interval (e.g. when air_exchange == 0).

        """
        return 0.


@dataclass(frozen=True)
class Ventilation(_VentilationBase):
    #: The interval in which the ventilation is active.
    active: Interval

    def transition_times(self) -> typing.Set[float]:
        return self.active.transition_times()


@dataclass(frozen=True)
class MultipleVentilation(_VentilationBase):
    """
    Represents a mechanism by which air can be exchanged (replaced/filtered)
    in a time dependent manner.

    Group together different sources of ventilations.

    """
    ventilations: typing.Tuple[_VentilationBase, ...]

    def transition_times(self) -> typing.Set[float]:
        transitions = set()
        for ventilation in self.ventilations:
            transitions.update(ventilation.transition_times())
        return transitions

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        """
        Returns the rate at which air is being exchanged in the given room
        at a given time (in hours).
        """
        return np.array([
            ventilation.air_exchange(room, time)
            for ventilation in self.ventilations
        ]).sum(axis=0)


@dataclass(frozen=True)
class WindowOpening(Ventilation):
    #: The interval in which the window is open.
    active: Interval

    #: The temperature inside the room (Kelvin).
    inside_temp: PiecewiseConstant

    #: The temperature outside of the window (Kelvin).
    outside_temp: PiecewiseConstant

    #: The height of the window (m).
    window_height: _VectorisedFloat

    #: The length of the opening-gap when the window is open (m).
    opening_length: _VectorisedFloat

    #: The number of windows of the given dimensions.
    number_of_windows: int = 1

    #: Minimum difference between inside and outside temperature (K).
    min_deltaT: float = 0.1

    @property
    def discharge_coefficient(self) -> _VectorisedFloat:
        """
        Discharge coefficient (or cd_b): what portion effective area is
        used to exchange air (0 <= discharge_coefficient <= 1).
        To be implemented in subclasses.
        """
        raise NotImplementedError("Unknown discharge coefficient")

    def transition_times(self) -> typing.Set[float]:
        transitions = super().transition_times()
        transitions.update(self.inside_temp.transition_times)
        transitions.update(self.outside_temp.transition_times)
        return transitions

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        # If the window is shut, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.

        # Reminder, no dependence on time in the resulting calculation.
        inside_temp: _VectorisedFloat = self.inside_temp.value(time)
        outside_temp: _VectorisedFloat = self.outside_temp.value(time)

        # The inside_temperature is forced to be always at least min_deltaT degree
        # warmer than the outside_temperature. Further research needed to
        # handle the buoyancy driven ventilation when the temperature gradient
        # is inverted.
        inside_temp = np.maximum(inside_temp, outside_temp + self.min_deltaT)  # type: ignore
        temp_gradient = (inside_temp - outside_temp) / outside_temp
        root = np.sqrt(9.81 * self.window_height * temp_gradient)
        window_area = self.window_height * self.opening_length * self.number_of_windows
        return (3600 / (3 * room.volume)) * self.discharge_coefficient * window_area * root


@dataclass(frozen=True)
class SlidingWindow(WindowOpening):
    """
    Sliding window, or side-hung window (with the hinge perpendicular to
    the horizontal plane).
    """
    @property
    def discharge_coefficient(self) -> _VectorisedFloat:
        """
        Average measured value of discharge coefficient for sliding or
        side-hung windows.
        """
        return 0.6


@dataclass(frozen=True)
class HingedWindow(WindowOpening):
    """
    Top-hung or bottom-hung hinged window (with the hinge parallel to
    horizontal plane).
    """
    #: Window width (m).
    window_width: _VectorisedFloat = 0.0

    def __post_init__(self):
        if self.window_width is float(0.0):
            raise ValueError('window_width must be set')

    @property
    def discharge_coefficient(self) -> _VectorisedFloat:
        """
        Simple model to compute discharge coefficient for top or bottom
        hung hinged windows, in the absence of empirical test results
        from manufacturers.
        From an excel spreadsheet calculator (Richard Daniels, Crawford
        Wright, Benjamin Jones - 2018) from the UK government -
        see Section 8.3 of BB101 and Section 11.3 of
        ESFA Output Specification Annex 2F on Ventilation opening areas.
        """
        window_ratio = np.array(self.window_width / self.window_height)
        coefs = np.empty(window_ratio.shape + (2, ), dtype=np.float64)

        coefs[window_ratio < 0.5] = (0.06, 0.612)
        coefs[np.bitwise_and(0.5 <= window_ratio, window_ratio < 1)] = (0.048, 0.589)
        coefs[np.bitwise_and(1 <= window_ratio, window_ratio < 2)] = (0.04, 0.563)
        coefs[window_ratio >= 2] = (0.038, 0.548)
        M, cd_max = coefs.T

        window_angle = 2.*np.rad2deg(np.arcsin(self.opening_length/(2.*self.window_height)))
        return cd_max*(1-np.exp(-M*window_angle))


@dataclass(frozen=True)
class HEPAFilter(Ventilation):
    #: The interval in which the HEPA filter is operating.
    active: Interval

    #: The rate at which the HEPA exchanges air (when switched on)
    # in m^3/h
    q_air_mech: _VectorisedFloat

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        # If the HEPA is off, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.
        # Reminder, no dependence on time in the resulting calculation.
        return self.q_air_mech / room.volume


@dataclass(frozen=True)
class HVACMechanical(Ventilation):
    #: The interval in which the mechanical ventilation (HVAC) is operating.
    active: Interval

    #: The rate at which the HVAC exchanges air (when switched on)
    # in m^3/h
    q_air_mech: _VectorisedFloat

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        # If the HVAC is off, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.
        # Reminder, no dependence on time in the resulting calculation.
        return self.q_air_mech / room.volume


@dataclass(frozen=True)
class AirChange(Ventilation):
    #: The interval in which the ventilation is operating.
    active: Interval

    #: The rate (in h^-1) at which the ventilation exchanges all the air
    # of the room (when switched on)
    air_exch: _VectorisedFloat

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        # No dependence on the room volume.
        # If off, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.
        # Reminder, no dependence on time in the resulting calculation.
        return self.air_exch


@dataclass(frozen=True)
class Virus:
    #: RNA copies  / mL
    viral_load_in_sputum: _VectorisedFloat

    #: Dose to initiate infection, in RNA copies
    infectious_dose: _VectorisedFloat

    #: viable-to-RNA virus ratio as a function of the viral load
    viable_to_RNA_ratio: _VectorisedFloat

    #: Reported increase of transmissibility of a VOC
    transmissibility_factor: float

    #: Pre-populated examples of Viruses.
    types: typing.ClassVar[typing.Dict[str, "Virus"]]

    def halflife(self, humidity: _VectorisedFloat) -> _VectorisedFloat:
        # Biological decay (inactivation of the virus in air) - virus 
        # dependent and function of humidity
        raise NotImplementedError

    def decay_constant(self, humidity: _VectorisedFloat) -> _VectorisedFloat:
        # Viral inactivation per hour (h^-1) (function of humidity)
        return np.log(2) / self.halflife(humidity)


@dataclass(frozen=True)
class SARSCoV2(Virus):

    def halflife(self, humidity: _VectorisedFloat) -> _VectorisedFloat:
        """
        Half-life changes with humidity level. Here is implemented a simple
        piecewise constant model (for more details see A. Henriques et al,
        CERN-OPEN-2021-004, DOI: 10.17181/CERN.1GDQ.5Y75)
        """
        # Taken from Morris et al (https://doi.org/10.7554/eLife.65902) data at T = 22°C and RH = 40 %,
        # and from Doremalen et al (https://www.nejm.org/doi/10.1056/NEJMc2004973).
        return np.piecewise(humidity, [humidity <= 0.4, humidity > 0.4], [6.43, 1.1])
        

Virus.types = {
    'SARS_CoV_2': SARSCoV2(
        viral_load_in_sputum=1e9,
        # No data on coefficient for SARS-CoV-2 yet.
        # It is somewhere between 1000 or 10 SARS-CoV viruses, 
        # as per https://www.dhs.gov/publication/st-master-question-list-covid-19
        # 50 comes from Buonanno et al.
        infectious_dose=50.,
        viable_to_RNA_ratio = 0.5,
        transmissibility_factor=1.0,
    ),
    'SARS_CoV_2_ALPHA': SARSCoV2(
        # also called VOC-202012/01
        viral_load_in_sputum=1e9,
        infectious_dose=50.,
        viable_to_RNA_ratio = 0.5,
        transmissibility_factor=0.78,
    ),
    'SARS_CoV_2_BETA': SARSCoV2(
        viral_load_in_sputum=1e9,
        infectious_dose=50.,
        viable_to_RNA_ratio=0.5,
        transmissibility_factor=0.8,
        ),
    'SARS_CoV_2_GAMMA': SARSCoV2(
        viral_load_in_sputum=1e9,
        infectious_dose=50.,
        viable_to_RNA_ratio = 0.5,
        transmissibility_factor=0.72,
    ),
    'SARS_CoV_2_DELTA': SARSCoV2(
        viral_load_in_sputum=1e9,
        infectious_dose=50.,
        viable_to_RNA_ratio = 0.5,
        transmissibility_factor=0.51,
    ),
    'SARS_CoV_2_OMICRON': SARSCoV2(
        viral_load_in_sputum=1e9,
        infectious_dose=20.,
        viable_to_RNA_ratio=0.5,
        transmissibility_factor=0.2
    ),
}


@dataclass(frozen=True)
class Mask:
    #: Filtration efficiency of masks when inhaling.
    η_inhale: _VectorisedFloat

    #: Global factor applied to filtration efficiency of masks when exhaling.
    factor_exhale: float = 1.

    #: Pre-populated examples of Masks.
    types: typing.ClassVar[typing.Dict[str, "Mask"]]

    def exhale_efficiency(self, diameter: _VectorisedFloat) -> _VectorisedFloat:
        """
        Overall exhale efficiency, including the effect of the leaks.
        See CERN-OPEN-2021-004 (doi: 10.17181/CERN.1GDQ.5Y75), and Ref.
        therein (Asadi 2020).
        Obtained from measurements of filtration efficiency and of
        the leakage through the sides.
        Diameter is in microns.
        """
        d = np.array(diameter)
        intermediate_range1 = np.bitwise_and(0.5 <= d, d < 0.94614)
        intermediate_range2 = np.bitwise_and(0.94614 <= d, d < 3.)

        eta_out = np.empty(d.shape, dtype=np.float64)

        eta_out[d < 0.5] = 0.
        eta_out[intermediate_range1] = 0.5893 * d[intermediate_range1] + 0.1546
        eta_out[intermediate_range2] = 0.0509 * d[intermediate_range2] + 0.664
        eta_out[d >= 3.] = 0.8167

        return eta_out*self.factor_exhale

    def inhale_efficiency(self) -> _VectorisedFloat:
        """
        Overall inhale efficiency, including the effect of the leaks.
        """
        return self.η_inhale


Mask.types = {
    'No mask': Mask(0, 0),
    'Type I': Mask(
        η_inhale=0.5,  # (CERN-OPEN-2021-004)
    ),
    'FFP2': Mask(
        η_inhale=0.865,  # (94% penetration efficiency + 8% max inward leakage -> EN 149)
    ),
}


@dataclass(frozen=True)
class Particle:
    """
    Represents an aerosol particle.
    """

    #: diameter of the aerosol in microns
    diameter: typing.Union[None,_VectorisedFloat] = None

    def settling_velocity(self, evaporation_factor: float=0.3) -> _VectorisedFloat:
        """
        Settling velocity (i.e. speed of deposition on the floor due
        to gravity), for aerosols, in m/s. Diameter-dependent expression
        from https://doi.org/10.1101/2021.10.14.21264988
        When an aerosol-diameter is not given, returns
        the default value of 1.88e-4 m/s (corresponds to diameter of
        2.5 microns, i.e. geometric average of the breathing
        expiration distribution, taking evaporation into account, see
        https://doi.org/10.1101/2021.10.14.21264988)
        evaporation_factor represents the factor applied to the diameter,
        due to instantaneous evaporation of the particle in the air.
        """
        if self.diameter is None:
            vg = 1.88e-4
        else:
            vg = 1.88e-4 * (self.diameter*evaporation_factor / 2.5)**2
        return vg

    def fraction_deposited(self, evaporation_factor: float=0.3) -> _VectorisedFloat:
        """
        The fraction of particles actually deposited in the respiratory
        tract (over the total number of particles). It depends on the
        particle diameter.
        From W. C. Hinds, New York, Wiley, 1999 (pp. 233 – 259).
        evaporation_factor represents the factor applied to the diameter,
        due to instantaneous evaporation of the particle in the air.
        """
        if self.diameter is None:
            # model is not evaluated for specific values of aerosol
            # diameters - we choose a single "average" deposition factor,
            # as in https://doi.org/10.1101/2021.10.14.21264988.
            fdep = 0.6
        else:
            # deposition fraction depends on aerosol particle diameter.
            d = (self.diameter * evaporation_factor)
            IFrac = 1 - 0.5 * (1 - (1 / (1 + (0.00076*(d**2.8)))))
            fdep = IFrac * (0.0587
                    + (0.911/(1 + np.exp(4.77 + 1.485 * np.log(d))))
                    + (0.943/(1 + np.exp(0.508 - 2.58 * np.log(d)))))
        return fdep


@dataclass(frozen=True)
class _ExpirationBase:
    """
    Represents the expiration of aerosols by a person.
    Subclasses of _ExpirationBase represent different models.
    """
    #: Pre-populated examples of Expirations.
    types: typing.ClassVar[typing.Dict[str, "_ExpirationBase"]]

    @property
    def particle(self) -> Particle:
        """
        the Particle object representing the aerosol - here the default one
        """
        return Particle()

    def aerosols(self, mask: Mask):
        """
        total volume of aerosols expired per volume of air (mL/cm^3).
        """
        raise NotImplementedError("Subclass must implement")


@dataclass(frozen=True)
class Expiration(_ExpirationBase):
    """
    Model for the expiration. For a given diameter of aerosol, provides
    the aerosol volume, weighted by the mask outward efficiency when
    applicable.
    """
    #: diameter of the aerosol in microns
    diameter: _VectorisedFloat

    #: total concentration of aerosols per unit volume of expired air
    # (in cm^-3), integrated over all aerosol diameters (corresponding
    # to c_n,i in Eq. (4) of https://doi.org/10.1101/2021.10.14.21264988)
    cn: float = 1.

    @property
    def particle(self) -> Particle:
        """
        the Particle object representing the aerosol
        """
        return Particle(diameter=self.diameter)

    @cached()
    def aerosols(self, mask: Mask):
        """ Result is in mL.cm^-3 """
        def volume(d):
            return (np.pi * d**3) / 6.

        # final result converted from microns^3/cm3 to mL/cm^3
        return self.cn * (volume(self.diameter) *
                (1 - mask.exhale_efficiency(self.diameter))) * 1e-12


@dataclass(frozen=True)
class MultipleExpiration(_ExpirationBase):
    """
    Represents an expiration of aerosols.
    Group together different modes of expiration, that represent
    each the main expiration mode for a certain fraction of time (given by
    the weights).
    This class can only be used with single diameters defined in each
    expiration (it cannot be used with diameter distributions).
    """
    expirations: typing.Tuple[_ExpirationBase, ...]
    weights: typing.Tuple[float, ...]

    def __post_init__(self):
        if len(self.expirations) != len(self.weights):
            raise ValueError("expirations and weigths must contain the"
                             "same number of elements")
        if not all(np.isscalar(e.diameter) for e in self.expirations):
            raise ValueError("diameters must all be scalars")

    def aerosols(self, mask: Mask):
        return np.array([
            weight * expiration.aerosols(mask) / sum(self.weights)
            for weight,expiration in zip(self.weights,self.expirations)
        ]).sum(axis=0)


# Typical expirations. The aerosol diameter given is an equivalent
# diameter, chosen in such a way that the aerosol volume is
# the same as the total aerosol volume given by the full BLO model
# (integrated between 0.1 and 30 microns)
# The correspondence with the BLO coefficients is given.
_ExpirationBase.types = {
    'Breathing': Expiration(1.3844), # corresponds to B/L/O coefficients of (1, 0, 0)
    'Speaking': Expiration(5.8925),   # corresponds to B/L/O coefficients of (1, 1, 1)
    'Shouting': Expiration(10.0411), # corresponds to B/L/O coefficients of (1, 5, 5)
    'Singing': Expiration(10.0411),  # corresponds to B/L/O coefficients of (1, 5, 5)
}


@dataclass(frozen=True)
class Activity:
    #: Inhalation rate in m^3/h
    inhalation_rate: _VectorisedFloat

    #: Exhalation rate in m^3/h
    exhalation_rate: _VectorisedFloat

    #: Pre-populated examples of activities.
    types: typing.ClassVar[typing.Dict[str, "Activity"]]


Activity.types = {
    'Seated': Activity(0.51, 0.51),
    'Standing': Activity(0.57, 0.57),
    'Light activity': Activity(1.25, 1.25),
    'Moderate activity': Activity(1.78, 1.78),
    'Heavy exercise': Activity(3.30, 3.30),
}


@dataclass(frozen=True)
class Population:
    """
    Represents a group of people all with exactly the same behaviour and
    situation.

    """
    #: How many in the population.
    number: int

    #: The times in which the people are in the room.
    presence: Interval

    #: The kind of mask being worn by the people.
    mask: Mask

    #: The physical activity being carried out by the people.
    activity: Activity

    #: The ratio of virions that are inactivated by the person's immunity.
    # This parameter considers the potential antibodies in the person, 
    # which might render inactive some RNA copies (virions).
    host_immunity: float

    def person_present(self, time):
        return self.presence.triggered(time)


@dataclass(frozen=True)
class _PopulationWithVirus(Population):
    #: The virus with which the population is infected.
    virus: Virus

    @method_cache
    def fraction_of_infectious_virus(self) -> _VectorisedFloat:
        """
        The fraction of infectious virus.

        """
        return 1.

    def aerosols(self):
        """
        total volume of aerosols expired per volume of air (mL/cm^3).
        """
        raise NotImplementedError("Subclass must implement")

    def emission_rate_per_aerosol_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of virions per fraction of aerosol volume in
        the expired air, if the infected population is present, in cm^3/(mL.h).
        It should not be a function of time.
        """
        raise NotImplementedError("Subclass must implement")

    @method_cache
    def emission_rate_when_present(self) -> _VectorisedFloat:
        """
        The emission rate if the infected population is present
        (in virions / h).
        """
        return (self.emission_rate_per_aerosol_when_present() *
                self.aerosols())

    def emission_rate(self, time) -> _VectorisedFloat:
        """
        The emission rate of the population vs time.
        """
        # Note: The original model avoids time dependence on the emission rate
        # at the cost of implementing a piecewise (on time) concentration function.

        if not self.person_present(time):
            return 0.

        # Note: It is essential that the value of the emission rate is not
        # itself a function of time. Any change in rate must be accompanied
        # with a declaration of state change time, as is the case for things
        # like Ventilation.

        return self.emission_rate_when_present()

    @property
    def particle(self) -> Particle:
        """
        the Particle object representing the aerosol expired by the
        population - here we take the default Particle object
        """
        return Particle()


@dataclass(frozen=True)
class EmittingPopulation(_PopulationWithVirus):
    #: The emission rate of a single individual, in virions / h.
    known_individual_emission_rate: float

    def aerosols(self):
        """
        total volume of aerosols expired per volume of air (mL/cm^3).
        Here arbitrarily set to 1 as the full emission rate is known.
        """
        return 1.

    @method_cache
    def emission_rate_per_aerosol_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of virions per fraction of aerosol volume in
        the expired air, if the infected population is present, in cm^3/(mL.h).
        It should not be a function of time.
        """
        return self.known_individual_emission_rate * self.number


@dataclass(frozen=True)
class InfectedPopulation(_PopulationWithVirus):
    #: The type of expiration that is being emitted whilst doing the activity.
    expiration: _ExpirationBase

    @method_cache
    def fraction_of_infectious_virus(self) -> _VectorisedFloat:
        """
        The fraction of infectious virus.
        """
        return self.virus.viable_to_RNA_ratio * (1 - self.host_immunity)

    def aerosols(self):
        """
        total volume of aerosols expired per volume of air (mL/cm^3).
        """
        return self.expiration.aerosols(self.mask)

    @method_cache
    def emission_rate_per_aerosol_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of virions per fraction of aerosol volume in
        the expired air, if the infected population is present, in cm^3/(mL.h).
        It should not be a function of time.
        """
        # Note on units: exhalation rate is in m^3/h -> 1e6 conversion factor

        ER = (self.virus.viral_load_in_sputum *
              self.activity.exhalation_rate *
              10 ** 6)

        return ER * self.number

    @property
    def particle(self) -> Particle:
        """
        the Particle object representing the aerosol - here the default one
        """
        return self.expiration.particle


@dataclass(frozen=True)
class ConcentrationModel:
    room: Room
    ventilation: _VentilationBase
    infected: _PopulationWithVirus

    #: evaporation factor: the particles' diameter is multiplied by this
    # factor as soon as they are in the air (but AFTER going out of the,
    # mask, if any).
    evaporation_factor: float = 0.3

    @property
    def virus(self):
        return self.infected.virus

    def infectious_virus_removal_rate(self, time: float) -> _VectorisedFloat:
        # Equilibrium velocity of particle motion toward the floor
        vg = self.infected.particle.settling_velocity(self.evaporation_factor)
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h

        return (
            k + self.virus.decay_constant(self.room.humidity)
            + self.ventilation.air_exchange(self.room, time)
        )

    @method_cache
    def _normed_concentration_limit(self, time: float) -> _VectorisedFloat:
        """
        Provides a constant that represents the theoretical asymptotic 
        value reached by the concentration when time goes to infinity,
        if all parameters were to stay time-independent.
        This is normalized by the emission rate, the latter acting as a
        multiplicative constant factor for the concentration model that
        can be put back in front of the concentration after the time
        dependence has been solved for.
        """
        if not self.infected.person_present(time):
            return 0.
        V = self.room.volume
        IVRR = self.infectious_virus_removal_rate(time)

        return 1. / (IVRR * V)

    @method_cache
    def state_change_times(self) -> typing.List[float]:
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.

        """
        state_change_times = {0.}
        state_change_times.update(self.infected.presence.transition_times())
        state_change_times.update(self.ventilation.transition_times())
        return sorted(state_change_times)

    @method_cache
    def _first_presence_time(self) -> float:
        """
        First presence time. Before that, the concentration is zero.

        """
        return self.infected.presence.boundaries()[0][0]

    def last_state_change(self, time: float) -> float:
        """
        Find the most recent/previous state change.

        Find the nearest time less than the given one. If there is a state
        change exactly at ``time`` the previous state change is returned
        (except at ``time == 0``).

        """
        times = self.state_change_times()
        t_index: int = np.searchsorted(times, time)  # type: ignore
        # Search sorted gives us the index to insert the given time. Instead we
        # want to get the index of the most recent time, so reduce the index by
        # one unless we are already at 0.
        t_index = max([t_index - 1, 0])
        return times[t_index]

    def _next_state_change(self, time: float) -> float:
        """
        Find the nearest future state change.

        """
        for change_time in self.state_change_times():
            if change_time >= time:
                return change_time
        raise ValueError(
            f"The requested time ({time}) is greater than last available "
            f"state change time ({change_time})"
        )

    @method_cache
    def _normed_concentration_cached(self, time: float) -> _VectorisedFloat:
        # A cached version of the _normed_concentration method. Use this
        # method if you expect that there may be multiple concentration
        # calculations for the same time (e.g. at state change times).
        return self._normed_concentration(time)

    def _normed_concentration(self, time: float) -> _VectorisedFloat:
        """
        Virus exposure concentration, as a function of time, and
        normalized by the emission rate.
        The formulas used here assume that all parameters (ventilation,
        emission rate) are constant between two state changes - only
        the value of these parameters at the next state change, are used.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        # The model always starts at t=0, but we avoid running concentration calculations
        # before the first presence as an optimisation.
        if time <= self._first_presence_time():
            return 0.0
        next_state_change_time = self._next_state_change(time)
        IVRR = self.infectious_virus_removal_rate(next_state_change_time)
        conc_limit = self._normed_concentration_limit(next_state_change_time)

        t_last_state_change = self.last_state_change(time)
        conc_at_last_state_change = self._normed_concentration_cached(t_last_state_change)

        delta_time = time - t_last_state_change
        fac = np.exp(-IVRR * delta_time)
        return conc_limit * (1 - fac) + conc_at_last_state_change * fac

    def concentration(self, time: float) -> _VectorisedFloat:
        """
        Virus exposure concentration, as a function of time.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        return (self._normed_concentration(time) * 
                self.infected.emission_rate_when_present())

    @method_cache
    def normed_integrated_concentration(self, start: float, stop: float) -> _VectorisedFloat:
        """
        Get the integrated concentration of viruses in the air  between the times start and stop,
        normalized by the emission rate.
        """
        if stop <= self._first_presence_time():
            return 0.0
        state_change_times = self.state_change_times()
        req_start, req_stop = start, stop
        total_normed_concentration = 0.
        for interval_start, interval_stop in zip(state_change_times[:-1], state_change_times[1:]):
            if req_start > interval_stop or req_stop < interval_start:
                continue
            # Clip the current interval to the requested range.
            start = max([interval_start, req_start])
            stop = min([interval_stop, req_stop])

            conc_start = self._normed_concentration_cached(start)

            next_conc_state = self._next_state_change(stop)
            conc_limit = self._normed_concentration_limit(next_conc_state)
            IVRR = self.infectious_virus_removal_rate(next_conc_state)
            delta_time = stop - start
            total_normed_concentration += (
                conc_limit * delta_time +
                (conc_limit - conc_start) * (np.exp(-IVRR*delta_time)-1) / IVRR
            )
        return total_normed_concentration

    def integrated_concentration(self, start: float, stop: float) -> _VectorisedFloat:
        """
        Get the integrated concentration of viruses in the air between the times start and stop.
        """
        return (self.normed_integrated_concentration(start, stop) *
                self.infected.emission_rate_when_present())


@dataclass(frozen=True)
class ExposureModel:
    """
    Represents the exposure to a concentration of virions in the air.
    NOTE: the infection probability formula assumes that if the diameter
    is an array, then none of the ventilation parameters, room volume or virus
    decay constant, are arrays as well.
    TODO: implement a check this is the case, in __post_init__
    """
    #: The virus concentration model which this exposure model should consider.
    concentration_model: ConcentrationModel

    #: The population of non-infected people to be used in the model.
    exposed: Population

    #: Geographic location population
    geographic_population: int = 0

    #: Geographic location cases
    geographic_cases: int = 0

    #: The number of times the exposure event is repeated (default 1).
    repeats: int = 1

    def fraction_deposited(self) -> _VectorisedFloat:
        """
        The fraction of particles actually deposited in the respiratory
        tract (over the total number of particles). It depends on the
        particle diameter.
        """
        return self.concentration_model.infected.particle.fraction_deposited(
                    self.concentration_model.evaporation_factor)

    def _normed_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        """The number of virions per meter^3 between any two times, normalized 
        by the emission rate of the infected population"""
        exposure = 0.
        for start, stop in self.exposed.presence.boundaries():
            if stop < time1:
                continue
            elif start > time2:
                break
            elif start <= time1 and time2<= stop:
                exposure += self.concentration_model.normed_integrated_concentration(time1, time2)
            elif start <= time1 and stop < time2:
                exposure += self.concentration_model.normed_integrated_concentration(time1, stop)
            elif time1 < start and time2 <= stop:
                exposure += self.concentration_model.normed_integrated_concentration(start, time2)
            elif time1 <= start and stop < time2:
                exposure += self.concentration_model.normed_integrated_concentration(start, stop)
        return exposure
            
    def _normed_exposure(self) -> _VectorisedFloat:
        """
        The number of virions per meter^3, normalized by the emission rate
        of the infected population.
        """
        normed_exposure = 0.0

        for start, stop in self.exposed.presence.boundaries():
            normed_exposure += self.concentration_model.normed_integrated_concentration(start, stop)

        return normed_exposure * self.repeats

    def deposited_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract
        between any two times.
        """
        emission_rate_per_aerosol = self.concentration_model.infected.emission_rate_per_aerosol_when_present()
        aerosols = self.concentration_model.infected.aerosols()
        fdep = self.fraction_deposited()
        f_inf = self.concentration_model.infected.fraction_of_infectious_virus()

        diameter = self.concentration_model.infected.particle.diameter

        if not np.isscalar(diameter) and diameter is not None:
            # we compute first the mean of all diameter-dependent quantities
            # to perform properly the Monte-Carlo integration over
            # particle diameters (doing things in another order would
            # lead to wrong results).
            dep_exposure_integrated = np.array(self._normed_exposure_between_bounds(time1, time2) *
                                               aerosols *
                                               fdep).mean()
        else:
            # in the case of a single diameter or no diameter defined,
            # one should not take any mean at this stage.
            dep_exposure_integrated = self._normed_exposure_between_bounds(time1, time2)*aerosols*fdep

        # then we multiply by the diameter-independent quantity emission_rate_per_aerosol,
        # and parameters of the vD equation (i.e. f_inf, BR_k and n_in).
        return (dep_exposure_integrated * emission_rate_per_aerosol * 
                f_inf * self.exposed.activity.inhalation_rate * 
                (1 - self.exposed.mask.inhale_efficiency()))
                
    def probability_random_individual(self, cases, population, AB) -> _VectorisedFloat:
        """Probability that a randomly selected individual in a focal population is infected."""
        return cases*AB/population

    def probability_meet_infected_person(self, population, cases, event, x) -> _VectorisedFloat:
        """Probability to meet x infected persons in an event."""
        
        # Ascertainment bias
        AB = 5
        return sct.binom.pmf(x, event, self.probability_random_individual(cases, population, AB))

    def deposited_exposure(self) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract.
        """
        deposited_exposure = 0.0

        for start, stop in self.exposed.presence.boundaries():
            deposited_exposure += self.deposited_exposure_between_bounds(start, stop)

        return deposited_exposure * self.repeats

    def infection_probability(self) -> _VectorisedFloat:
        # viral dose (vD)
        vD = self.deposited_exposure()
        
        # oneoverln2 multiplied by ID_50 corresponds to ID_63.
        infectious_dose = oneoverln2 * self.concentration_model.virus.infectious_dose

        # Probability of infection.        
        return (1 - np.exp(-((vD * (1 - self.exposed.host_immunity))/(infectious_dose * 
                self.concentration_model.virus.transmissibility_factor)))) * 100

    def total_probability_rule(self) -> _VectorisedFloat:
        if (self.geographic_population != 0 and self.geographic_cases != 0): 
            sum_probability = 0.0
            # Create an equivalent exposure model but with i infected cases
            total_people = self.concentration_model.infected.number + self.exposed.number
            X = (total_people if total_people < 10 else 10)
            for x in range(1, X):
                exposure_model = nested_replace(
                    self, {'concentration_model.infected.number': x}
                )
                prob_exposed_occupant = exposure_model.infection_probability().mean() / 100
                # By means of a Binomial Distribution
                sum_probability += (prob_exposed_occupant)*self.probability_meet_infected_person(self.geographic_population, self.geographic_cases, self.exposed.number, x)
            return sum_probability * 100
        else:
            return 0

    def expected_new_cases(self) -> _VectorisedFloat:
        prob = self.infection_probability()
        exposed_occupants = self.exposed.number
        return prob * exposed_occupants / 100

    def reproduction_number(self) -> _VectorisedFloat:
        """
        The reproduction number can be thought of as the expected number of
        cases directly generated by one infected case in a population.

        """
        if self.concentration_model.infected.number == 1:
            return self.expected_new_cases()

        # Create an equivalent exposure model but with precisely
        # one infected case.
        single_exposure_model = nested_replace(
            self, {'concentration_model.infected.number': 1}
        )

        return single_exposure_model.expected_new_cases()
