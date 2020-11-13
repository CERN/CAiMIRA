import dataclasses

from cara.dataclass_utils import nested_replace


@dataclasses.dataclass(frozen=True)
class Four:
    four: float


@dataclasses.dataclass(frozen=True)
class Two:
    three: int
    four: Four


@dataclasses.dataclass(frozen=True)
class One:
    one: int
    two: Two



def test_nested_replace():
    inst = One(1, two=Two(3, Four(4)))
    new_inst = nested_replace(inst, {'two.four': Four(5)})
    assert new_inst == One(1, two=Two(3, Four(5)))
