# This module is part of CAiMIRA. Please see the repository at
# https://gitlab.cern.ch/caimira/caimira for details of the license and terms of use.
"""
This module implements the core CAiMIRA models.

The CAiMIRA model is a flexible, object-oriented numerical model. It is designed
to allow the user to swap-out and extend its various components. One of the
major abstractions of the model is the distinction between virus concentration
(:class:`ConcentrationModel`) and virus exposure (:class:`ExposureModel`).

The concentration component is a recursive (on model time) model and therefore in order
to optimise its execution certain layers of caching are implemented. This caching
mandates that the models in this module, once instantiated, are immutable and
deterministic (i.e. running the same model twice will result in the same answer).

In order to apply stochastic / non-deterministic analyses therefore you must
introduce the randomness before constructing the models themselves; the
:mod:`caimira.monte_carlo` module is a good example of doing this - that module uses
the models defined here to allow you to construct a ConcentrationModel containing
parameters which are expressed as probability distributions. Under the hood the
``caimira.monte_carlo.ConcentrationModel`` implementation simply samples all of those
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
import scipy.stats as sct
from scipy.optimize import minimize

from caimira.calculator.store.data_registry import DataRegistry

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

    # TODO: Implement rather a periodic version (24-hour period), where
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
        # Build an Interval object
        present_times = []
        for t1, t2, value in zip(self.transition_times[:-1],
                                 self.transition_times[1:], self.values):
            if value:
                present_times.append((t1, t2))
        return SpecificInterval(present_times=tuple(present_times))

    def refine(self, refine_factor=10) -> "PiecewiseConstant":
        # Build a new PiecewiseConstant object with a refined mesh,
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
class IntPiecewiseConstant(PiecewiseConstant):

    #: values of the function between transitions
    values: typing.Tuple[int, ...]

    def value(self, time) -> _VectorisedFloat:
        if time <= self.transition_times[0] or time > self.transition_times[-1]:
            return 0

        for t1, t2, value in zip(self.transition_times[:-1],
                                 self.transition_times[1:], self.values):
            if t1 < time <= t2:
                break
        return value


@dataclass(frozen=True)
class Room:
    #: The total volume of the room
    volume: _VectorisedFloat

    #: The temperature inside the room (Kelvin).
    inside_temp: PiecewiseConstant = PiecewiseConstant((0, 24), (293,))

    #: The humidity in the room (from 0 to 1 - e.g. 0.5 is 50% humidity)
    humidity: _VectorisedFloat = 0.5

    #: The maximum occupation of the room - design limit
    capacity: typing.Optional[int] = None


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
    def transition_times(self, room: Room) -> typing.Set[float]:
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

    def transition_times(self, room: Room) -> typing.Set[float]:
        return self.active.transition_times()


@dataclass(frozen=True)
class MultipleVentilation(_VentilationBase):
    """
    Represents a mechanism by which air can be exchanged (replaced/filtered)
    in a time dependent manner.

    Group together different sources of ventilations.

    """
    ventilations: typing.Tuple[_VentilationBase, ...]

    def transition_times(self, room: Room) -> typing.Set[float]:
        transitions = set()
        for ventilation in self.ventilations:
            transitions.update(ventilation.transition_times(room))
        return transitions

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        """
        Returns the rate at which air is being exchanged in the given room
        at a given time (in hours).
        """
        return np.array([
            ventilation.air_exchange(room, time)
            for ventilation in self.ventilations
        ], dtype=object).sum(axis=0)


@dataclass(frozen=True)
class WindowOpening(Ventilation):
    #: The interval in which the window is open.
    active: Interval

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

    def transition_times(self, room: Room) -> typing.Set[float]:
        transitions = super().transition_times(room)
        transitions.update(room.inside_temp.transition_times)
        transitions.update(self.outside_temp.transition_times)
        return transitions

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        # If the window is shut, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.

        # Reminder, no dependence on time in the resulting calculation.
        inside_temp: _VectorisedFloat = room.inside_temp.value(time)
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
    data_registry: DataRegistry = DataRegistry()

    @property
    def discharge_coefficient(self) -> _VectorisedFloat:
        """
        Average measured value of discharge coefficient for sliding or
        side-hung windows.
        """
        return self.data_registry.ventilation['natural']['discharge_factor']['sliding'] # type: ignore


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
class CustomVentilation(_VentilationBase):
    # The ventilation value for a given time
    ventilation_value: PiecewiseConstant

    def transition_times(self, room: Room) -> typing.Set[float]:
        return set(self.ventilation_value.transition_times)

    def air_exchange(self, room: Room, time: float) -> _VectorisedFloat:
        return self.ventilation_value.value(time)


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

    #: Number of days the infector is contagious
    infectiousness_days: int

    def halflife(self, humidity: _VectorisedFloat, inside_temp: _VectorisedFloat) -> _VectorisedFloat:
        # Biological decay (inactivation of the virus in air) - virus
        # dependent and function of humidity
        raise NotImplementedError

    def decay_constant(self, humidity: _VectorisedFloat, inside_temp: _VectorisedFloat) -> _VectorisedFloat:
        # Viral inactivation per hour (h^-1) (function of humidity and inside temperature)
        return np.log(2) / self.halflife(humidity, inside_temp)


@dataclass(frozen=True)
class SARSCoV2(Virus):
    #: Number of days the infector is contagious
    infectiousness_days: int = 14

    def halflife(self, humidity: _VectorisedFloat, inside_temp: _VectorisedFloat) -> _VectorisedFloat:
        """
        Half-life changes with humidity level. Here is implemented a simple
        piecewise constant model (for more details see A. Henriques et al,
        CERN-OPEN-2021-004, DOI: 10.17181/CERN.1GDQ.5Y75)
        """
        # Updated to use the formula from Dabish et al. with correction https://doi.org/10.1080/02786826.2020.1829536
        # with a maximum at hl = 6.43 (compensate for the negative decay values in the paper).
        # Note that humidity is in percentage and inside_temp in °C.
        # factor np.log(2) -> decay rate to half-life; factor 60 -> minutes to hours
        hl_calc = ((np.log(2)/((0.16030 + 0.04018*(((inside_temp-273.15)-20.615)/10.585)
                                       +0.02176*(((humidity*100)-45.235)/28.665)
                                       -0.14369
                                       -0.02636*((inside_temp-273.15)-20.615)/10.585)))/60)

        return np.where(hl_calc <= 0, 6.43, np.minimum(6.43, hl_calc))


# Example of Viruses only used for the Expert app and tests.
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
        # Also called VOC-202012/01
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
        infectious_dose=50.,
        viable_to_RNA_ratio=0.5,
        transmissibility_factor=0.2
    ),
}


@dataclass(frozen=True)
class Mask:
    #: Filtration efficiency of masks when inhaling.
    η_inhale: _VectorisedFloat

    #: Filtration efficiency of masks when exhaling.
    η_exhale: typing.Union[None, _VectorisedFloat] = None

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
        if self.η_exhale is not None:
            # When η_exhale is specified, return it directly
            return self.η_exhale

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


# Example of Masks only used for the Expert app and tests.
Mask.types = {
    'No mask': Mask(0, 0),
    'Type I': Mask(
        η_inhale=0.5,  # (CERN-OPEN-2021-004)
    ),
    'FFP2': Mask(
        η_inhale=0.865,  # (94% penetration efficiency + 8% max inward leakage -> EN 149)
    ),
    'Cloth': Mask(  # https://doi.org/10.1080/02786826.2021.1890687
        η_inhale=0.225,
        η_exhale=0.35,
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
            return 1.88e-4
        else:
            return 1.88e-4 * (self.diameter*evaporation_factor / 2.5)**2

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
                    + (0.943/(1 + np.exp(0.508 - 2.58 * np.log(d))))) # type: ignore
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
        The Particle object representing the aerosol - here the default one
        """
        return Particle()

    def aerosols(self, mask: Mask):
        """
        Total volume of aerosols expired per volume of exhaled air 
        considering the outward mask efficiency (mL/cm^3).
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

    #: Total concentration of aerosols per unit volume of expired air
    # (in cm^-3), integrated over all aerosol diameters (corresponding
    # to c_n,i in Eq. (4) of https://doi.org/10.1101/2021.10.14.21264988)
    cn: float = 1.

    @property
    def particle(self) -> Particle:
        """
        The Particle object representing the aerosol
        """
        return Particle(diameter=self.diameter)

    @cached()
    def aerosols(self, mask: Mask):
        """
        Total volume of aerosols expired per volume 
        of exhaled air considering the outward mask 
        efficiency. Result is in mL.cm^-3.
        """
        def volume(d):
            return (np.pi * d**3) / 6.

        # Final result converted from microns^3/cm3 to mL/cm^3
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
# Only used for the Expert app and tests.
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

    #: Pre-populated examples of Activities.
    types: typing.ClassVar[typing.Dict[str, "Activity"]]


# Example of Activities only used for the Expert app and tests.
Activity.types = {
    'Seated': Activity(0.51, 0.51),
    'Standing': Activity(0.57, 0.57),
    'Light activity': Activity(1.25, 1.25),
    'Moderate activity': Activity(1.78, 1.78),
    'Heavy exercise': Activity(3.30, 3.30),
}


@dataclass(frozen=True)
class SimplePopulation:
    """
    Represents a group of people all with exactly the same behaviour and
    situation.

    """
    #: How many in the population.
    number: typing.Union[int, IntPiecewiseConstant]

    #: The times in which the people are in the room.
    presence: typing.Optional[Interval]

    #: The physical activity being carried out by the people.
    activity: Activity

    def __post_init__(self):
        if isinstance(self.number, int):
            if not isinstance(self.presence, Interval):
                raise TypeError(f'The presence argument must be an "Interval". Got {type(self.presence)}')
        else:
            if self.presence is not None:
                raise TypeError(f'The presence argument must be None for a IntPiecewiseConstant number')

    def presence_interval(self):
        if isinstance(self.presence, Interval):
            return self.presence
        elif isinstance(self.number, IntPiecewiseConstant):
            return self.number.interval()

    def person_present(self, time: float):
        # Allow back-compatibility
        if isinstance(self.number, int) and isinstance(self.presence, Interval):
            return self.presence.triggered(time)
        elif isinstance(self.number, IntPiecewiseConstant):
            return self.number.value(time) != 0

    def people_present(self, time: float):
        # Allow back-compatibility
        if isinstance(self.number, int):
            return self.number * self.person_present(time)
        else:
            return int(self.number.value(time))


@dataclass(frozen=True)
class Population(SimplePopulation):
    """
    Represents a group of people all with exactly the same behaviour and
    situation, considering the usage of mask and a certain host immunity.

    """
    #: The kind of mask being worn by the people.
    mask: Mask

    #: The ratio of virions that are inactivated by the person's immunity.
    # This parameter considers the potential antibodies in the person,
    # which might render inactive some RNA copies (virions).
    host_immunity: float


@dataclass(frozen=True)
class _PopulationWithVirus(Population):
    data_registry: DataRegistry

    #: The virus with which the population is infected.
    virus: Virus

    @method_cache
    def fraction_of_infectious_virus(self) -> _VectorisedFloat:
        """
        The fraction of infectious virus.

        """
        return 1

    def aerosols(self):
        """
        Total volume of aerosols expired per volume of exhaled air (mL/cm^3).
        """
        raise NotImplementedError("Subclass must implement")

    def emission_rate_per_aerosol_per_person_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of infectious respiratory particles (IRP) in the expired air per 
        mL of respiratory fluid, if the infected population is present, in (virions.cm^3)/(mL.h).
        This method returns only the diameter-independent variables within the emission rate.
        It should not be a function of time.
        """
        raise NotImplementedError("Subclass must implement")

    @method_cache
    def emission_rate_per_person_when_present(self) -> _VectorisedFloat:
        """
        The emission rate if the infected population is present, per person
        (in virions/h).
        """
        return (self.emission_rate_per_aerosol_per_person_when_present() *
                self.aerosols())

    def emission_rate(self, time: float) -> _VectorisedFloat:
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
        return self.emission_rate_per_person_when_present() * self.people_present(time)

    @property
    def particle(self) -> Particle:
        """
        The Particle object representing the aerosol expired by the
        population - here we take the default Particle object
        """
        return Particle()


