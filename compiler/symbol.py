import typing


class Symbol:
    __slots__ = ('_module', '_sym', )
    _module: typing.Any
    _sym: str

    def __init__(self):
        self._module = None
        self._sym = ':sym'

class SymbolTable:
    __slots__ = ('_syms', )
    _syms: typing.Dict[int, Symbol]

    def __init__(self):
        self._syms = {}
