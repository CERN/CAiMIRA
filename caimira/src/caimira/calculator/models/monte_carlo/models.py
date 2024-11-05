import copy
import dataclasses
import sys
import typing

from caimira.calculator.models import models

from .sampleable import SampleableDistribution, _VectorisedFloatOrSampleable

_ModelType = typing.TypeVar('_ModelType')
dataclass_instance = typing.Any

class MCModelBase(typing.Generic[_ModelType]):
    """
    A model base class for monte carlo types.

    This base class is essentially a declarative description of a caimira.models
    model with a :meth:`.build_model` method to generate an appropriate
    ``caimira.models` model instance on demand.

    """
    _base_cls: typing.Type[dataclass_instance]

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
        Turn this MCModelBase subclass into a caimira.model Model instance
        from which you can then run the model.

        """
        kwargs = {}
        for field in dataclasses.fields(self._base_cls):
            attr = getattr(self, field.name)
            kwargs[field.name] = self._to_vectorized_form(attr, size)
        return self._base_cls(**kwargs)


def _build_mc_model(model: dataclass_instance) -> typing.Type[MCModelBase[_ModelType]]:
    """
    Generate a new MCModelBase subclass for the given caimira.models model.

    """
    fields = []
    for field in dataclasses.fields(model):
        # Note: deepcopy not needed here as we aren't mutating entities beyond
        # the top level.
        new_field = copy.copy(field)
        if field.type is models._VectorisedFloat:  # noqa
            new_field.type = _VectorisedFloatOrSampleable   # type: ignore

        field_type: typing.Any = new_field.type

        if getattr(field_type, '__origin__', None) in [typing.Union, typing.Tuple]:
            # It is challenging to generalise this code, so we provide specific transformations,
            # and raise for unforseen cases.
            if new_field.type == typing.Tuple[models._VentilationBase, ...]:
                VB = getattr(sys.modules[__name__], "_VentilationBase")
                field_type = typing.Tuple[typing.Union[models._VentilationBase, VB], ...]
            elif new_field.type == typing.Tuple[models._ExpirationBase, ...]:
                EB = getattr(sys.modules[__name__], "_ExpirationBase")
                field_type = typing.Tuple[typing.Union[models._ExpirationBase, EB], ...]
            elif new_field.type == typing.Tuple[models.SpecificInterval, ...]:
                SI = getattr(sys.modules[__name__], "SpecificInterval")
                field_type = typing.Tuple[typing.Union[models.SpecificInterval, SI], ...]

            elif new_field.type == typing.Union[int, models.IntPiecewiseConstant]:
                IPC = getattr(sys.modules[__name__], "IntPiecewiseConstant")
                field_type = typing.Union[int, models.IntPiecewiseConstant, IPC]
            elif new_field.type == typing.Union[models.Interval, None]:
                I = getattr(sys.modules[__name__], "Interval")
                field_type = typing.Union[None, models.Interval, I]

            else:
                # Check that we don't need to do anything with this type.
                if hasattr(new_field.type, "__args__"):
                    for item in new_field.type.__args__:
                        if getattr(item, '__module__', None) == 'source.models.models':
                            raise ValueError(
                                f"unsupported type annotation transformation required for {new_field.type}")
        elif field_type.__module__ == 'source.models.models':
            if isinstance(new_field.type, type):
                mc_model = getattr(sys.modules[__name__], new_field.type.__name__)
                field_type = typing.Union[new_field.type, mc_model]
            else:
                raise ValueError(f"Expected a class/type but got {new_field.type}")
        fields.append((new_field.name, field_type, new_field))

    bases = []
    # Update the inheritance/based to use the new MC classes, rather than the caimira.models ones.
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
    cls for cls in vars(models).values()
    if dataclasses.is_dataclass(cls) and isinstance(cls, type)
]


# Inject the runtime generated MC types into this module.
for _model in _MODEL_CLASSES:
    setattr(sys.modules[__name__], _model.__name__, _build_mc_model(_model)) # type: ignore


# Make sure that each of the models is imported if you do a ``import *``.
__all__ = [_model.__name__ for _model in _MODEL_CLASSES] + ["MCModelBase"] # type: ignore
