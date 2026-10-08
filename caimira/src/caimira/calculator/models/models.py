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

# shape (n_populations, _VectorisedFloat)
_MatrixFloat = np.ndarray[float]

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
            fdep = IFrac * (0.0587 # type: ignore
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

    #: Expiration name
    name: typing.Optional[str] = None

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


@dataclass(frozen=True, kw_only=True)
class SimplePopulation:
    """
    Represents a group of people all with exactly the same behavior and
    situation.
    """
    #: Identifier of the population
    identifier: str = ""

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

    def first_presence_time(self) -> float:
        return self.presence_interval().boundaries()[0][0]


@dataclass(frozen=True, kw_only=True)
class Population(SimplePopulation):
    """
    Represents a group of people all with exactly the same behavior and
    situation, considering the usage of mask and a certain host immunity.

    """
    #: The kind of mask being worn by the people.
    mask: Mask

    #: The ratio of virions that are inactivated by the person's immunity.
    # This parameter considers the potential antibodies in the person,
    # which might render inactive some RNA copies (virions).
    host_immunity: float


@dataclass(frozen=True, kw_only=True)
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


@dataclass(frozen=True, kw_only=True)
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
    

@dataclass(frozen=True, kw_only=True)
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
class ShortRangeModel:
    '''
    Based on the two-stage (jet/puff) expiratory jet model by
    Jia et al (2022) - https://doi.org/10.1016/j.buildenv.2022.109166
    '''
    data_registry: DataRegistry

    #: Identifier of the population exposed to the jet
    exposed_identifier: str

    #: Physical activity of the infected during this short-range interaction. 
    #  TODO: All types of physical activities in activity must also be in infected.activity (or reasonable).
    activity: Activity

    #: Expiratory activity of the infected during this short-range interaction. 
    #  TODO: Validate that all types of expiratory activities in expiration are also in infected.expiration.
    #  dmin and dmax are different for expiration and infected.expiration.
    expiration: Expiration

    #: Short-range interaction time
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
    
    def _normed_diluted_jet_concentration(self):
        return 1/self.dilution_factor()*self._normed_jet_origin_concentration()

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


@dataclass(frozen=True)
class _ConcentrationModelBase:
    """
    A generic superclass that contains the methods to calculate the
    concentration (e.g. viral concentration or CO2 concentration).

    Note that min_background_concentration is added at the very end, 
    and not to the normalized computations of the (integrated) concentration. 
    Hence, computation of normalized concetrations and the normalization_factor
    are kept fully separate. 

    The normalization factor instances have dimentionality
        ``(n_populations, n_samples)`` 
    where n_samples is the number of MC samples of diameter-independent random 
    variables. 

    If the aerosol diameter is a random variable, the normalized methods also
    return arrays with dimentionality
        ``(n_populations, n_samples)`` 

    Otherwise, if the aerosol diameter is not a random variable, the normalized methods 
    return arrays with dimentionality
        ``(n_populations, )`` 

    Because the normalization_factor may have a different shape than normalized methods,
    it is important to compute the normalization_factor separate of the normalized methods.
    Therefore, the (non-normalized) min_background_concentration is only included after 
    multiplying the normalized results with the normalization_factor. 
    """
    data_registry: DataRegistry
    room: Room
    ventilation: _VentilationBase

    @property
    def populations(self) -> typing.Tuple[SimplePopulation, ...]:
        """
        Population in the room (the emitters of what we compute the
        concentration of)
        """
        raise NotImplementedError("Subclass must implement")

    def people_present(self, time) -> np.array[float]:
        return np.asarray(
            [population.people_present(time) for population in self.populations],
            dtype=np.float64,
        )[:, np.newaxis]
    
    def removal_rate(self, time: float) -> _MatrixFloat:
        """
        Remove rate of the species considered, in h^-1
        """
        raise NotImplementedError("Subclass must implement")

    def min_background_concentration(self) -> float:
        """
        Minimum background concentration in the room for a given scenario
        (in the same unit as the concentration). Its the value towards which
        the concentration will decay to.
        """
        return self.data_registry.concentration_model['virus_concentration_model']['min_background_concentration'] # type: ignore

    def normalization_factor(self) -> _MatrixFloat:
        """
        Normalization factor (in the same unit as the concentration).
        This factor is applied to the normalized concentration only
        at the very end.
        """
        raise NotImplementedError("Subclass must implement")

    @method_cache
    def _normed_concentration_increase_limit(self, time: float) -> _MatrixFloat:
        """
        Provides a constant that represents the theoretical asymptotic
        value reached by the concentration when time goes to infinity,
        if all parameters were to stay time-independent.
        This is normalized by the normalization factor, the latter acting as a
        multiplicative constant factor for the concentration model that
        can be put back in front of the concentration after the time
        dependence has been solved for.
        """
        volume = np.asarray(self.room.volume, dtype=np.float64)
        if volume.ndim == 1:
            volume = volume[np.newaxis, :]
        RR = np.asarray(self.removal_rate(time), dtype=np.float64)

        # Set $1 / RR$ to NaN where $RR = 0$, without divide-by-zero warnings.
        invRR = np.full_like(RR, np.nan, dtype=np.float64)
        np.divide(
            1.0,
            RR,
            out=invRR,
            where=RR != 0.0,
        )
        return (self.people_present(time) * invRR / self.room.volume)

    @method_cache
    def state_change_times(self) -> typing.List[float]:
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.
        """
        state_change_times = {0.}
        for population in self.populations:
            state_change_times.update(population.presence_interval().transition_times())
        state_change_times.update(self.ventilation.transition_times(self.room))
        return sorted(state_change_times)

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

    @method_cache
    def _normed_concentration_increase_cached(self, time: float) -> _MatrixFloat:
        """
        A cached version of the _normed_concentration method. Use this
        method if you expect that there may be multiple concentration
        calculations for the same time (e.g. at state change times).
        """
        return self._normed_concentration_increase(time)

    def _normed_concentration_increase(self, time: float) -> _MatrixFloat:
        """
        Concentration increase from the min_background_concentration 
        as a function of time, normalized by normalization_factor, 
        for each population. 

        The formulas used here assume that all parameters (ventilation,
        emission rate) are constant between two state changes - only
        the value of these parameters at the next state change, are used.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        volume = np.asarray(self.room.volume, dtype=np.float64)
        if volume.ndim == 1:
            volume = volume[np.newaxis, :]

        t_last_state_change = self.last_state_change(time)
        delta_time = time - t_last_state_change
        RR = self.removal_rate(time)
        if time == 0.0:
            return np.zeros_like(RR, dtype=np.float64)

        conc_at_last_state_change = self._normed_concentration_increase_cached(
            t_last_state_change
        )

        concentration_limit = np.asarray(
            self._normed_concentration_increase_limit(time),
            dtype=np.float64,
        )
        if concentration_limit.ndim == 1:
            concentration_limit = concentration_limit[:, np.newaxis]

        people_present = np.asarray(
            self.people_present(time),
            dtype=np.float64,
        )
        if people_present.ndim == 1:
            people_present = people_present[:, np.newaxis]

        fac = np.exp(-RR * delta_time)
        curr_conc_state = np.empty_like(concentration_limit, dtype=np.float64)

        np.divide(
            delta_time * people_present,
            self.room.volume,
            out=curr_conc_state,
            where=RR == 0.0,
        )

        np.multiply(
            concentration_limit,
            1.0 - fac,
            out=curr_conc_state,
            where=RR != 0.0,
        )

        result = curr_conc_state + conc_at_last_state_change * fac

        before_first_presence = np.asarray(
            [
                time <= population.first_presence_time()
                for population in self.populations
            ],
            dtype=bool,
        )[:, np.newaxis]

        return np.where(before_first_presence, 0.0, result)

    def concentration(self, time: float) -> _MatrixFloat:
        """
        Total concentration as a function of time, including the 
        min_background_concentration. The normalization
        factor has been put back.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """
        return (self._normed_concentration_increase_cached(time)*self.normalization_factor()
                +self.min_background_concentration())

    @method_cache
    def normed_integrated_concentration_increase(self, start: float, stop: float) -> _MatrixFloat:
        """
        Get the integrated concentration increase between the times start and stop,
        not including the min_background_concentration, normalized by normalization_factor.
        """
        change_times = np.asarray(self.state_change_times(), dtype=np.float64)
        interval_bounds = np.unique(np.concatenate((
            np.array([start, stop]),
            change_times[(change_times > start) & (change_times < stop)],
        )))

        volume = np.asarray(self.room.volume, dtype=np.float64)
        if volume.ndim == 1:
            volume = volume[np.newaxis, :]

        total_normed_concentration = np.zeros_like(self._normed_concentration_increase_cached(start), dtype=np.float64)
        for interval_start, interval_stop in zip(
            interval_bounds[:-1],
            interval_bounds[1:],
        ):
            delta_time = interval_stop - interval_start

            conc_start = self._normed_concentration_increase_cached(interval_start)
            conc_limit = self._normed_concentration_increase_limit(interval_stop)
            removal_rate = self.removal_rate(interval_stop)

            nonzero_removal = removal_rate != 0.0
            contribution = np.empty_like(removal_rate, dtype=np.float64)

            np.divide(
                (conc_limit - conc_start)
                * np.expm1(-removal_rate * delta_time),
                removal_rate,
                out=contribution,
                where=nonzero_removal,
            )
            contribution[nonzero_removal] += (
                conc_limit[nonzero_removal] * delta_time
            )
            people_present = self.people_present(interval_stop)
            zero_removal = ~nonzero_removal

            zero_removal_contribution = (
                conc_start * delta_time
                + people_present * delta_time ** 2 / (2.0 * volume)
            )
            contribution[zero_removal] = (
                zero_removal_contribution[zero_removal]
            )

            total_normed_concentration += contribution

        # A population which has not entered before
        # `stop` contributes no integrated concentration.
        not_yet_present = np.asarray(
            [
                stop <= population.first_presence_time()
                for population in self.populations
            ],
            dtype=bool,
        )[:, np.newaxis]

        return np.where(not_yet_present, 0.0, total_normed_concentration)

    def integrated_concentration_increase(self, start: float, stop: float) -> _MatrixFloat:
        """
        Get the integrated concentration increase, not including the min_background_concentration,
        of aerosols between the times start and stop.
        """
        return (self.normed_integrated_concentration_increase(start, stop)*self.normalization_factor())

    def integrated_concentration(self, start: float, stop: float) -> float:
        """
        Get the integrated concentration, including the min_background_concentration,
        of aerosols between the times start and stop.
        """
        return (self.integrated_concentration_increase(start, stop)
                +(stop-start)*self.min_background_concentration())

@dataclass(frozen=True)
class ConcentrationModel(_ConcentrationModelBase):
    """
    Class used for the computation of the long-range virus concentration.
    """
    #: Infected population in the room, emitting virions
    infected_populations: typing.Tuple[InfectedPopulation, ...]

    #: evaporation factor: the particles' diameter is multiplied by this
    # factor as soon as they are in the air (but AFTER going out of the,
    # mask, if any).
    evaporation_factor: float

    #: The short-range interactions the infected in this class is participating in.
    short_range: typing.Tuple[typing.Tuple[ShortRangeModel, ...], ...]

    def __post_init__(self):
        if self.evaporation_factor is None:
            self.evaporation_factor = self.data_registry.expiration_particle['particle']['evaporation_factor']

        if any(infected.virus is not self.virus for infected in self.infected_populations):
            raise ValueError("All infected must be infected with the same virus.")

        for infected, interaction_tuple in zip(self.infected_populations, self.short_range):
            for interaction in interaction_tuple:
                if interaction.presence.boundaries()[0][0] < infected.presence.boundaries()[0][0] or interaction.presence.boundaries()[-1][-1] > infected.presence.boundaries()[-1][-1]:
                    raise ValueError("A short-range-interaction cannot lie outside the presence of the infected.")

    @property
    def populations(self) -> InfectedPopulation:
        return self.infected_populations

    @property
    def virus(self) -> Virus:
        return self.infected_populations[0].virus

    def normalization_factor(self) -> _MatrixFloat:
        # we normalize by the emission rate
        nf = np.asarray([infected.emission_rate_per_person_when_present()
            for infected in self.infected_populations],
            dtype=np.float64,
        )
        if nf.ndim == 1:
            return nf[:, np.newaxis] 
        else:
            return nf

    def removal_rate(self, time: float) -> _MatrixFloat:
        # Equilibrium velocity of particle motion toward the floor
        vg = np.asarray([
            infected.particle.settling_velocity(self.evaporation_factor)
            for infected in self.infected_populations
        ], dtype=float)
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h
        RR = (
            k + self.virus.decay_constant(self.room.humidity, self.room.inside_temp.value(time))
            + self.ventilation.air_exchange(self.room, time)
        )
        if RR.ndim == 1:
            return RR[:, np.newaxis]
        else:
            return RR

    def short_range_normalization_factors(self) -> _MatrixFloat:
        """
        For short-range interactions, the infected population parameters intervene only through this factor.
        Result in (virions.cm^3)/(mL.m^3).
        """
        # Re-use the emission rate method divided by the BR contribution. 
        sr_nf = np.asarray([
            infected.emission_rate_per_aerosol_per_person_when_present() / infected.activity.exhalation_rate
            for infected in self.infected_populations
        ])
        if sr_nf.ndim == 1:
            return sr_nf[:, np.newaxis] 
        else:
            return sr_nf


@dataclass(frozen=True)
class CO2ConcentrationModel(_ConcentrationModelBase):
    """
    Class used for the computation of the CO2 concentration.
    """
    #: Population in the room emitting CO2
    CO2_emitting_populations: typing.Tuple[SimplePopulation, ...]

    #: CO2 concentration in the atmosphere (in ppm)
    @property
    def CO2_atmosphere_concentration(self) -> float:
        return self.data_registry.concentration_model['CO2_concentration_model']['CO2_atmosphere_concentration'] # type: ignore

    #: CO2 fraction in the exhaled air
    @property
    def CO2_fraction_exhaled(self) -> float:
        return self.data_registry.concentration_model['CO2_concentration_model']['CO2_fraction_exhaled'] # type: ignore

    @property
    def populations(self) -> typing.Tuple[SimplePopulation, ...]:
        return self.CO2_emitting_populations

    def removal_rate(self, time: float) -> _VectorisedFloat:
        RR = np.asarray([self.ventilation.air_exchange(self.room, time)]*len(self.populations))
        if RR.ndim == 1:
            return RR[:, np.newaxis]
        else:
            return RR

    def min_background_concentration(self) -> _VectorisedFloat:
        """
        Background CO2 concentration in the atmosphere (in ppm)
        """
        return self.CO2_atmosphere_concentration

    def normalization_factor(self) -> _VectorisedFloat:
        # normalization by the CO2 exhaled per person.
        # CO2 concentration given in ppm, hence the 1e6 factor.
        nf = np.asarray([
            1e6*population.activity.exhalation_rate*self.CO2_fraction_exhaled
            for population in self.populations],
            dtype=np.float64,
        )
        if nf.ndim == 1:
            return nf[:, np.newaxis] 
        else:
            return nf

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
            CO2_emitting_populations=(
                    SimplePopulation(
                    identifier="",
                    number=self.occupancy,
                    presence=None,
                    activity=Activity(
                        exhalation_rate=exhalation_rate, inhalation_rate=exhalation_rate),
                ),
            ),
        )

    def CO2_concentrations_from_params(self, CO2_concentration_model: CO2ConcentrationModel) -> typing.List[_VectorisedFloat]:
        # Calculate the predictive CO2 concentration
        return [CO2_concentration_model.concentration(time).mean() for time in self.times] # Averaging arrays with 1 element

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

    #: The population of non-infected people to be used in the model.
    exposed: Population

    #: Geographical data
    geographical_data: Cases

    #: Total people with short-range interactions
    exposed_to_short_range: int = 0

    @property
    def identifier(self) -> str:
        return self.exposed.identifier

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

        It also checks that the number of exposed is
        static during the simulation time.
        """
        for infected in self.concentration_model.infected_populations:
            # Check if the diameter is vectorised.
            if (isinstance(infected, InfectedPopulation) and not np.isscalar(infected.expiration.diameter)
                # Check if the diameter-independent elements of the infectious_virus_removal_rate method are vectorised.
                and not (
                    all(np.isscalar(self.virus.decay_constant(self.room.humidity, self.room.inside_temp.value(time)) +
                    self.concentration_model.ventilation.air_exchange(self.room, time)) for time in self.concentration_model.state_change_times()))):
                raise ValueError("If the diameter is an array, none of the ventilation parameters "
                                "or virus decay constant can be arrays at the same time.")
        
        # Check if exposed population is static
        if not isinstance(self.exposed.number, int) or not isinstance(self.exposed.presence, Interval):
            raise TypeError("The exposed number must be an int and presence an Interval. "
                            f"Got {type(self.exposed.number)} and {type(self.exposed.presence)}.")


    @property
    def virus(self):
        return self.concentration_model.virus
    
    @property
    def room(self):
        return self.concentration_model.room

    @property
    def evaporation_factor(self):
        return self.concentration_model.evaporation_factor

    @method_cache
    def population_state_change_times(self) -> typing.List[float]:
        """
        All time dependent population entities on this model must provide information
        about the times at which their state changes.
        """
        state_change_times = set(self.exposed.presence_interval().transition_times())
        for infected in self.concentration_model.infected_populations:
            state_change_times.update(infected.presence_interval().transition_times())

        return sorted(state_change_times)

    def long_range_fraction_deposited(self, infected) -> _VectorisedFloat:
        """
        The fraction of particles actually deposited in the respiratory
        tract (over the total number of particles). It depends on the
        particle diameter.
        """
        return infected.particle.fraction_deposited(self.evaporation_factor)

    def _long_range_normed_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        """
        The number of virions per meter^3 between any two times, normalized
        by the emission rate of the infected population
        """
        exposure = np.zeros_like(self.concentration_model.normed_integrated_concentration_increase(self.population_state_change_times()[0], self.population_state_change_times()[1]), dtype=np.float64)
        for start, stop in self.exposed.presence_interval().boundaries():
            if stop < time1:
                continue
            elif start > time2:
                break
            elif start <= time1 and time2<= stop:
                exposure += self.concentration_model.normed_integrated_concentration_increase(time1, time2)
            elif start <= time1 and stop < time2:
                exposure += self.concentration_model.normed_integrated_concentration_increase(time1, stop)
            elif time1 < start and time2 <= stop:
                exposure += self.concentration_model.normed_integrated_concentration_increase(start, time2)
            elif time1 <= start and stop < time2:
                exposure += self.concentration_model.normed_integrated_concentration_increase(start, stop)
        return exposure
    
    def long_range_concentration(self, time: float) -> float:
        """
        Total virus concentration in the room at long-range, as a function of time, averaged over the particle diameters.

        It only considers the long-range concentration without the
        contribution of the short-range concentration.

        Since the different ConcentrationModel objects may have different infected with different expirations,
        they can have different particle diameters bases drawn from different probability distributions.
        To Monte-Carlo integrate correctly over the particle diameters, we must therefore average the concentration 
        of each ConcentrationModel over the particle diameters before adding together all the contributions from all 
        the ConcentrationModels.
        """
        return self.concentration_model.concentration(time)
    
    def concentration(self, time: float) -> float:
        """
        Integrated virus exposure concentration, as a function of time.

        It considers the long-range concentration with the
        contribution of the short-range concentration.

        Since the different ConcentrationModel objects may have different diameter bases drawn 
        from different distributions, the concentrations from different ConcentrationModel 
        objects must be averaged over the diameter before summed together.
        """
        concentration = self.long_range_concentration(time)
        for short_range_normalization_factor, interactions in zip(self.concentration_model.short_range_normalization_factors(), self.concentration_model.short_range):
            for interaction in interactions:
                if interaction.exposed_identifier == self.identifier:
                    start, stop = interaction.presence.boundaries()[0]
                    # Verifies if the given time falls within a short-range interaction
                    # NOTE: max one short-range interaction at a time, so the test should just yield true once (TODO check?)
                    if start <= time <= stop:
                        concentration += interaction._normed_diluted_jet_concentration()*short_range_normalization_factor
                        concentration -= 1/interaction.dilution_factor() * self.concentration_model.concentration(time)
        return concentration

    def long_range_deposited_exposure_between_bounds(self, time1: float, time2: float) -> _VectorisedFloat:
        deposited_exposure = 0.

        _long_range_normed_exposure_between_bounds = self._long_range_normed_exposure_between_bounds(time1, time2)
        for infected, normed_exposure in zip(self.concentration_model.infected_populations, _long_range_normed_exposure_between_bounds):
            diameter = infected.particle.diameter
            fdep = self.long_range_fraction_deposited(infected)
            aerosols = infected.aerosols()
            emission_rate_per_aerosol_per_person = \
                infected.emission_rate_per_aerosol_per_person_when_present()

            if not np.isscalar(diameter) and diameter is not None:#TODO: check dimention of normed_exposure instead so diameter does not have to be retrieved?
                # We compute first the mean of all diameter-dependent quantities
                # to perform properly the Monte-Carlo integration over
                # particle diameters (doing things in another order would
                # lead to wrong results for the probability of infection).
                dep_exposure_integrated = np.array(normed_exposure *
                                                    aerosols *
                                                    fdep).mean()
            else:
                # In the case of a single diameter or no diameter defined,
                # one should not take any mean at this stage.
                dep_exposure_integrated = normed_exposure*aerosols*fdep

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
        for infected, interatcions in zip(self.concentration_model.infected_populations, self.concentration_model.short_range):
            for interaction in interatcions:
                if interaction.exposed_identifier == self.identifier:
                    # Only adding the additional contribution from the short-range interaction
                    start, stop = interaction.extract_between_bounds(time1, time2)
                    short_range_jet_exposure = interaction._normed_jet_exposure_between_bounds(start, stop)

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
                            * fdep).mean())
                    else:
                        # In the case of a single diameter or no diameter defined,
                        # one should not take any mean at this stage.
                        this_deposited_exposure = (short_range_jet_exposure * fdep)

                    # Multiply by the (diameter-independent) inhalation rate
                    _deposited_exposure = (this_deposited_exposure *
                                        interaction.activity.inhalation_rate
                                        /dilution) 
                    
                    # Then we multiply by the emission rate without the BR contribution (and conversion factor),
                    # and parameters of the vD equation (i.e. n_in).
                    deposited_exposure += _deposited_exposure*(
                        (infected.emission_rate_per_aerosol_per_person_when_present() / (
                        infected.activity.exhalation_rate * 10**6)) *                 
                        (1 - self.exposed.mask.inhale_efficiency()))
                    
                    deposited_exposure -= self.long_range_deposited_exposure_between_bounds(time1, time2)/dilution

            
        # Long-range contributions from all infected populations (including the ones with SR interactions)
        deposited_exposure += self.long_range_deposited_exposure_between_bounds(time1, time2)

        return deposited_exposure

    def deposited_exposure(self, short_range: bool = True) -> _VectorisedFloat:
        """
        The number of virus per m^3 deposited on the respiratory tract of a  
        member of the considered exposed population, accumulated over the entire 
        presence of the exposed.
        If short_range = True, the dose exposure from all short-range interactions 
        the exposed have is included.
        If short_range = False, then we only consider long-range dose exposure.
        """
        population_change_times = self.population_state_change_times()
        deposited_exposure = []
        if short_range:
            for start, stop in zip(population_change_times[:-1], population_change_times[1:]):
                deposited_exposure.append(self.deposited_exposure_between_bounds(start, stop))
        else:
            for start, stop in zip(population_change_times[:-1], population_change_times[1:]):
                deposited_exposure.append(self.long_range_deposited_exposure_between_bounds(start, stop))
        return np.sum(deposited_exposure, axis=0) * self.repeats # type: ignore

    @method_cache
    def individual_infection_probability(self, short_range: bool = True) -> _VectorisedFloat:
        """
        The probability that a specific member of the considered exposed population 
        will be infected.
        If short_range = True, the probability is computed including dose exposure 
        from any short-range interactions the exposed might have.
        If short_range = False, the probability is computing only considering 
        long-range dose exposure.
        Note that if no short-range interactions are defined for the exposed, 
        this method will yield the same result with both values of short_range
        """
        # Viral dose (vD)
        vD = self.deposited_exposure(short_range)

        # oneoverln2 multiplied by ID_50 corresponds to ID_63.
        infectious_dose = oneoverln2 * self.virus.infectious_dose

        # Probability of infection.
        return (1 - np.exp(-((vD * (1 - self.exposed.host_immunity))/(infectious_dose *
                self.virus.transmissibility_factor)))) * 100

    def total_probability_rule(self) -> _VectorisedFloat:
        if len(self.concentration_model.infected_populations) > 1:
            raise NotImplementedError("Cannot compute total probability "
                        "(including incidence rate) with dynamic occupancy")
        elif isinstance(self.concentration_model.infected_populations[0].number, IntPiecewiseConstant):
                raise NotImplementedError("Cannot compute total probability "
                        "(including incidence rate) with dynamic occupancy")

        if (self.geographical_data.geographic_population != 0 and self.geographical_data.geographic_cases != 0):
            sum_probability = 0.0

            # Create an equivalent exposure model but changing the number of infected cases.
            total_people = self.concentration_model.infected_populations[0].number + self.exposed.number # type: ignore
            max_num_infected = (total_people if total_people < 10 else 10)
            # The influence of a higher number of simultaneous infected people (> 4 - 5) yields an almost negligible contribution to the total probability.
            # To be on the safe side, a hard coded limit with a safety margin of 2x was set.
            # Therefore we decided a hard limit of 10 infected people.
            for num_infected in range(1, max_num_infected + 1):
                infected = self.concentration_model.infected_populations[0]
                new_infected = nested_replace(infected, {"number": num_infected})
                exposure_model = nested_replace(
                    self, {'concentration_model.infected_populations': (new_infected,)}
                )
                prob_ind = exposure_model.individual_infection_probability().mean() / 100
                n = total_people - num_infected
                # By means of the total probability rule
                prob_at_least_one_infected = 1 - (1 - prob_ind)**n
                sum_probability += (prob_at_least_one_infected *
                    self.geographical_data.probability_meet_infected_person(self.virus, num_infected, total_people))
            return sum_probability * 100
        else:
            return 0

    def expected_new_cases(self) -> _VectorisedFloat:
        """
        The expected_new_cases may provide one or two different outputs:
            1) Long-range exposure: take the individual_infection_probability and multiply by the occupants exposed only to long-range concentrations. 
            2) Short- and long-range exposure: take the individual_infection_probability of long-range multiplied by the occupants exposed to long-range only, 
               and add the individual_infection_probability of short- and long-range multiplied by the occupants who are also exposed to short-range.
        """
        number = self.exposed.number
        new_cases_long_range = (self.individual_infection_probability(short_range=False) / 100) * (number - self.exposed_to_short_range) # type: ignore
        new_cases_short_range = (self.individual_infection_probability(short_range=True) / 100) * self.exposed_to_short_range
        return (new_cases_long_range + new_cases_short_range) 

    def reproduction_number(self) -> _VectorisedFloat:
        """
        The reproduction number can be thought of as the expected number of
        cases directly generated by one infected case in a population.
        """
        if len(self.concentration_model.infected_populations) > 1:
            raise NotImplementedError("yet to implement dynamic infected for the reproduction number")
        infected_population: InfectedPopulation = self.concentration_model.infected_populations[0]
        if isinstance(infected_population.number, int) and infected_population.number == 1:
            return self.expected_new_cases()

        # Create an equivalent exposure model but with precisely
        # one infected case, respecting the presence interval.
        infected = self.concentration_model.infected_populations[0]
        new_infected = nested_replace(infected, {"number": 1, "presence": infected_population.presence_interval(),})
        single_exposure_model = nested_replace(
            self, {'concentration_model.infected_populations': (new_infected,)}
        )
        return single_exposure_model.expected_new_cases()
    

@dataclass(frozen=True)
class ExposureModelGroup:
    """
    Represents a group of exposure models. This is to handle the case
    when different groups of people come and go in the room at different
    times. These groups are then handled fully independently, with
    exposure dose and probability of infection defined for each of them.
    """
    data_registry: DataRegistry

    #: The set of exposure models for each exposed population
    exposure_models: typing.Tuple[ExposureModel, ...]

    def __post_init__(self):
        """
        Validate that all ExposureModels have the same list of ConcentrationModels.
        """
        n_infected_populations = len(self.exposure_models[0].concentration_model.infected_populations)
        if any(len(exposure_model.concentration_model.infected_populations) != n_infected_populations for exposure_model in self.exposure_models[1:]):
                raise ValueError("All ExposureModels must have the same number of ConcentrationModels.")
        for i in range(n_infected_populations):
            first_infected = self.exposure_models[0].concentration_model.infected_populations[0]
            for model in self.exposure_models[1:]:
                # Check that the number of infected people and their presence is the same
                if (model.concentration_model.infected_populations[i].number != first_infected.number or
                    model.concentration_model.infected_populations[i].presence != first_infected.presence):
                    raise ValueError("All ExposureModels must have the same infected number and presence in each ConcentrationModel.")

    @method_cache
    def _deposited_exposure_list(self) -> typing.List[_VectorisedFloat]:
        """
        List of doses absorbed by each member of the groups.
        """
        return [model.deposited_exposure() for model in self.exposure_models]
    
    @method_cache
    def individual_infection_probability(self):
        """
        List of the probability of infection for each group.
        """
        return [model.individual_infection_probability() for model in self.exposure_models] # type: ignore

    def expected_new_cases(self) -> _VectorisedFloat:
        """
        Final expected number of new cases considering the
        contribution of each individual probability of infection.
        """
        return np.sum([model.expected_new_cases() for model in self.exposure_models], axis=0) # type: ignore
    
    def reproduction_number(self) -> _VectorisedFloat:
        """
        Expected number of cases when there is only one infected case.
        """
        return np.sum([model.reproduction_number() for model in self.exposure_models], axis=0) # type: ignore
