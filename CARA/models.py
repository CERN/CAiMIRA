import functools
import numpy as np
import typing


from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    volume: int


@dataclass(frozen=True)
class Ventilation:
    QairNat: float = 514.74

    def air_change_per_hour(self, room: Room):
        return self.QairNat / room.volume


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
        return self.η_exhale - (self.η_exhale * self.η_leaks)


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

    @property
    def infectious_virus_removal_rate(self):
        # Particle deposition on the floor
        vg = 1 * 10 ** -4
        # Height of the emission source to the floor - i.e. mouth/nose (m)
        h = 1.5
        # Deposition rate (h^-1)
        k = (vg * 3600) / h

        return k + self.virus.decay_constant + self.ventilation.air_change_per_hour(self.room)

    @functools.lru_cache()
    def concentration(self, time: float) -> float:
        t = time
        IVRR = self.infectious_virus_removal_rate
        V = self.room.volume
        Ni = self.infected_occupants
        ER = self.infected.emission_rate(time)
        t0, t1 = self.infected.start_end_of_presence(time)

        if t == 0:
            return 0.0
        elif t0 < t <= t1:
            # Concentration while infected present.
            init_concentration = self.concentration(t0)
            time_present = t - t0
            fac = np.exp(-IVRR * time_present)
            return ((ER + Ni) / (IVRR * V)) * (1 - fac) + init_concentration * fac
        else:
            # Concentration while infected not present.
            end_concentration = self.concentration(t1)
            return (end_concentration + ((np.exp(IVRR * t1) - 1) * end_concentration)) * np.exp(-IVRR * t)
