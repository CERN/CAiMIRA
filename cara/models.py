import functools
import numpy as np
import typing
from abc import abstractmethod


from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    # The total volume of the room
    volume: float


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
    def boundaries(self) -> typing.Tuple[typing.Tuple[float, float], ...]:
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
    present_times: typing.Tuple[typing.Tuple[float, float], ...]

    def boundaries(self):
        return self.present_times


@dataclass(frozen=True)
class PeriodicInterval(Interval):
    #: How often does the interval occur (minutes).
    period: int

    #: How long does the interval occur for (minutes).
    #: A value greater than :data:`period` signifies the event is permanently
    #: occurring, a value of 0 signifies that the event never happens.
    duration: int

    def boundaries(self) -> typing.Tuple[typing.Tuple[float, float], ...]:
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
    values: typing.Tuple[float, ...]

    def __post_init__(self):
        if len(self.transition_times) != len(self.values)+1:
            raise ValueError("transition_times should contain one more element than values")
        if tuple(sorted(set(self.transition_times))) != self.transition_times:
            raise ValueError("transition_times should not contain duplicated elements and should be sorted")

    def value(self,time) -> float:
        if time <= self.transition_times[0]:
            return self.values[0]
        if time > self.transition_times[-1]:
            return self.values[-1]

        for t1,t2,value in zip(self.transition_times[:-1],
                               self.transition_times[1:],self.values):
            if time > t1 and time <= t2:
                return value

    def interval(self) -> Interval:
        # build an Interval object
        present_times = []
        for t1,t2,value in zip(self.transition_times[:-1],
                               self.transition_times[1:],self.values):
            if value:
                present_times.append((t1,t2))
        return SpecificInterval(present_times=present_times)

    def refine(self,refine_factor=10):
        # build a new PiecewiseConstant object with a refined mesh,
        # using a linear interpolation in-between the initial mesh points
        refined_times = np.linspace(self.transition_times[0],self.transition_times[-1],
                                    (len(self.transition_times)-1)*refine_factor+1)
        return PiecewiseConstant(tuple(refined_times),
                tuple(np.interp(refined_times[:-1],self.transition_times,
                                self.values+(self.values[-1],) ) ) )


@dataclass(frozen=True)
class Ventilation:
    """
    Represents a mechanism by which air can be exchanged (replaced/filtered)
    in a time dependent manner.

    The nature of the various air exchange schemes means that it is expected
    for subclasses of Ventilation to exist. Known subclasses include
    WindowOpening for window based air exchange, and HEPAFilter, for
    mechanical air exchange through a filter.

    """
    #: The times at which the air exchange is taking place.
    active: Interval

    def transition_times(self) -> typing.Set[float]:
        return self.active.transition_times()

    @abstractmethod
    def air_exchange(self, room: Room, time: float) -> float:
        """
        Returns the rate at which air is being exchanged in the given room
        at a given time (in hours).

        Note that whilst the time is known inside this function, it may not
        be used to vary the result unless the specific time used is declared
        as part of a state change in the interval (e.g. when air_exchange == 0).

        """
        return 0.


@dataclass(frozen=True)
class MultipleVentilation:
    """
    Represents a mechanism by which air can be exchanged (replaced/filtered)
    in a time dependent manner.

    Group together different sources of ventilations.

    """
    ventilations: typing.Tuple[Ventilation, ...]

    def transition_times(self) -> typing.Set[float]:
        transitions = set()
        for ventilation in self.ventilations:
            transitions.update(ventilation.transition_times())
        return transitions

    @abstractmethod
    def air_exchange(self, room: Room, time: float) -> float:
        """
        Returns the rate at which air is being exchanged in the given room 
        at a given time (in hours).
        """
        return sum([ventilation.air_exchange(room,time)
                    for ventilation in self.ventilations])


