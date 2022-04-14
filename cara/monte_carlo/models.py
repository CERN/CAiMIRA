import copy
import dataclasses
import sys
import typing

import cara.models

from .sampleable import SampleableDistribution, _VectorisedFloatOrSampleable


_ModelType = typing.TypeVar('_ModelType')


class MCModelBase(typing.Generic[_ModelType]):
    """
    A model base class for monte carlo types.

    This base class is essentially a declarative description of a cara.models
    model with a :meth:`.build_model` method to generate an appropriate
    ``cara.models` model instance on demand.

    """
    _base_cls: typing.Type[_ModelType]

    @classmethod
    def _to_vectorized_form(cls, item, size):
        if isinstance(item, SampleableDistribution):
            return item.generate_samples(size)
        elif isinstance(item, MCModelBase):
            # Recurse into other MCModelBase instances by calling their
            # build_model method.
            return item.build_model(size)
        elif isinstance(item, tuple):
            return tuple(cls._to_vectorized_form(sub, size) for sub in item)
        else:
            return item

    def build_model(self, size: int) -> _ModelType:
        """
        Turn this MCModelBase subclass into a cara.model Model instance
        from which you can then run the model.

        """
        kwargs = {}
        for field in dataclasses.fields(self._base_cls):
            attr = getattr(self, field.name)
            kwargs[field.name] = self._to_vectorized_form(attr, size)
        return self._base_cls(**kwargs)  # type: ignore


def _build_mc_model(model: _ModelType) -> typing.Type[MCModelBase[_ModelType]]:
    """
    Generate a new MCModelBase subclass for the given cara.models model.

    """
    fields = []
    for field in dataclasses.fields(model):
        # Note: deepcopy not needed here as we aren't mutating entities beyond
        # the top level.
        new_field = copy.copy(field)
        if field.type is cara.models._VectorisedFloat:  # noqa
            new_field.type = _VectorisedFloatOrSampleable   # type: ignore

        field_type: typing.Any = new_field.type

        if getattr(field_type, '__origin__', None) in [typing.Union, typing.Tuple]:
            # It is challenging to generalise this code, so we provide specific transformations,
            # and raise for unforseen cases.
            if new_field.type == typing.Tuple[cara.models._VentilationBase, ...]:
                VB = getattr(sys.modules[__name__], "_VentilationBase")
                field_type = typing.Tuple[typing.Union[cara.models._VentilationBase, VB], ...]
            elif new_field.type == typing.Tuple[cara.models._ExpirationBase, ...]:
                EB = getattr(sys.modules[__name__], "_ExpirationBase")
                field_type = typing.Tuple[typing.Union[cara.models._ExpirationBase, EB], ...]
            elif new_field.type == typing.Tuple[cara.models.SpecificInterval, ...]:
                SI = getattr(sys.modules[__name__], "SpecificInterval")
                field_type = typing.Tuple[typing.Union[cara.models.SpecificInterval, SI], ...]
            else:
                # Check that we don't need to do anything with this type.
                for item in new_field.type.__args__:
                    if getattr(item, '__module__', None) == 'cara.models':
                        raise ValueError(
                            f"unsupported type annotation transformation required for {new_field.type}")
        elif field_type.__module__ == 'cara.models':
            mc_model = getattr(sys.modules[__name__], new_field.type.__name__)
            field_type = typing.Union[new_field.type, mc_model]

        fields.append((new_field.name, field_type, new_field))

    bases = []
    # Update the inheritance/based to use the new MC classes, rather than the cara.models ones.
    for model_base in model.__bases__:  # type: ignore
        if model_base is object:
            bases.append(MCModelBase)
        else:
            mc_model = getattr(sys.modules[__name__], model_base.__name__)
            bases.append(mc_model)

    cls = dataclasses.make_dataclass(
        model.__name__,  # type: ignore
        fields,  # type: ignore
        bases=tuple(bases),  # type: ignore
        namespace={'_base_cls': model},
        # This thing can be mutable - the calculations live on
        # the wrapped class, not on the MCModelBase.
        frozen=False,
    )
    # Update the module of the generated class to be this one. Without this the
    # module will be "types".
    cls.__module__ = __name__
    return cls


_MODEL_CLASSES = [
    cls for cls in vars(cara.models).values()
    if dataclasses.is_dataclass(cls)
]


# Inject the runtime generated MC types into this module.
for _model in _MODEL_CLASSES:
    setattr(sys.modules[__name__], _model.__name__, _build_mc_model(_model))


# Make sure that each of the models is imported if you do a ``import *``.
__all__ = [_model.__name__ for _model in _MODEL_CLASSES] + ["MCModelBase"]
