import dataclasses
from dataclasses import dataclass
import typing
from unittest.mock import Mock

import pytest

from cara import state


@dataclass
class DCSimple:
    attr1: str
    attr2: int


@dataclass
class DCAnother:
    attr3: float


@dataclass
class DCSimpleSubclass(DCSimple):
    attr3: float


@dataclass
class DCOverrideSubclass(DCSimple):
    attr1: float  # type: ignore


@dataclass
class DCClassVar(DCSimple):
    a_class_var: typing.ClassVar[int]


@dataclass
class DCRecursive(DCSimple):
    simple: DCSimple


@dataclass
class DCContainer:
    contained: typing.Tuple[DCSimple, ...]


@dataclass
class DCNested:
    simple: DCSimple
    others: typing.List[DCSimple]
    vanilla: str = 'Default'


@dataclass
class DCNestedDeep:
    child: DCNested


@pytest.fixture
def dc_simple():
    return DCSimple


def test_DCS_construct():
    s = state.DataclassInstanceState(DCSimple)
    assert repr(s) == '<state for DCSimple(**{})>'

    with pytest.raises(TypeError, match=r"A dataclass type must be provided, not an instance of one"):
        state.DataclassInstanceState(DCSimple('', 1))

    with pytest.raises(TypeError, match="The given class is not a valid dataclass"):
        state.DataclassInstanceState(None)


def test_DCS_construct_nested():
    s = state.DataclassInstanceState(DCNested)
    assert repr(s) == "<state for DCNested(**{'simple': {}})>"


@pytest.mark.xfail
def test_DCS_subclass():
    s = state.DataclassInstanceState(DCSimple)
    s.dcs_set_instance_type(DCSimpleSubclass)
    s.set('attr3', 3.14)
    assert s._instance_kwargs() == {'attr3': 3.14}
    s.dcs_set_instance_type(DCSimple)
    # TODO: Make this fail.
    assert s._instance_kwargs() == {}


def test_DCS_setattr():
    s = state.DataclassInstanceState(DCSimple)
    s.attr1 = 'Hello world'
    assert s._instance_kwargs() == {'attr1': 'Hello world'}


@pytest.mark.xfail
def test_DCS_type_check():
    s = state.DataclassInstanceState(DCSimple)
    with pytest.raises(TypeError):
        # TODO: Should we make this fail? It involves type-checking / validation.
        s.attr1 = 1


def test_DCS_update_from_instance():
    s = state.DataclassInstanceState(DCSimple)
    s.dcs_update_from(DCSimple('a1', 2))
    assert s._instance_type == DCSimple
    assert s._instance_kwargs() == {'attr1': 'a1', 'attr2': 2}


def test_DCS_update_from_instance_subclass():
    s = state.DataclassInstanceState(DCSimple)
    s.dcs_update_from(DCSimpleSubclass('a1', 2, 3.14))
    assert s._instance_type == DCSimpleSubclass
    assert s._instance_kwargs() == {'attr1': 'a1', 'attr2': 2, 'attr3': 3.14}


def test_DCS_update_from_instance_nested():
    s = state.DataclassInstanceState(DCNested)
    nested = DCNested(DCSimpleSubclass('a1', 2, 3.14), [])
    s.dcs_update_from(nested)
    assert s.simple.dcs_instance() == nested.simple
    assert s.dcs_instance() == nested


def test_observe_instance_nested():
    top_level = Mock()
    nested = Mock()

    s = state.DataclassInstanceState(DCNested)

    s.dcs_observe(top_level)
    s.simple.dcs_observe(nested)

    s.simple.attr1 = 'something new'
    top_level.assert_called_with()
    nested.assert_called_with()

    top_level.reset_mock()
    nested.reset_mock()
    s.vanilla = 'something new'
    top_level.assert_called_with()
    nested.assert_not_called()


def test_observe_instance_container__container():
    top_level = Mock()
    nested = Mock()

    dc1 = DCSimple(attr1='foo', attr2=2)
    dc2 = DCSimple(attr1='bar', attr2=3)
    s = state.DataclassInstanceState(DCContainer)
    u = DCContainer(contained=(dc1, dc2))
    s.dcs_update_from(u)

    s.dcs_observe(top_level)
    s.contained[0].dcs_observe(nested)

    s.contained[0].attr1 = 'something new'
    nested.assert_called_with()
    top_level.assert_called_with()
    first = s.dcs_instance().contained[0]
    assert isinstance(first, DCSimple)
    assert first.attr1 == 'something new'
    assert first.attr2 == 2


def test_DCS_predefined():
    opt1 = DCSimple('a', 1)
    opt2 = DCSimpleSubclass('b', 2, 3.14)
    s = state.DataclassStatePredefined(
        DCSimple, {'option 1': opt1, 'option 2': opt2}
    )
    assert s._selected == 'option 1'
    # TODO: This should fail.
    s.attr1 = 'can I set it?'
    assert s.dcs_instance() == opt1

    s.dcs_select('option 2')
    assert s.dcs_instance() == opt2

    assert repr(s) == "<state for DCSimple. 'option 2' selected>"

    # TODO: This should fail too.
    s.dcs_update_from(opt1)
    assert s.dcs_instance() == opt2

    observer = Mock()
    s.dcs_observe(observer)
    s.dcs_select('option 1')
    observer.assert_called_once_with()


def test_DCS_named():
    opt1 = DCSimpleSubclass('a', 1, 3.14)
    opt2 = DCAnother(4.2)
    s = state.DataclassStateNamed({
        # Entirely different types possible.
        'option 1': state.DataclassInstanceState(DCSimple),
        'option 2': state.DataclassInstanceState(DCAnother),
    })
    assert s._selected == 'option 1'

    with pytest.raises(ValueError):
        s.dcs_select('option 3')

    with pytest.raises(TypeError):
        # Not initialised all the values yet...
        s.dcs_instance()

    opt1_observer = Mock()
    s.dcs_observe(opt1_observer)

    s.dcs_update_from(opt1)
    assert s.dcs_instance() == opt1

    opt1_observer.assert_called_once_with()
    opt1_observer.reset_mock()

    with pytest.raises(TypeError):
        s.dcs_update_from(opt2)

    s.dcs_select('option 2')
    opt1_observer.assert_called_once_with()
    opt1_observer.reset_mock()

    s.dcs_update_from(opt2)
    assert s.dcs_instance() == opt2
    # We can't observe individual states directly.
    opt1_observer.assert_called_once_with()

    # Roll back to option 1.
    s.dcs_select('option 1')
    opt1_observer.reset_mock()

    with s.dcs_state_transaction():
        s.dcs_select('option 2')
        s.dcs_update_from(opt2)
    # TODO: Currently calls twice.
    # opt1_observer.assert_called_once_with()
    opt1_observer.reset_mock()

    assert s.dcs_instance() == opt2

    s.dcs_select('option 1')
    assert s.dcs_instance() == opt1

    # TODO: This should fail.
    s.foo = 10


def test_DCS_non_dataclass_attrs():
    val = DCClassVar('a', 1)
    s = state.DataclassInstanceState(DCSimple)
    s.dcs_update_from(val)
    s.dcs_instance() == val
