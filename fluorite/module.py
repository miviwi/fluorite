import typing

from .value import Value
from .atom import Atom


class Module:
    __slots__ = ('_name', )
    _name: Atom

    def __init__(self, name):
        self._name = name

    @property
    def pretty_name(self) -> str:
        return self._name.name
