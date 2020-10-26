"""
This module is entirely in support of providing a convenient mutable counterpart
to frozen dataclasses. Significant effort went into to trying to use traitlets
for this purpose, but the need to define class-level attributes proved to be a
limitation that meant we could not mutate the state from one subclass to another
after the state was instantiated.

This module MUST not import other parts of cara as this would point at a
leaky abstraction.

"""
from contextlib import contextmanager
import dataclasses
import typing


Datamodel_T = typing.Type
dataclass_instance = typing.Any


class StateBuilder:
    def visit(self, field: dataclasses.Field):
        builder = self.resolve_builder(field)
        return builder(field.type)

    def resolve_builder(self, field: dataclasses.Field):
        method_name = [
            f'build_name_{field.name}',
            f'build_type_{field.type.__name__}',
        ]
        for name in method_name:
            method = getattr(self, name, None)
            if method is not None:
                return method
        return self.build_generic

    def build_generic(self, type_to_build: typing.Type):
        return DataclassInstanceState(type_to_build, state_builder=self)


class DataclassState:
    def __init__(self, state_builder=StateBuilder()):
        with self._object_setattr():
            self._state_builder = state_builder

    @contextmanager
    def _object_setattr(self):
        """
        For the lifetime of this contextmanager, don't do anything other than
        standard object.__setattr__ when setting attributes.

        """
        object.__setattr__(self, '_use_base_setattr', True)
        yield
        object.__setattr__(self, '_use_base_setattr', False)

    def dcs_instance(self):
        """
        Return the instance that this state represents. The instance returned
        is immutable, so it is advised to call this method each time that
        you want the instance so that it reflects the most up-to-date state.

        """
        pass

    def dcs_observe(self, callback: typing.Callable):
        """
        If any changes are made to the state, call the given callback.

        """
        pass

    @contextmanager
    def dcs_state_transaction(self):
        """
        For the lifetime of this context manager, do not fire observer
        notifications. If any notifications would have been fired during the
        lifetime of this context manager, then an event will be fired once
        exiting the context.

        """
        yield

    def dcs_update_from(self, data: dataclass_instance):
        """
        Update the state based on the values of the given dataclass instance.

        """
        pass

    def _dcs_set_value(self, attr_name, value):
        """
        Set the state of the given attribute to the given value.

        """

    def dcs_set_instance_type(self, instance_dataclass: Datamodel_T):
        """
        Update the current instance of the state to this type.

        Note: This currently wipes all downstream observers.

        """


class DataclassInstanceState(DataclassState):
    """
    Represents the state of a frozen dataclass.
    No type checking of the attributes is attempted.

    Setting the state can be done with:

        setattr(state, attr, value)

    Accessing the instance that this state represents can be done with:

        state.dcs_instance()

    Changing the type to a subclass of the base that this state represents can be done with:

        state.dcs_set_instance_type(ASubclassOfBase)

    """

    def __init__(self, dataclass: Datamodel_T, state_builder=StateBuilder()):
        super().__init__(state_builder=state_builder)

        # Note that the constructor does *not* insert any data by default. It
        # therefore doesn't build nested DataclassState instances when a dataclass contains another.
        # For that, use the build classmethod.
        if not dataclasses.is_dataclass(dataclass):
            raise TypeError("The given class is not a valid dataclass")
        if not isinstance(dataclass, type):
            raise TypeError("A dataclass type must be provided, not an instance of one")

        with self._object_setattr():
            #: The base instance which this state must support.
            self._base = dataclass
            #: The actual instance type that this state represents (i.e. may be a
            #: subclass of _base).
            self._instance_type = dataclass

            #: The instance of dataclass which this state represents. Undefined until
            #: sufficient data is provided.
            self._instance = None
            self._data = {}
            self._observers: typing.List[callable] = []
            self._state_builder = state_builder
            self._held_events = []
            self._hold_fire = False

        self.dcs_set_instance_type(dataclass)

    def __repr__(self):
        return f"<state for {self._instance_type.__name__}(**{self._instance_state()})>"

    def _instance_attrs(self):
        return [field.name for field in dataclasses.fields(self._instance_type)]

    def dcs_observe(self, callback: typing.Callable):
        self._observers.append(callback)

    @contextmanager
    def dcs_state_transaction(self):
        self._hold_fire = True
        yield
        self._hold_fire = False
        if self._held_events:
            self._held_events.clear()
            self._fire_observers()

    def dcs_update_from(self, data: dataclass_instance):
        with self.dcs_state_transaction():
            self.dcs_set_instance_type(data.__class__)
            for field in dataclasses.fields(data):
                attr = field.name
                current_value = self._data.get(attr, None)
                new_value = getattr(data, attr)
                if dataclasses.is_dataclass(field.type):
                    assert isinstance(current_value, DataclassState)
                    current_value.dcs_update_from(new_value)
                else:
                    self._data[attr] = new_value
            self._fire_observers()

    def _fire_observers(self):
        if self._hold_fire:
            self._held_events.append(True)
        else:
            self._instance = None
            for observer in self._observers:
                observer()

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass
        if name in self._data:
            return self._data[name]
        elif name in self._instance_attrs():
            raise ValueError(f"State not yet set for {name}")
        else:
            raise AttributeError(f"Attribute {name} does not exist on {self._instance_type.__name__}")

    def __setattr__(self, name, value):
        if name in self.__dict__ or self.__dict__.get('_use_base_setattr', True):
            return object.__setattr__(self, name, value)
        if name in self._instance_attrs():
            self._dcs_set_value(name, value)

    def _dcs_set_value(self, attr_name, value):
        valid_attrs = self._instance_attrs()
        if isinstance(value, DataclassState):
            # TODO: We need to check that the value is acceptable. (needs
            #  thinking about)
            # assert value._base ==
            pass
            # TODO: Inject some notifications here to tell any holding DataclassState
            #  instances that we've changed.

        if attr_name in valid_attrs:
            self._data[attr_name] = value
            self._fire_observers()
        else:
            raise AttributeError(f"No attribute {attr_name} on a {self._instance_type.__name__}")

    def dcs_set_instance_type(self, instance_dataclass: Datamodel_T):
        if not dataclasses.is_dataclass(instance_dataclass):
            raise TypeError("The given class is not a valid dataclass")
        if not issubclass(instance_dataclass, self._base):
            raise TypeError(f"The dataclass type provided ({instance_dataclass}) must be a subclass of the base ({self._base})")
        self._instance_type = instance_dataclass

        # TODO: It is possible to cut observer connections by clearing like this.
        self._data.clear()
        for field in dataclasses.fields(instance_dataclass):
            if dataclasses.is_dataclass(field.type):
                self._data[field.name] = self._state_builder.visit(field)
                self._data[field.name].dcs_observe(self._fire_observers)

    def _instance_state(self):
        # Note: this method should not validate that the args are complete or
        # overspecified.
        kwargs = {}
        for name, data in self._data.items():
            if isinstance(data, DataclassState):
                data = data._instance_state()
            kwargs[name] = data
        return kwargs

    def _instance_kwargs(self):
        # Note: this method should not validate that the args are complete or
        # overspecified.
        kwargs = {}
        for name, data in self._data.items():
            if isinstance(data, DataclassState):
                data = data.dcs_instance()
            kwargs[name] = data
        return kwargs

    def dcs_instance(self):
        if self._instance is None:
            # TODO: Check if we are able to create an instance with our data...
            self._instance = self._instance_type(**self._instance_kwargs())
        return self._instance


