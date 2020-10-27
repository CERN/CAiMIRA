import functools
import numpy as np
import typing
from abc import abstractmethod


from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    # The total volume of the room
    volume: int


@dataclass(frozen=True)
class Interval:
    """
    Represents a collection of times in which a "thing" happens.

    The "thing" may be when an action is taken, such as opening a window, or
    entering a room.

    """
    def triggered(self, time: float) -> bool:
        """Whether the given time falls inside this interval."""
        return False

    def boundaries(self) -> typing.Set[float]:
        """Returns the edges of this interval."""
        return set()


@dataclass(frozen=True)
class PeriodicInterval(Interval):
    #: How often does the interval occur.
    period: int

    #: How long does the interval occur for.
    #: A value greater than :data:`period` signifies the event is permanently
    #: occurring, a value of 0 signifies that the event never happens.
    duration: int

    def triggered(self, time: float) -> bool:
        period = self.period / 60.
        duration = self.duration / 60.
        return (time % period) >= (period - duration)

    def boundaries(self) -> typing.Set[float]:
        state_changes = set()
        period_h = self.period / 60
        duration_h = self.duration / 60
        # The current implementation starts at the end of the first period, not at 0.
        start = period_h
        # Take as many steps as we need to get to a full day.
        for i in np.arange(start, 24, period_h):
            state_changes.add(i)
            if duration_h < period_h:
                state_changes.add(i - duration_h)

        return state_changes


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

    @abstractmethod
    def air_exchange(self, room: Room, time: float) -> float:
        """
        Returns the rate at which air is being exchanged in the given room per
        cubic meter at a given time (in hours).

        """
        return 0.

    def times_of_state_change(self) -> typing.Set[float]:
        """
        Returns the times at which a change in ventilation occurs.

        """
        return self.active.boundaries()


@dataclass(frozen=True)
class WindowOpening(Ventilation):
    #: The interval in which the window is open.
    active: Interval

    inside_temp: float   #: The temperature inside the room (Kelvin)
    outside_temp: float   #: The temperature outside of the window (Kelvin)

    window_height: float   #: The height of the window

    opening_length: float   #: The length of the opening-gap when the window is open

    cd_b: float = 0.6   #: Discharge coefficient: what portion effective area is used to exchange air (0 <= cd_b <= 1)

    def air_exchange(self, room: Room, time: float) -> float:
        # If the window is shut, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.

        temp_delta = abs(self.inside_temp - self.outside_temp) / self.outside_temp
        root = np.sqrt(9.81 * self.window_height * temp_delta)

        return (3600 / (3 * room.volume)) * self.cd_b * self.window_height * self.opening_length * root


@dataclass(frozen=True)
class HEPAFilter(Ventilation):
    #: The interval in which the HEPA filter is operating.
    active: Interval

    q_air_mech: float   #: The rate at which the HEPA exchanges air (when switched on)

    def air_exchange(self, room: Room, time: float) -> float:
        # If the HEPA is off, no air is being exchanged.
        if not self.active.triggered(time):
            return 0.

        return self.q_air_mech / room.volume


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
        for i, (diameter, factor) in enumerate(zip(self.particle_sizes, self.ejection_factor)):
            contribution = volume(diameter) * factor
            if i >= 2:
                # TODO: It is probably the case that this term comes from the
                #  particle diameter, rather than arbitrary position in a sequence...
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
    #: A sequence of times (start, stop), in hours, that the infected person
    #: is present. The flattened list of times must be strictly monotonically
    #: increasing.
    present_times: typing.Tuple[typing.Tuple[float, float], ...]
    mask: Mask
    activity: Activity
    expiration: Expiration

    def person_present(self, time):
        for start, end in self.present_times:
            if start <= time <= end:
                return True
        return False

    def start_end_of_presence(self, time) -> typing.Tuple[float, float]:
        """
        Find the most recent start (and associated) end-time (even if the
        given time is after the end-point) given a time.

        """
        for start, end in self.present_times[::-1]:
            if time > start:
                return start, end
        return start, end

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
    def collect_time_state_changes(self):
        """
        All time dependent entities on this model must provide information about
        the times at which their state changes.

        """
        state_change_times = set()
        for start, end in self.infected.present_times:
            state_change_times.add(start)
            state_change_times.add(end)
        state_change_times.update(self.ventilation.times_of_state_change())
        return sorted(state_change_times)

    def last_state_change(self, time: float):
        """
        Find the most recent state change.

        """
        for change_time in self.collect_time_state_changes()[::-1]:
            if time >= change_time:
                return change_time
        return 0

    @functools.lru_cache()
    def concentration(self, time: float) -> float:
        t = time
        IVRR = self.infectious_virus_removal_rate(time)
        V = self.room.volume
        Ni = self.infected_occupants
        ER = self.infected.emission_rate(time)
        if t == 0:
            return 0.0
        t_last_state_change = self.last_state_change(time)
        if t != t_last_state_change:
            concentration_at_last_state_change = self.concentration(t_last_state_change)
        else:
            concentration_at_last_state_change = self.concentration(t - 0.0001)

        fac = np.exp(IVRR * (t_last_state_change - t))
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
        for start, stop in self.infected.present_times:
            exposure += (integrate(self.concentration, start, stop))

        inf_aero = (
            self.exposed_activity.inhalation_rate *
            (1 - self.infected.mask.η_inhale) *
            exposure
        )

        # Probability of infection.
        return (1 - np.exp(-inf_aero)) * 100
