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

if not typing.TYPE_CHECKING:
    from memoization import cached
else:
    # Workaround issue https://github.com/lonelyenvoy/python-memoization/issues/18
    # by providing a no-op cache decorator when type-checking.
    cached = lambda *cached_args, **cached_kwargs: lambda function: function  # noqa

from .dataclass_utils import nested_replace


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
    humidity: _VectorisedFloat=0.5


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

    def boundaries(self) -> BoundarySequence_t:
        if self.period == 0 or self.duration == 0:
            return tuple()
        result = []
        for i in np.arange(0, 24, self.period / 60):
            result.append((i, i+self.duration/60))
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
            raise ValueError("transition_times should contain one more element than values")
        if tuple(sorted(set(self.transition_times))) != self.transition_times:
            raise ValueError("transition_times should not contain duplicated elements and should be sorted")
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
            tuple(refined_times),
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
        if self.window_width is 0.0:
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

    #: RNA-copies per quantum
    quantum_infectious_dose: _VectorisedFloat

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
        halflife = np.empty_like(humidity)
        halflife[humidity <= 0.4] = 3.8
        halflife[humidity > 0.4] = 1.1
        return halflife


Virus.types = {
    'SARS_CoV_2': SARSCoV2(
        viral_load_in_sputum=1e9,
        # No data on coefficient for SARS-CoV-2 yet.
        # It is somewhere between 1000 or 10 SARS-CoV viruses, 
        # as per https://www.dhs.gov/publication/st-master-question-list-covid-19
        # 50 comes from Buonanno et al.
        quantum_infectious_dose=50.,
    ),
    'SARS_CoV_2_B117': SARSCoV2(
        # also called VOC-202012/01
        viral_load_in_sputum=1e9,
        quantum_infectious_dose=30.,
    ),
    'SARS_CoV_2_P1': SARSCoV2(
        viral_load_in_sputum=1e9,
        quantum_infectious_dose=1/0.045,
    ),
}


@dataclass(frozen=True)
class Mask:
    #: Filtration efficiency of masks when inhaling.
    η_inhale: _VectorisedFloat

    #: Global factor applied to filtration efficiency of masks when exhaling.
    factor_exhale: _VectorisedFloat = 1.

    #: Pre-populated examples of Masks.
    types: typing.ClassVar[typing.Dict[str, "Mask"]]

    def exhale_efficiency(self, diameter: float) -> _VectorisedFloat:
        """
        Overall exhale efficiency, including the effect of the leaks.
        See CERN-OPEN-2021-004 (doi: 10.17181/CERN.1GDQ.5Y75), and Ref.
        therein (Asadi 2020).
        Obtained from measurements of filtration efficiency and of
        the leakage through the sides.
        Diameter is in microns.
        """
        if diameter < 0.5:
            eta_out = 0.
        elif diameter < 0.94614:
            eta_out = 0.5893 * diameter + 0.1546
        elif diameter < 3.:
            eta_out = 0.0509 * diameter + 0.664
        else:
            eta_out = 0.8167
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
class _ExpirationBase:
    """
    Represents the expiration of aerosols by a person.
    Subclasses of _ExpirationBase represent different models.
    """
    #: Pre-populated examples of Expirations.
    types: typing.ClassVar[typing.Dict[str, "_ExpirationBase"]]

    def aerosols(self, mask: Mask):
        # total volume of aerosols expired (cm^3).
        raise NotImplementedError("Subclass must implement")


@dataclass(frozen=True)
class Expiration(_ExpirationBase):
    """
    Simple model based on four different sizes of particles emitted,
    with different ejection factors. See Fig. 4 in L. Morawska et al,
    Size distribution and sites of origin of droplets expelled from the
    human respiratory tract during expiratory activities,
    Aerosol Science 40 (2009) pp. 256 - 269.
    """
    ejection_factor: typing.Tuple[float, ...]
    particle_sizes: typing.Tuple[float, ...] = (0.8e-4, 1.8e-4, 3.5e-4, 5.5e-4)  # In cm.

    def aerosols(self, mask: Mask):
        def volume(diameter):
            return (4 * np.pi * (diameter/2)**3) / 3
        total = 0
        for diameter, factor in zip(self.particle_sizes, self.ejection_factor):
            contribution = (volume(diameter) * factor *
                            (1 - mask.exhale_efficiency(diameter*1e4)))
            total += contribution
        return total


@dataclass(frozen=True)
class MultipleExpiration(_ExpirationBase):
    """
    Represents an expiration of aerosols.
    Group together different modes of expiration, that represent
    each the main expiration mode for a certain fraction of time (given by
    the weights).

    """
    expirations: typing.Tuple[_ExpirationBase, ...]
    weights: typing.Tuple[float, ...]

    def __post_init__(self):
        if len(self.expirations) != len(self.weights):
            raise ValueError("expirations and weigths should contain the"
                             "same number of elements")

    def aerosols(self, mask: Mask):
        return np.array([
            weight * expiration.aerosols(mask) / sum(self.weights)
            for weight,expiration in zip(self.weights,self.expirations)
        ]).sum(axis=0)


_ExpirationBase.types = {
    'Breathing': Expiration((0.084, 0.009, 0.003, 0.002)),
    'Whispering': Expiration((0.11, 0.014, 0.004, 0.002)),
    'Talking': Expiration((0.236, 0.068, 0.007, 0.011)),
    'Unmodulated Vocalization': Expiration((0.751, 0.139, 0.0139, 0.059)),
    'Superspreading event': Expiration((np.inf, np.inf, np.inf, np.inf)),
}


@dataclass(frozen=True)
class Activity:
    inhalation_rate: _VectorisedFloat
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

    def person_present(self, time):
        return self.presence.triggered(time)


