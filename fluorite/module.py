import typing

from .value import Value
from .atom import Atom


class Module:
    __slots__ = ('_name', '_fns')
    _name: Atom
    _fns: typing.Mapping[int, typing.Callable]

    def __init__(self, name):
        self._name = name

    @property
    def pretty_name(self) -> str:
        return self._name.name