@dataclass(frozen=True)
class EmittingPopulation(_PopulationWithVirus):
    #: The emission rate of a single individual, in virions / h.
    known_individual_emission_rate: float

    def aerosols(self):
        """
        Total volume of aerosols expired per volume of exhaled air (mL/cm^3).
        Here arbitrarily set to 1 as the full emission rate is known.
        """
        return 1.

    @method_cache
    def emission_rate_per_aerosol_per_person_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of infectious respiratory particles (IRP) in the expired air per 
        mL of respiratory fluid, if the infected population is present, in (virions.cm^3)/(mL.h).
        This method returns only the diameter-independent variables within the emission rate.
        It should not be a function of time.
        """
        return self.known_individual_emission_rate
    

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
        Total volume of aerosols expired per volume of exhaled air (mL/cm^3).
        """
        return self.expiration.aerosols(self.mask)

    @method_cache
    def emission_rate_per_aerosol_per_person_when_present(self) -> _VectorisedFloat:
        """
        The emission rate of infectious respiratory particles (IRP) in the expired air per 
        mL of respiratory fluid, if the infected population is present, in (virions.cm^3)/(mL.h).
        This method returns only the diameter-independent variables within the emission rate.
        It should not be a function of time.
        """
        # Conversion factor explanation:
        # The exhalation rate is in m^3/h, therefore the 1e6 conversion factor
        # is to convert m^3/h into cm^3/h to return (virions.cm^3)/(mL.h),
        # so that we can then multiply by aerosols (mL/cm^3).
        ER = (self.virus.viral_load_in_sputum *
              self.activity.exhalation_rate *
              self.fraction_of_infectious_virus() *
              10**6)
        return ER

    @property
    def particle(self) -> Particle:
        """
        The Particle object representing the aerosol - here the default one
        """
        return self.expiration.particle


