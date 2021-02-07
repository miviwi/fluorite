import typing

from .value import Value
from .atom import Atom


class Function:
    _ArgsPack = typing.Tuple[Value, ...]

    _KeywordArg = typing.Tuple[Atom, Value
    _KwargsPack = typing.Tuple[KeywordArg, ...]

    FnCodeObject = typing.Callable[[_ArgsPack, _KwargsPack], Value]

    __slots__ = ("_module", "_symbol", "_arity", "_co")
    _module: Atom
    _symbol: Atom
    _arity: int
    _co: FnCodeObject

    def __init__(self, symbol: Atom, fn_codeobj: FnCodeObject, *,
                       module: Atom, arity: int):
        self._symbol = symbol
        self._module = module
        self._arity = arity

    @property
    def qual_name(self):
        return '.'.join((self._module, self._symbol))

    def __repr__(self):
        return f"{self.qual_name}/{self._arity}"
