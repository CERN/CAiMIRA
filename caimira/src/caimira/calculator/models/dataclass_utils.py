import dataclasses
import typing


def nested_replace(obj, new_values: typing.Dict[str, typing.Any]):
    """Replace an attribute on a dataclass, much like dataclasses.replace,
    except it supports nested replacement definitions. For example:

    >>> new_obj = nested_replace(obj, {'attr1.sub_attr2.sub_sub_attr3': 4})
    >>> new_obj.attr1.sub_attr2.sub_sub_attr3
    4

    """
    new_inst = obj
    for name, value in new_values.items():
        if '.' in name:
            # Recurse into the desired name and come out with a top-level
            # dataclass which has been updated appropriately.
            name, remainder = name.split('.', 1)
            value = nested_replace(
                getattr(new_inst, name),
                {remainder: value}
            )
        # We have a plain old name. So set it.
        new_inst = dataclasses.replace(new_inst, **{name: value})
    return new_inst


def nested_getattr(obj, name: str):
    """Get an attribute on a dataclass, much like getattr,
    except it supports nested attributes definitions. For example:

    >>> nested_getattr(obj, 'attr1.sub_attr2.sub_sub_attr3')
 
    """
    if '.' in name:
        # Recurse into the desired name and come out with a top-level
        # dataclass which has been updated appropriately.
        name, remainder = name.split('.', 1)
        return nested_getattr(getattr(obj,name), remainder)
    else:
        return getattr(obj,name)


def replace(obj, **changes):
    """
    A version of dataclasses.replace that handles ClassVar declarations.

    See https://bugs.python.org/issue33796.

    """

    orig = obj.__dataclass_fields__
    object.__setattr__(
        obj, '__dataclass_fields__',
        {name: field for name, field in orig.items()
         if field._field_type is not dataclasses._FIELD_CLASSVAR}
    )
    new = dataclasses.replace(obj, **changes)
    object.__setattr__(obj, '__dataclass_fields__', orig)
    return new


def walk_dataclass(model, name=""):
    """
    Recursively walk a dataclass instance, generating (name, obj) pairs for
    attributes and decending into nested dataclasses.

    >>> list(walk_dataclass(obj), 'my_obj')
    [('my_obj.attr_a', <dataclass instance>), ('my_obj.attr_a.sub_attr', <dataclass instance>)]

    """
    if name:
        name = name + '.'
    if not dataclasses.is_dataclass(model):
        raise TypeError(f'Not a dataclass based model: {type(model)}')
    for field in dataclasses.fields(model):
        obj = getattr(model, field.name)
        fq_name = f'{name}{field.name}'
        yield fq_name, obj
        if dataclasses.is_dataclass(obj):
            yield from walk_dataclass(obj, name=fq_name)
