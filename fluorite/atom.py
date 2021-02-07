import xxhash

from .value import Value


class Atom(Value):
    __slots__ = ('_name', '_id')
    _name: str
    _id: int

    def __init__(self, *path: str):
        name = '.'.join(path)

        h = xxhash.xxh64()
        h.update(self._name)

        self._name = name
        self._id = h.intdigest()

    @property
    def name(self) -> str:
        return self._name