@dataclass(frozen=True)
class InfectedPopulation(Population):
    #: The virus with which the population is infected.
    virus: Virus

    #: The type of expiration that is being emitted whilst doing the activity.
    expiration: _ExpirationBase

    def emission_rate_when_present(self) -> _VectorisedFloat:
        """
        The emission rate if the infected population is present.

        Note that the rate is not currently time-dependent.

        """
        # Emission Rate (infectious quantum / h)
        aerosols = self.expiration.aerosols(self.mask)

        ER = (self.virus.viral_load_in_sputum *
              self.activity.exhalation_rate *
              10 ** 6 *
              aerosols /
              self.virus.quantum_infectious_dose)

        # For superspreading event, where ejection_factor is infinite we fix the ER
        # based on Miller et al. (2020).
        if isinstance(aerosols, np.ndarray):
            ER[np.isinf(aerosols)] = 970
        elif np.isinf(aerosols):
            ER = 970

        return ER

    def individual_emission_rate(self, time) -> _VectorisedFloat:
        """
        The emission rate of a single individual in the population.

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

    @cached()
    def emission_rate(self, time) -> _VectorisedFloat:
        """
        The emission rate of the entire population.

        """
        return self.individual_emission_rate(time) * self.number


@dataclass(frozen=True)
class ConcentrationModel:
    room: Room
    ventilation: _VentilationBase
    infected: InfectedPopulation

    @property
    def virus(self):
        return self.infected.virus

    def infectious_virus_removal_rate(self, time: float) -> _VectorisedFloat:
        # Particle deposition on the floor
        vg = 1 * 10 ** -4
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h

        return k + self.virus.decay_constant(self.room.humidity
                    ) + self.ventilation.air_exchange(self.room, time)

    @cached()
    def _concentration_limit(self, time: float) -> _VectorisedFloat:
        """
        Provides a constant that represents the theoretical asymptotic 
        value reached by the concentration when time goes to infinity,
        if all parameters were to stay time-independent.
        """
        V = self.room.volume
        IVRR = self.infectious_virus_removal_rate(time)

        return (self.infected.emission_rate(time)) / (IVRR * V)

    @cached()
    def state_change_times(self):
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.

        """
        state_change_times = set()
        state_change_times.update(self.infected.presence.transition_times())
        state_change_times.update(self.ventilation.transition_times())

        return sorted(state_change_times)

    def last_state_change(self, time: float):
        """
        Find the most recent state change.

        """
        for change_time in self.state_change_times()[::-1]:
            if change_time < time:
                return change_time
        return 0

    def _next_state_change(self, time: float):
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

    def _is_interval_between_state_changes(self, start: float, stop: float) -> bool:
        """
        Check that the times start and stop are in-between two state
        changes of the concentration model (to ensure sure that all
        model parameters stay constant between start and stop).
        """
        return (self.last_state_change(stop) <= start)

    @cached()
    def concentration(self, time: float) -> _VectorisedFloat:
        """
        Virus quanta concentration, as a function of time.
        The formulas used here assume that all parameters (ventilation,
        emission rate) are constant between two state changes - only
        the value of these parameters at the next state change, are used.

        Note that time is not vectorised. You can only pass a single float
        to this method.
        """

        if time == 0:
            return 0.0
        next_state_change_time = self._next_state_change(time)
        IVRR = self.infectious_virus_removal_rate(next_state_change_time)
        concentration_limit = self._concentration_limit(next_state_change_time)

        t_last_state_change = self.last_state_change(time)
        concentration_at_last_state_change = self.concentration(t_last_state_change)

        delta_time = time - t_last_state_change
        fac = np.exp(-IVRR * delta_time)
        return concentration_limit * (1 - fac) + concentration_at_last_state_change * fac

    def integrated_concentration(self, start: float, stop: float) -> _VectorisedFloat:
        """
        Get the integrated concentration dose between the times start and stop.
        """
        state_change_times = self.state_change_times()
        req_start, req_stop = start, stop
        total_concentration = 0.
        for interval_start, interval_stop in zip(state_change_times[:-1], state_change_times[1:]):
            if req_start > interval_stop or req_stop < interval_start:
                continue
            # Clip the current interval to the requested range.
            start = max([interval_start, req_start])
            stop = min([interval_stop, req_stop])

            conc_start = self.concentration(start)

            next_conc_state = self._next_state_change(stop)
            conc_limit = self._concentration_limit(next_conc_state)
            IVRR = self.infectious_virus_removal_rate(next_conc_state)
            delta_time = stop - start
            total_concentration += (
                conc_limit * delta_time +
                (conc_limit - conc_start) * (np.exp(-IVRR*delta_time)-1) / IVRR
            )
        return total_concentration


@dataclass(frozen=True)
class ExposureModel:
    #: The virus concentration model which this exposure model should consider.
    concentration_model: ConcentrationModel

    #: The population of non-infected people to be used in the model.
    exposed: Population

    #: The number of times the exposure event is repeated (default 1).
    repeats: int = 1

    def quanta_exposure(self) -> _VectorisedFloat:
        """The number of virus quanta per meter^3."""
        exposure = 0.0

        for start, stop in self.exposed.presence.boundaries():
            exposure += self.concentration_model.integrated_concentration(start, stop)

        return exposure * self.repeats

    def infection_probability(self) -> _VectorisedFloat:
        exposure = self.quanta_exposure()

        inf_aero = (
            self.exposed.activity.inhalation_rate *
            (1 - self.exposed.mask.inhale_efficiency()) *
            exposure
        )

        # Probability of infection.
        return (1 - np.exp(-inf_aero)) * 100

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
