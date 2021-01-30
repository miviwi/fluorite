import typing

from .symbol import Symbol, SymbolTable


class CodeObject:
    __slots__ = ('_syms', )
    _syms: SymbolTable

    def __init__(self):
        self._syms = SymbolTable()
