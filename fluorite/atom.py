import hashlib

from .value import Value


class Atom(Value):
    __slots__ = ('_name', )
    _name: str

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name