@dataclass(frozen=True)
class WindowOpening(Ventilation):
    #: The interval in which the window is open.
    active: Interval

    #: The temperature inside the room (Kelvin).
    inside_temp: PiecewiseConstant

    #: The temperature outside of the window (Kelvin).
    outside_temp: PiecewiseConstant

    #: The height of the window.
    window_height: float

    #: The length of the opening-gap when the window is open
    opening_length: float

    #: The number of windows of the given dimensions.
    number_of_windows: int = 1

    #: Discharge coefficient: what portion effective area is
    #: used to exchange air (0 <= cd_b <= 1)
    cd_b: float = 0.6

    def transition_times(self) -> typing.Set[float]:
        transitions = super().transition_times()
        transitions.update(self.inside_temp.transition_times)
        transitions.update(self.outside_temp.transition_times)
        return transitions

    def air_exchange(self, room: Room, time: float) -> float:
        # If the window is shut, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.

        inside_temp = self.inside_temp.value(time)
        outside_temp = self.outside_temp.value(time)

        # Reminder, no dependence on time in the resulting calculation.
        temp_delta = abs(inside_temp - outside_temp) / outside_temp
        root = np.sqrt(9.81 * self.window_height * temp_delta)
        window_area = self.window_height * self.opening_length * self.number_of_windows
        return (3600 / (3 * room.volume)) * self.cd_b * window_area * root


@dataclass(frozen=True)
class HEPAFilter(Ventilation):
    #: The interval in which the HEPA filter is operating.
    active: Interval

    #: The rate at which the HEPA exchanges air (when switched on)
    # in m^3/h
    q_air_mech: float

    def air_exchange(self, room: Room, time: float) -> float:
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
    q_air_mech: float

    def air_exchange(self, room: Room, time: float) -> float:
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
    air_exch: float

    def air_exchange(self, room: Room, time: float) -> float:
        # No dependence on the room volume.
        # If off, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.
        # Reminder, no dependence on time in the resulting calculation.
        return self.air_exch


@dataclass(frozen=True)
class Virus:
    #: Biological decay (inactivation of the virus in air)
    halflife: float

    #: RNA copies  / mL
    viral_load_in_sputum: float

    #: Ratio between infectious aerosols and dose to cause infection.
    coefficient_of_infectivity: float

    #: Pre-populated examples of Viruses.
    types: typing.ClassVar[typing.Dict[str, "Virus"]]

    @property
    def decay_constant(self):
        # Viral inactivation per hour (h^-1)
        return np.log(2) / self.halflife


Virus.types = {
    'SARS_CoV_2': Virus(
        halflife=1.1,
        viral_load_in_sputum=10e8,
        # No data on coefficient for SARS-CoV-2 yet.
        # It is somewhere between 0.001 and 0.01 to have a 50% chance
        # to cause infection. i.e. 1000 or 100 SARS-CoV viruses to cause infection.
        coefficient_of_infectivity=0.02,
    ),
}


@dataclass(frozen=True)
class Mask:
    #: Filtration efficiency. (In %/100)
    η_exhale: float

    #: Leakage through side of masks.
    η_leaks: float

    #: Filtration efficiency of masks when inhaling.
    η_inhale: float

    particle_sizes: typing.Tuple[float] = (0.8e-4, 1.8e-4, 3.5e-4, 5.5e-4)  # In cm.

    #: Pre-populated examples of Masks.
    types: typing.ClassVar[typing.Dict[str, "Mask"]]

    @property
    def exhale_efficiency(self):
        # Overall efficiency with the effect of the leaks for aerosol emission
        #  Gammaitoni et al (1997)
        return self.η_exhale * (1 - self.η_leaks)


Mask.types = {
    'No mask': Mask(0, 0, 0),
    'Type I': Mask(
        η_exhale=0.95,
        η_leaks=0.15,  # (Huang 2007)
        η_inhale=0.3,  # (Browen 2010)
    ),
}


@dataclass(frozen=True)
class Expiration:
    ejection_factor: typing.Tuple[float, float, float, float]
    particle_sizes: typing.Tuple[float, float, float, float] = (0.8e-4, 1.8e-4, 3.5e-4, 5.5e-4)  # In cm.

    #: Pre-populated examples of Expiration.
    types: typing.ClassVar[typing.Dict[str, "Expiration"]]

    def aerosols(self, mask: Mask):
        def volume(diameter):
            return (4 * np.pi * (diameter/2)**3) / 3
        total = 0
        for diameter, factor in zip(self.particle_sizes, self.ejection_factor):
            contribution = volume(diameter) * factor
            if diameter >= 3e-4:
                contribution = contribution * (1 - mask.exhale_efficiency)
            total += contribution
        return total