@dataclass(frozen=True)
class Cases:
    """
    The geographical data to calculate the probability of having at least 1
    new infection in a probabilistic exposure.
    """
    #: Geographic location population
    geographic_population: int = 0

    #: Geographic location new cases
    geographic_cases: int = 0

    #: Number of new cases confidence level
    ascertainment_bias: int = 0

    def probability_random_individual(self, virus: Virus) -> _VectorisedFloat:
        """Probability that a randomly selected individual in a focal population is infected."""
        return self.geographic_cases*virus.infectiousness_days*self.ascertainment_bias/self.geographic_population

    def probability_meet_infected_person(self, virus: Virus, n_infected: int, event_population: int) -> _VectorisedFloat:
        """
        Probability to meet n_infected persons in an event.
        From https://doi.org/10.1038/s41562-020-01000-9.
        """
        return sct.binom.pmf(n_infected, event_population, self.probability_random_individual(virus))


@dataclass(frozen=True)
class _ConcentrationModelBase:
    """
    A generic superclass that contains the methods to calculate the
    concentration (e.g. viral concentration or CO2 concentration).
    """
    data_registry: DataRegistry
    room: Room
    ventilation: _VentilationBase

    @property
    def population(self) -> SimplePopulation:
        """
        Population in the room (the emitters of what we compute the
        concentration of)
        """
        raise NotImplementedError("Subclass must implement")

    def removal_rate(self, time: float) -> _VectorisedFloat:
        """
        Remove rate of the species considered, in h^-1
        """
        raise NotImplementedError("Subclass must implement")

    def min_background_concentration(self) -> _VectorisedFloat:
        """
        Minimum background concentration in the room for a given scenario
        (in the same unit as the concentration). Its the value towards which
        the concentration will decay to.
        """
        return self.data_registry.concentration_model['virus_concentration_model']['min_background_concentration'] # type: ignore

    def normalization_factor(self) -> _VectorisedFloat:
        """
        Normalization factor (in the same unit as the concentration).
        This factor is applied to the normalized concentration only
        at the very end.
        """
        raise NotImplementedError("Subclass must implement")

    @method_cache
    def _normed_concentration_limit(self, time: float) -> _VectorisedFloat:
        """
        Provides a constant that represents the theoretical asymptotic
        value reached by the concentration when time goes to infinity,
        if all parameters were to stay time-independent.
        This is normalized by the normalization factor, the latter acting as a
        multiplicative constant factor for the concentration model that
        can be put back in front of the concentration after the time
        dependence has been solved for.
        """
        V = self.room.volume
        RR = self.removal_rate(time)

        if isinstance(RR, np.ndarray):
            invRR = np.empty(RR.shape, dtype=np.float64)
            invRR[RR == 0.] = np.nan
            invRR[RR != 0.] = 1. / RR[RR != 0.]
        else:
            invRR = np.nan if RR == 0. else 1. / RR # type: ignore

        return (self.population.people_present(time) * invRR / V +
                self.min_background_concentration()/self.normalization_factor())

    @method_cache
    def state_change_times(self) -> typing.List[float]:
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.
        """
        state_change_times = {0.}
        state_change_times.update(self.population.presence_interval().transition_times())
        state_change_times.update(self.ventilation.transition_times(self.room))
        return sorted(state_change_times)

    @method_cache
    def _first_presence_time(self) -> float:
        """
        First presence time. Before that, the concentration is zero.
        """
        return self.population.presence_interval().boundaries()[0][0]

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
        """
        A cached version of the _normed_concentration method. Use this
        method if you expect that there may be multiple concentration
        calculations for the same time (e.g. at state change times).
        """
        return self._normed_concentration(time)

    def _normed_concentration(self, time: float) -> _VectorisedFloat:
        """
        Concentration as a function of time, and normalized by
        normalization_factor.
        The formulas used here assume that all parameters (ventilation,
        emission rate) are constant between two state changes - only
        the value of these parameters at the next state change, are used.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        # The model always starts at t=0, but we avoid running concentration calculations
        # before the first presence as an optimisation.
        if time <= self._first_presence_time():
            return self.min_background_concentration()/self.normalization_factor()

        next_state_change_time = self._next_state_change(time)
        RR = self.removal_rate(next_state_change_time)

        t_last_state_change = self.last_state_change(time)
        conc_at_last_state_change = self._normed_concentration_cached(t_last_state_change)
        delta_time = time - t_last_state_change

        fac = np.exp(-RR * delta_time)
        if isinstance(RR, np.ndarray):
            curr_conc_state = np.empty(RR.shape, dtype=np.float64)
            curr_conc_state[RR == 0.] = delta_time * self.population.people_present(time) / (
                self.room.volume[RR == 0.] if isinstance(self.room.volume,np.ndarray) else self.room.volume)
            curr_conc_state[RR != 0.] = self._normed_concentration_limit(next_state_change_time)[RR != 0.] * (1 - fac[RR != 0.])
        else:
            if RR == 0.:
                curr_conc_state = delta_time * self.population.people_present(time) / self.room.volume
            else:
                curr_conc_state = self._normed_concentration_limit(next_state_change_time) * (1 - fac)

        return curr_conc_state + conc_at_last_state_change * fac

    def concentration(self, time: float) -> _VectorisedFloat:
        """
        Total concentration as a function of time. The normalization
        factor has been put back.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        return (self._normed_concentration_cached(time) *
                self.normalization_factor())

    @method_cache
    def normed_integrated_concentration(self, start: float, stop: float) -> _VectorisedFloat:
        """
        Get the integrated concentration between the times start and stop,
        normalized by normalization_factor.
        """
        if stop <= self._first_presence_time():
            return (stop - start)*self.min_background_concentration()/self.normalization_factor()
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
            RR = self.removal_rate(next_conc_state)
            delta_time = stop - start
            total_normed_concentration += (
                conc_limit * delta_time +
                (conc_limit - conc_start) * (np.exp(-RR*delta_time)-1) / RR
            )
        return total_normed_concentration

    def integrated_concentration(self, start: float, stop: float) -> _VectorisedFloat:
        """
        Get the integrated concentration of viruses in the air between the times start and stop.
        """
        return (self.normed_integrated_concentration(start, stop) *
                self.normalization_factor())


@dataclass(frozen=True)
class ConcentrationModel(_ConcentrationModelBase):
    """
    Class used for the computation of the long-range virus concentration.
    """
    #: Infected population in the room, emitting virions
    infected: InfectedPopulation

    #: evaporation factor: the particles' diameter is multiplied by this
    # factor as soon as they are in the air (but AFTER going out of the,
    # mask, if any).
    evaporation_factor: float

    def __post_init__(self):
        if self.evaporation_factor is None:
            self.evaporation_factor = self.data_registry.expiration_particle['particle']['evaporation_factor']

    @property
    def population(self) -> InfectedPopulation:
        return self.infected

    @property
    def virus(self) -> Virus:
        return self.infected.virus

    def normalization_factor(self) -> _VectorisedFloat:
        # we normalize by the emission rate
        return self.infected.emission_rate_per_person_when_present()

    def removal_rate(self, time: float) -> _VectorisedFloat:
        # Equilibrium velocity of particle motion toward the floor
        vg = self.infected.particle.settling_velocity(self.evaporation_factor)
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h
        return (
            k + self.virus.decay_constant(self.room.humidity, self.room.inside_temp.value(time))
            + self.ventilation.air_exchange(self.room, time)
        )

    def infectious_virus_removal_rate(self, time: float) -> _VectorisedFloat:
        # defined for back-compatibility purposes
        return self.removal_rate(time)


@dataclass(frozen=True)
class CO2ConcentrationModel(_ConcentrationModelBase):
    """
    Class used for the computation of the CO2 concentration.
    """
    #: Population in the room emitting CO2
    CO2_emitters: SimplePopulation

    #: CO2 concentration in the atmosphere (in ppm)
    @property
    def CO2_atmosphere_concentration(self) -> float:
        return self.data_registry.concentration_model['CO2_concentration_model']['CO2_atmosphere_concentration'] # type: ignore

    #: CO2 fraction in the exhaled air
    @property
    def CO2_fraction_exhaled(self) -> float:
        return self.data_registry.concentration_model['CO2_concentration_model']['CO2_fraction_exhaled'] # type: ignore

    @property
    def population(self) -> SimplePopulation:
        return self.CO2_emitters

    def removal_rate(self, time: float) -> _VectorisedFloat:
        return self.ventilation.air_exchange(self.room, time)

    def min_background_concentration(self) -> _VectorisedFloat:
        """
        Background CO2 concentration in the atmosphere (in ppm)
        """
        return self.CO2_atmosphere_concentration

    def normalization_factor(self) -> _VectorisedFloat:
        # normalization by the CO2 exhaled per person.
        # CO2 concentration given in ppm, hence the 1e6 factor.
        return (1e6*self.population.activity.exhalation_rate
                *self.CO2_fraction_exhaled)


@dataclass(frozen=True)
class ShortRangeModel:
    '''
    Based on the two-stage (jet/puff) expiratory jet model by
    Jia et al (2022) - https://doi.org/10.1016/j.buildenv.2022.109166
    '''
    data_registry: DataRegistry

    #: Expiration type
    expiration: _ExpirationBase

    #: Activity type
    activity: Activity

    #: Short-range expiration and respective presence
    presence: SpecificInterval

    #: Interpersonal distances
    distance: _VectorisedFloat

    def dilution_factor(self) -> _VectorisedFloat:
        '''
        The dilution factor for the respective expiratory activity type.
        '''
        _dilution_factor = self.data_registry.short_range_model['dilution_factor'] 
        # Average mouth opening diameter (m)
        mouth_diameter: float = _dilution_factor['mouth_diameter'] # type: ignore

        # Breathing rate, from m3/h to m3/s
        BR = np.array(self.activity.exhalation_rate/3600.)

        # Exhalation coefficient. Ratio between the duration of a breathing cycle and the duration of
        # the exhalation.
        φ: float = _dilution_factor['exhalation_coefficient'] # type: ignore

        # Exhalation airflow, as per Jia et al. (2022)
        Q_exh: _VectorisedFloat = φ * BR

        # Area of the mouth assuming a perfect circle (m2)
        Am = np.pi*(mouth_diameter**2)/4

        # Initial velocity of the exhalation airflow (m/s)
        u0 = np.array(Q_exh/Am)

        # Duration of one breathing cycle
        breathing_cicle: float = _dilution_factor['breathing_cycle'] # type: ignore

        # Duration of the expiration period(s)
        tstar: float = breathing_cicle / 2

        # Streamwise and radial penetration coefficients
        _df_pc = _dilution_factor['penetration_coefficients'] # type: ignore
        𝛽r1: float = _df_pc['𝛽r1'] # type: ignore
        𝛽r2: float = _df_pc['𝛽r2'] # type: ignore
        𝛽x1: float = _df_pc['𝛽x1'] # type: ignore

        # Parameters in the jet-like stage
        # Position of virtual origin
        x0 = mouth_diameter/2/𝛽r1
        # Time of virtual origin
        t0 = (np.sqrt(np.pi)*(mouth_diameter**3))/(8*(𝛽r1**2)*(𝛽x1**2)*Q_exh)
        # The transition point, m
        xstar = np.array(𝛽x1*(Q_exh*u0)**0.25*(tstar + t0)**0.5 - x0)
        # Dilution factor at the transition point xstar
        Sxstar = np.array(2*𝛽r1*(xstar+x0)/mouth_diameter)

        distances = np.array(self.distance)
        factors = np.empty(distances.shape, dtype=np.float64)
        factors[distances < xstar] = 2*𝛽r1*(distances[distances < xstar]
                                        + x0)/mouth_diameter
        factors[distances >= xstar] = Sxstar[distances >= xstar]*(1 +
            𝛽r2*(distances[distances >= xstar] -
            xstar[distances >= xstar])/𝛽r1/(xstar[distances >= xstar]
            + x0))**3
        return factors
    
    def _normed_jet_origin_concentration(self) -> _VectorisedFloat:
        """
        The initial jet concentration at the source origin (mouth/nose), normalized by
        normalization_factor in the ShortRange class (corresponding to the diameter-independent
        variables). Results in mL.cm^-3.
        """
        # The short range origin concentration does not consider the mask contribution.
        return self.expiration.aerosols(mask=Mask.types['No mask'])

    def _long_range_normed_concentration(self, concentration_model: ConcentrationModel, time: float) -> _VectorisedFloat:
        """
        Virus long-range exposure concentration normalized by normalization_factor in the 
        ShortRange class, as function of time. Results in mL.cm^-3.
        """
        return (concentration_model.concentration(time) / self.normalization_factor(concentration_model.infected))

    def _normed_concentration(self, concentration_model: ConcentrationModel, time: float) -> _VectorisedFloat:
        """
        Virus short-range exposure concentration, as a function of time.

        If the given time falls within a short-range interval it returns the
        short-range concentration normalized by normalization_factor in the
        Short-range class. Otherwise it returns 0. Results in mL.cm^-3.
        """
        start, stop = self.presence.boundaries()[0]
        # Verifies if the given time falls within a short-range interaction
        if start <= time <= stop:
            dilution = self.dilution_factor()
            # Jet origin concentration normalized by the emission rate (except the BR)
            normed_jet_origin_concentration = self._normed_jet_origin_concentration()
            # Long-range concentration normalized by the emission rate (except the BR)
            long_range_normed_concentration = self._long_range_normed_concentration(concentration_model, time)

            # The long-range concentration values are then approximated using interpolation:
            # The set of points where we want the interpolated values are the short-range particle diameters (given the current expiration);
            # The set of points with a known value are the long-range particle diameters (given the initial expiration);
            # The set of known values are the long-range concentration values normalized by the viral load.
            long_range_normed_concentration_interpolated=np.interp(np.array(self.expiration.particle.diameter),
                                np.array(concentration_model.infected.particle.diameter), long_range_normed_concentration)

            # Short-range concentration formula. The long-range concentration is added in the concentration method (ExposureModel).
            # based on continuum model proposed by Jia et al (2022) - https://doi.org/10.1016/j.buildenv.2022.109166
            return ((1/dilution)*(normed_jet_origin_concentration - long_range_normed_concentration_interpolated))
        return 0.
    
    def normalization_factor(self, infected: InfectedPopulation) -> _VectorisedFloat:
        """
        The normalization factor applied to the short-range results. It refers to the emission
        rate per aerosol without accounting for the exhalation rate (viral load and f_inf).
        Result in (virions.cm^3)/(mL.m^3).
        """
        # Re-use the emission rate method divided by the BR contribution. 
        return infected.emission_rate_per_aerosol_per_person_when_present() / infected.activity.exhalation_rate
    
    def jet_origin_concentration(self, infected: InfectedPopulation) -> _VectorisedFloat:
        """
        The initial jet concentration at the source origin (mouth/nose).
        Returns the full result with the diameter dependent and independent variables, in virions/m^3.
        """
        return self._normed_jet_origin_concentration() * self.normalization_factor(infected)
    
    def short_range_concentration(self, concentration_model: ConcentrationModel, time: float) -> _VectorisedFloat:
        """
        Virus short-range exposure concentration, as a function of time.
        Factor of normalization applied back here. Results in virions/m^3.
        """
        return (self._normed_concentration(concentration_model, time) * 
                self.normalization_factor(concentration_model.infected))

    @method_cache
    def _normed_short_range_concentration_cached(self, concentration_model: ConcentrationModel, time: float) -> _VectorisedFloat:
        # A cached version of the _normed_concentration method. Use this
        # method if you expect that there may be multiple short-range concentration
        # calculations for the same time (e.g. at state change times).
        return self._normed_concentration(concentration_model, time)

    @method_cache
    def extract_between_bounds(self, time1: float, time2: float) -> typing.Union[None, typing.Tuple[float,float]]:
        """
        Extract the bounds of the interval resulting from the
        intersection of [time1, time2] and the presence interval.
        If [time1, time2] has nothing common to the presence interval,
        we return (0, 0).
        Raise an error if time1 and time2 are not in ascending order.
        """
        if time1>time2:
            raise ValueError("time1 must be less or equal to time2")

        start, stop = self.presence.boundaries()[0]
        if (stop < time1) or (start > time2):
            return (0, 0)
        elif start <= time1 and time2<= stop:
            return time1, time2
        elif start <= time1 and stop < time2:
            return time1, stop
        elif time1 < start and time2 <= stop:
            return start, time2
        elif time1 <= start and stop < time2:
            return start, stop

    def _normed_jet_exposure_between_bounds(self,
                    time1: float, time2: float):
        """
        Get the part of the integrated short-range concentration of
        viruses in the air, between the times start and stop, coming
        from the jet concentration, normalized by normalization_factor, 
        and without dilution.
        """
        start, stop = self.extract_between_bounds(time1, time2)
        # Note the conversion factor mL.cm^-3 -> mL.m^-3
        jet_origin = self._normed_jet_origin_concentration() * 10**6
        return jet_origin * (stop - start)

    def _normed_interpolated_longrange_exposure_between_bounds(
                    self, concentration_model: ConcentrationModel,
                    time1: float, time2: float):
        """
        Get the part of the integrated short-range concentration due
        to the background concentration, normalized by normalization_factor 
        together with breathing rate, and without dilution.
        One needs to interpolate the integrated long-range concentration
        for the particle diameters defined here.
        """
        start, stop = self.extract_between_bounds(time1, time2)
        if stop<=start:
            return 0.

        # Note that for the correct integration one needs to isolate those parameters
        # that are diameter-dependent from those that are diameter independent.
        # Therefore, the diameter-independent parameters (viral load, f_ind and BR)
        # are removed for the interpolation, and added back once the integration over
        # the new aerosol diameters (done with the mean) is completed.
        normed_int_concentration = (
            concentration_model.integrated_concentration(start, stop)
                /concentration_model.virus.viral_load_in_sputum
                /concentration_model.infected.fraction_of_infectious_virus()
                /concentration_model.infected.activity.exhalation_rate
                )
        normed_int_concentration_interpolated = np.interp(
                np.array(self.expiration.particle.diameter),
                np.array(concentration_model.infected.particle.diameter),
                normed_int_concentration
                )
        return normed_int_concentration_interpolated


@dataclass(frozen=True)
class CO2DataModel:
    '''
    The CO2DataModel class models CO2 data based on room volume and capacity, 
    ventilation transition times, and people presence.
    It uses optimization techniques to fit the model's parameters and estimate the
    exhalation rate and ventilation values that best match the measured CO2 concentrations.
    '''
    data_registry: DataRegistry
    room: Room
    occupancy: IntPiecewiseConstant
    ventilation_transition_times: typing.Tuple[float, ...]
    times: typing.Sequence[float]
    CO2_concentrations: typing.Sequence[float]

    def CO2_concentration_model(self, 
                                exhalation_rate: float, 
                                ventilation_values: typing.Tuple[float, ...]) -> CO2ConcentrationModel:
        return CO2ConcentrationModel(
            data_registry=self.data_registry,
            room=Room(volume=self.room.volume),
            ventilation=CustomVentilation(PiecewiseConstant(
                self.ventilation_transition_times, ventilation_values)),
            CO2_emitters=SimplePopulation(
                number=self.occupancy,
                presence=None,
                activity=Activity(
                    exhalation_rate=exhalation_rate, inhalation_rate=exhalation_rate),
            )
        )

    def CO2_concentrations_from_params(self, CO2_concentration_model: CO2ConcentrationModel) -> typing.List[_VectorisedFloat]:
        # Calculate the predictive CO2 concentration
        return [CO2_concentration_model.concentration(time) for time in self.times]

    def CO2_fit_params(self) -> typing.Dict:
        if len(self.times) != len(self.CO2_concentrations):
            raise ValueError('times and CO2_concentrations must have same length.')

        if len(self.times) < 2:
            raise ValueError(
                'times and CO2_concentrations must contain at last two elements')

        def fun(x):
            '''
            The objective function to be minimized, where x is an argument
            containing the initial guess for the breathing rate (exhalation_rate) 
            and ventilation values (ventilation_values).
            '''
            exhalation_rate = x[0]
            ventilation_values = tuple(x[1:])
            CO2_concentration_model = self.CO2_concentration_model(
                exhalation_rate=exhalation_rate,
                ventilation_values=ventilation_values
            )
            the_concentrations = self.CO2_concentrations_from_params(CO2_concentration_model)
            return np.sqrt(np.sum((np.array(self.CO2_concentrations) -
                                   np.array(the_concentrations))**2))
        # The goal is to minimize the difference between the two different curves (known concentrations vs. predicted concentrations)
        res_dict = minimize(fun=fun, x0=np.ones(len(self.ventilation_transition_times)), method='powell',
                            bounds=[(0, None) for _ in range(len(self.ventilation_transition_times))],
                            options={'xtol': 1e-3})

        # Final prediction
        exhalation_rate = res_dict['x'][0]
        ventilation_values = res_dict['x'][1:] # In ACH

        # Final CO2ConcentrationModel with obtained prediction
        the_CO2_concentration_model = self.CO2_concentration_model(
            exhalation_rate=exhalation_rate, 
            ventilation_values=ventilation_values
        )
        the_predictive_CO2 = self.CO2_concentrations_from_params(the_CO2_concentration_model)

        # Ventilation in L/s
        flow_rates_l_s = [vent / 3600 * self.room.volume * 1000 for vent in ventilation_values] # 1m^3 = 1000L
        
        # Ventilation in L/s/person
        flow_rates_l_s_p = [flow_rate / self.room.capacity for flow_rate in flow_rates_l_s] if self.room.capacity else None
        
        return {
            "exhalation_rate": exhalation_rate, 
            "ventilation_values": list(ventilation_values),
            "room_capacity": self.room.capacity,
            "ventilation_ls_values": flow_rates_l_s,
            "ventilation_lsp_values": flow_rates_l_s_p,
            'predictive_CO2': list(the_predictive_CO2)
        }


@dataclass(frozen=True)
class ExposureModel:
    """
    Represents the exposure to a concentration of
    infectious respiratory particles (IRP) in the air.
    """
    data_registry: DataRegistry

    #: The virus concentration model which this exposure model should consider.
    concentration_model: ConcentrationModel

    #: The list of short-range models which this exposure model should consider.
    short_range: typing.Tuple[ShortRangeModel, ...]

    #: The population of non-infected people to be used in the model.
    exposed: Population

    #: Geographical data
    geographical_data: Cases

    #: Total people with short-range interactions
    exposed_to_short_range: int = 0

    #: The number of times the exposure event is repeated (default 1).
    @property
    def repeats(self) -> int:
        return 1

    def __post_init__(self):
        """
        When diameters are sampled (given as an array),
        the Monte-Carlo integration over the diameters
        assumes that all the parameters within the IVRR,
        apart from the settling velocity, are NOT arrays.
        In other words, the air exchange rate from the
        ventilation, and the virus decay constant, must
        not be given as arrays.
        """
        c_model = self.concentration_model
        # Check if the diameter is vectorised.
        if (isinstance(c_model.infected, InfectedPopulation) and not np.isscalar(c_model.infected.expiration.diameter)
            # Check if the diameter-independent elements of the infectious_virus_removal_rate method are vectorised.
            and not (
                all(np.isscalar(c_model.virus.decay_constant(c_model.room.humidity, c_model.room.inside_temp.value(time)) +
                c_model.ventilation.air_exchange(c_model.room, time)) for time in c_model.state_change_times()))):
            raise ValueError("If the diameter is an array, none of the ventilation parameters "
                             "or virus decay constant can be arrays at the same time.")

    @method_cache
    def population_state_change_times(self) -> typing.List[float]:
        """
        All time dependent population entities on this model must provide information
        about the times at which their state changes.
        """
        state_change_times = set(self.concentration_model.infected.presence_interval().transition_times())
        state_change_times.update(self.exposed.presence_interval().transition_times())

        return sorted(state_change_times)

    def long_range_fraction_deposited(self) -> _VectorisedFloat:
        """
        The fraction of particles actually deposited in the respiratory
        tract (over the total number of particles). It depends on the
        particle diameter.
        """
        return self.concentration_model.infected.particle.fraction_deposited(
                    self.concentration_model.evaporation_factor)

    def _long_range_normed_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        """
        The number of virions per meter^3 between any two times, normalized
        by the emission rate of the infected population
        """
        exposure = 0.
        for start, stop in self.exposed.presence_interval().boundaries():
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

    def concentration(self, time: float) -> _VectorisedFloat:
        """
        Virus exposure concentration, as a function of time.

        It considers the long-range concentration with the
        contribution of the short-range concentration.
        """
        concentration = self.concentration_model.concentration(time)
        for interaction in self.short_range:
            concentration += interaction.short_range_concentration(self.concentration_model, time)
        return concentration

    def long_range_deposited_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        deposited_exposure = 0.

        emission_rate_per_aerosol_per_person = \
            self.concentration_model.infected.emission_rate_per_aerosol_per_person_when_present()
        aerosols = self.concentration_model.infected.aerosols()
        fdep = self.long_range_fraction_deposited()

        diameter = self.concentration_model.infected.particle.diameter

        if not np.isscalar(diameter) and diameter is not None:
            # We compute first the mean of all diameter-dependent quantities
            # to perform properly the Monte-Carlo integration over
            # particle diameters (doing things in another order would
            # lead to wrong results for the probability of infection).
            dep_exposure_integrated = np.array(self._long_range_normed_exposure_between_bounds(time1, time2) *
                                                aerosols *
                                                fdep).mean()
        else:
            # In the case of a single diameter or no diameter defined,
            # one should not take any mean at this stage.
            dep_exposure_integrated = self._long_range_normed_exposure_between_bounds(time1, time2)*aerosols*fdep

        # Then we multiply by the diameter-independent quantity emission_rate_per_aerosol_per_person,
        # and parameters of the vD equation (i.e. BR_k and n_in).
        deposited_exposure += (dep_exposure_integrated *
                emission_rate_per_aerosol_per_person *
                self.exposed.activity.inhalation_rate *
                (1 - self.exposed.mask.inhale_efficiency()))

        return deposited_exposure

    def deposited_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract
        between any two times.

        Considers a contribution between the short-range and long-range exposures:
        It calculates the deposited exposure given a short-range interaction (if any).
        Then, the deposited exposure given the long-range interactions is added to the
        initial deposited exposure.
        """
        deposited_exposure: _VectorisedFloat = 0.
        for interaction in self.short_range:
            start, stop = interaction.extract_between_bounds(time1, time2)
            short_range_jet_exposure = interaction._normed_jet_exposure_between_bounds(start, stop)
            short_range_lr_exposure = interaction._normed_interpolated_longrange_exposure_between_bounds(
                                        self.concentration_model, start, stop)
            dilution = interaction.dilution_factor()

            fdep = interaction.expiration.particle.fraction_deposited(evaporation_factor=1.0)
            diameter = interaction.expiration.particle.diameter

            # Aerosols not considered given the formula for the initial
            # concentration at mouth/nose.
            if diameter is not None and not np.isscalar(diameter):
                # We compute first the mean of all diameter-dependent quantities
                # to perform properly the Monte-Carlo integration over
                # particle diameters (doing things in another order would
                # lead to wrong results for the probability of infection).
                this_deposited_exposure = (np.array(short_range_jet_exposure
                    * fdep).mean()
                    - np.array(short_range_lr_exposure * fdep).mean()
                    * self.concentration_model.infected.activity.exhalation_rate)
            else:
                # In the case of a single diameter or no diameter defined,
                # one should not take any mean at this stage.
                this_deposited_exposure = (short_range_jet_exposure * fdep
                    - short_range_lr_exposure * fdep
                    * self.concentration_model.infected.activity.exhalation_rate)

            # Multiply by the (diameter-independent) inhalation rate
            deposited_exposure += (this_deposited_exposure *
                                   interaction.activity.inhalation_rate
                                   /dilution)

        # Then we multiply by the emission rate without the BR contribution (and conversion factor),
        # and parameters of the vD equation (i.e. n_in).
        deposited_exposure *= (
            (self.concentration_model.infected.emission_rate_per_aerosol_per_person_when_present() / (
             self.concentration_model.infected.activity.exhalation_rate * 10**6)) *                 
            (1 - self.exposed.mask.inhale_efficiency()))
        # Long-range concentration
        deposited_exposure += self.long_range_deposited_exposure_between_bounds(time1, time2)

        return deposited_exposure

    def _deposited_exposure_list(self):
        """
        The number of virus per m^3 deposited on the respiratory tract.
        """
        population_change_times = self.population_state_change_times()

        deposited_exposure = []
        for start, stop in zip(population_change_times[:-1], population_change_times[1:]):
            deposited_exposure.append(self.deposited_exposure_between_bounds(start, stop))

        return deposited_exposure

    def deposited_exposure(self) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract.
        """
        return np.sum(self._deposited_exposure_list(), axis=0) * self.repeats

    def _infection_probability_list(self):
        # Viral dose (vD)
        vD_list = self._deposited_exposure_list()

        # oneoverln2 multiplied by ID_50 corresponds to ID_63.
        infectious_dose = oneoverln2 * self.concentration_model.virus.infectious_dose

        # Probability of infection.
        return [(1 - np.exp(-((vD * (1 - self.exposed.host_immunity))/(infectious_dose *
                self.concentration_model.virus.transmissibility_factor)))) for vD in vD_list]

    @method_cache
    def infection_probability(self) -> _VectorisedFloat:
        return (1 - np.prod([1 - prob for prob in self._infection_probability_list()], axis = 0)) * 100

    def total_probability_rule(self) -> _VectorisedFloat:
        if (isinstance(self.concentration_model.infected.number, IntPiecewiseConstant) or
                isinstance(self.exposed.number, IntPiecewiseConstant)):
                raise NotImplementedError("Cannot compute total probability "
                        "(including incidence rate) with dynamic occupancy")

        if (self.geographical_data.geographic_population != 0 and self.geographical_data.geographic_cases != 0):
            sum_probability = 0.0

            # Create an equivalent exposure model but changing the number of infected cases.
            total_people = self.concentration_model.infected.number + self.exposed.number
            max_num_infected = (total_people if total_people < 10 else 10)
            # The influence of a higher number of simultainious infected people (> 4 - 5) yields an almost negligible contirbution to the total probability.
            # To be on the safe side, a hard coded limit with a safety margin of 2x was set.
            # Therefore we decided a hard limit of 10 infected people.
            for num_infected in range(1, max_num_infected + 1):
                exposure_model = nested_replace(
                    self, {'concentration_model.infected.number': num_infected}
                )
                prob_ind = exposure_model.infection_probability().mean() / 100
                n = total_people - num_infected
                # By means of the total probability rule
                prob_at_least_one_infected = 1 - (1 - prob_ind)**n
                sum_probability += (prob_at_least_one_infected *
                    self.geographical_data.probability_meet_infected_person(self.concentration_model.infected.virus, num_infected, total_people))
            return sum_probability * 100
        else:
            return 0

    def expected_new_cases(self) -> _VectorisedFloat:
        """
        The expected_new_cases may provide one or two different outputs:
            1) Long-range exposure: take the infection_probability and multiply by the occupants exposed to long-range. 
            2) Short- and long-range exposure: take the infection_probability of long-range multiplied by the occupants exposed to long-range only, 
               plus the infection_probability of short- and long-range multiplied by the occupants exposed to short-range only.

        Currently disabled when dynamic occupancy is defined for the exposed population.
        """

        if (isinstance(self.concentration_model.infected.number, IntPiecewiseConstant) or
            isinstance(self.exposed.number, IntPiecewiseConstant)):
            raise NotImplementedError("Cannot compute expected new cases "
                    "with dynamic occupancy")

        if self.short_range != ():
            new_cases_long_range = nested_replace(self, {'short_range': [],}).infection_probability() * (self.exposed.number - self.exposed_to_short_range)
            return (new_cases_long_range + (self.infection_probability() * self.exposed_to_short_range)) / 100

        return self.infection_probability() * self.exposed.number / 100

    def reproduction_number(self) -> _VectorisedFloat:
        """
        The reproduction number can be thought of as the expected number of
        cases directly generated by one infected case in a population.

        Currently disabled when dynamic occupancy is defined for both the infected and exposed population.
        """

        if (isinstance(self.concentration_model.infected.number, IntPiecewiseConstant) or
            isinstance(self.exposed.number, IntPiecewiseConstant)):
            raise NotImplementedError("Cannot compute reproduction number "
                    "with dynamic occupancy")

        if self.concentration_model.infected.number == 1:
            return self.expected_new_cases()

        # Create an equivalent exposure model but with precisely
        # one infected case.
        single_exposure_model = nested_replace(
            self, {
                'concentration_model.infected.number': 1}
        )

        return single_exposure_model.expected_new_cases()
    