class DataclassStatePredefined(DataclassInstanceState):
    """
    Only a pre-defined selection of states for the given type are allowed.
    Selected by name (the keys in the dictionary).

    You can change the chosen state with:

        state.dcs_select(name)

    """
    def __init__(self,
                 dataclass: Datamodel_T,
                 choices: typing.Dict[typing.Hashable, dataclass_instance],
                 **kwargs,
                 ):
        super().__init__(dataclass=dataclass, **kwargs)

        with self._object_setattr():
            self._choices = choices
            self._selected = None
        # Pick the first choice until we know otherwise.
        self.dcs_select(list(choices.keys())[0])

    def dcs_select(self, name: typing.Hashable):
        if name not in self._choices:
            raise ValueError(f'The choice {name} is not valid. Possible options are {", ".join(self._choices)}')
        self._selected = name
        self._instance = self._choices[name]

    def dcs_instance(self):
        return self._choices[self._selected]

    def __repr__(self):
        return f"<state for {self._instance_type.__name__}. '{self._selected}' selected>"

    def _instance_state(self):
        return dataclasses.asdict(self.dcs_instance())

    def _instance_kwargs(self):
        return dataclasses.asdict(self.dcs_instance())


class DataclassStateNamed(DataclassState):
    """
    A collection of instances of the given type, switchable by name, but each
    instance is still mutable.

    """
    def __init__(self,
                 states: typing.Dict[typing.Hashable, DataclassState],
                 **kwargs
                 ):
        # TODO: This is effectively a container type. We shouldn't use the standard constructor for this.
        enabled = list(states.keys())[0]
        t = states[enabled]
        super().__init__(**kwargs)

        with self._object_setattr():
            self._states = states.copy()
            self._selected = None
        # Pick the first choice until we know otherwise.
        self.dcs_select(enabled)

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass
        return getattr(self._selected_state(), name)
        # if name in self._data:
        #     return self._data[name]
        # elif name in self._instance_attrs():
        #     raise ValueError(f"State not yet set for {name}")
        # else:
        #     raise AttributeError(f"Attribute {name} does not exist on {self._instance_type.__name__}")

    def __setattr__(self, name, value):
        if name in self.__dict__ or self.__dict__.get('_use_base_setattr', True):
            return object.__setattr__(self, name, value)
        setattr(self._selected_state(), name, value)

    def dcs_select(self, name: typing.Hashable):
        if name not in self._states:
            raise ValueError(f'The choice {name} is not valid. Possible options are {", ".join(self._states)}')
        self._selected = name
        self._selected_state()._fire_observers()

    def _selected_state(self):
        return self._states[self._selected]

    def dcs_instance(self):
        return self._selected_state().dcs_instance()

    def __repr__(self):
        return f"<state for {self._instance_type.__name__}. Holding {len(self._states)} state(s). '{self._selected}' selected>"

    def dcs_observe(self, callback: typing.Callable):
        # Note there is no way to observe the selected state change currently.
        # You can only watch for the individual selected states being changed.
        for state in self._states.values():
            state.dcs_observe(callback)

    def dcs_update_from(self, data: dataclass_instance):
        return self._selected_state().dcs_update_from(data)

    def dcs_set_instance_type(self, instance_dataclass: Datamodel_T):
        return self._selected_state().dcs_set_instance_type(instance_dataclass)

    @contextmanager
    def dcs_state_transaction(self):
        orig = [s._hold_fire for s in self._states.values()]
        for s in self._states.values():
            s._hold_fire = True
        yield
        for orig_hold, s in zip(orig, self._states.values()):
            s._hold_fire = orig_hold
            if s._held_events:
                s._held_events.clear()
                s._fire_observers()