Expiration.types = {
    'Breathing': Expiration((0.084, 0.009, 0.003, 0.002)),
    'Whispering': Expiration((0.11, 0.014, 0.004, 0.002)),
    'Talking': Expiration((0.236, 0.068, 0.007, 0.011)),
    'Unmodulated Vocalization': Expiration((0.751, 0.139, 0.0139, 0.059)),
    'Superspreading event': Expiration((np.inf, np.inf, np.inf, np.inf)),
}


@dataclass(frozen=True)
class Activity:
    inhalation_rate: float
    exhalation_rate: float

    #: Pre-populated examples of activities.
    types: typing.ClassVar[typing.Dict[str, "Activity"]]


Activity.types = {
    'Resting': Activity(0.49, 0.49),
    'Seated': Activity(0.54, 0.54),
    'Light exercise': Activity(1.38, 1.38),
    'Moderate exercise': Activity(2.35, 2.35),
    'Heavy exercise': Activity(3.30, 3.30),
}


@dataclass(frozen=True)
class InfectedPerson:
    virus: Virus
    #: The times in which the person is in the room.
    presence: Interval
    mask: Mask
    activity: Activity
    expiration: Expiration

    def person_present(self, time):
        return self.presence.triggered(time)

    @functools.lru_cache()
    def emission_rate(self, time) -> float:
        # Note: The original model avoids time dependence on the emission rate
        # at the cost of implementing a piecewise (on time) concentration function.
        if not self.person_present(time):
            return 0

        # Emission Rate (infectious quantum / h)
        aerosols = self.expiration.aerosols(self.mask)
        if np.isinf(aerosols):
            # A superspreading event. Miller et al. (2020)
            ER = 970
        else:
            ER = (self.virus.viral_load_in_sputum *
                  self.virus.coefficient_of_infectivity *
                  self.activity.exhalation_rate *
                  10**6 *
                  aerosols)
        return ER


@dataclass(frozen=True)
class Model:
    room: Room
    ventilation: Ventilation
    infected: InfectedPerson
    infected_occupants: int
    exposed_occupants: int
    exposed_activity: Activity

    @property
    def virus(self):
        return self.infected.virus

    def infectious_virus_removal_rate(self, time: float) -> float:
        # Particle deposition on the floor
        vg = 1 * 10 ** -4
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h

        return k + self.virus.decay_constant + self.ventilation.air_exchange(self.room, time)

    @functools.lru_cache()
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

    @functools.lru_cache()
    def concentration(self, time: float) -> float:
        if time == 0:
            return 0.0
        IVRR = self.infectious_virus_removal_rate(time)
        V = self.room.volume
        Ni = self.infected_occupants
        ER = self.infected.emission_rate(time)

        t_last_state_change = self.last_state_change(time)
        concentration_at_last_state_change = self.concentration(t_last_state_change)

        delta_time = time - t_last_state_change
        fac = np.exp(-IVRR * delta_time)
        concentration_limit = (ER * Ni) / (IVRR * V)
        return concentration_limit * (1 - fac) + concentration_at_last_state_change * fac

    def infection_probability(self):
        # Infection probability
        # Probability of COVID-19 Infection

        exposure = 0.0  # q/m3*h

        def integrate(fn, start, stop):
            values = np.linspace(start, stop)
            return np.trapz([fn(v) for v in values], values)

        # TODO: Have this for exposed not infected.
        for start, stop in self.infected.presence.boundaries():
            exposure += (integrate(self.concentration, start, stop))

        inf_aero = (
            self.exposed_activity.inhalation_rate *
            (1 - self.infected.mask.η_inhale) *
            exposure
        )

        # Probability of infection.
        return (1 - np.exp(-inf_aero)) * 100
