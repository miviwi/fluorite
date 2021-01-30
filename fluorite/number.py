from .value import Value


class Integer(Value):
    __slots__ = ('_i', )
    _i: int

    def __init__(self, i: int):
        self._i = i

    @property
    def value(self) -> int:
        return self._i
