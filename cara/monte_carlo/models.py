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

    def build_model(self, size: int) -> _ModelType:
        """
        Turn this MCModelBase subclass into a cara.models Model instance
        from which you can then run the model.

        """
        kwargs = {}
        for field in dataclasses.fields(self._base_cls):
            attr = getattr(self, field.name)
            if isinstance(attr, SampleableDistribution):
                attr = attr.generate_samples(size)
            elif isinstance(attr, MCModelBase):
                # Recurse into other MCModelBase instances by calling their
                # build_model method.
                attr = attr.build_model(size)
            kwargs[field.name] = attr
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
        # TODO: Update the type annotation to support the new model classes that exist.
        fields.append((new_field.name, new_field.type, new_field))
    cls = dataclasses.make_dataclass(
        model.__name__,  # type: ignore
        fields,  # type: ignore
        bases=(MCModelBase, ),
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
