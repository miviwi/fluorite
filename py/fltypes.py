import ast
import itertools
import typing


class FlTerm(ast.expr):
    """
        FlTerm = FlInteger(number value)
               | FlFloat(real value)
               | FlAtom(atom value)
               | FlString(string value)
               | FlList(list value)
               | FlTuple(tuple value)
               | FlKeywordList(kw-list value)
    """
    Term = typing.Union[int, float, str]

    __slots__ = ('value', )
    value: Term

    def __init__(self, *args, value: Term = None, **kwargs):
        self.value = value

        super().__init__(args=args, kwargs=kwargs)

    _fields = (
        'value',
    )


class FlInteger(FlTerm):
    """ FlInteger(number value) """
    __slots__ = ()
    value: int

    def __init__(self, value: int, *args, **kwargs):
        super().__init__(value=value, args=args, kwargs=kwargs)


class FlAtom(FlTerm):
    """ FlAtom(atom value) """
    __slots__ = ('module', )
    value: str
    module: typing.Tuple[str, ...]

    def __init__(self, value: str, *args, module: typing.Iterable[str] = (), **kwargs):
        self.module = tuple(module)

        super().__init__(value=value, args=args, kwargs=kwargs)

    @property
    def name(self):
        return '.'.join(self.module + ('', )) + self.value

    def __repr__(self):
        return self.name

    _fields = (
        'name',
    )


class FlString(FlTerm):
    """ FlString(string value) """
    __slots__ = ()
    value: str

    def __init__(self, value: str, *args, **kwargs):
        super().__init__(value=value, args=args, kwargs=kwargs)


class FlCollection(FlTerm):
    """
        FlCollection = FlList(list value)
                     | FlTuple(tuple value)
                     | FlKeywordList(kw-list value)
    """
    __slots__ = ()
    value: typing.List[ast.expr]

    def __init__(self, value: typing.List[ast.expr], *args, **kwargs):
        super().__init__(value=value, args=args, kwargs=kwargs)


class FlList(FlCollection):
    """ FlList(list value) """
    __slots__ = ()


class FlTuple(FlTerm):
    """ FlTuple(tuple value) """
    __slots__ = ()
