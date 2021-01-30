import ast
import itertools
import functools
import typing


class NoTailError(Exception):
    def __init__(self):
        super().__init__("Do.NoTailError: a tail expression hasn't been declared!")


class Match(ast.stmt):
    """ Match(target lhs, bind rhs) """

    class Pattern(ast.expr):
        """ MatchPattern(expr pattern) """
        __slots__ = ('pattern',)
        pattern: ast.expr

        def __init__(self, pattern: ast.expr, *args, **kwargs):
            self.pattern = pattern

            super().__init__(args=args, kwargs=kwargs)

        _fields = (
            'pattern',
        )

    __slots__ = ('target', 'bound')
    target: Pattern
    bind: Pattern

    def __init__(self, *args, target: ast.expr = None, bind: ast.expr = None, **kwargs):
        self.target = Match.Pattern(target)
        self.bind = Match.Pattern(bind)

        super().__init__(args=args, kwargs=kwargs)

    _fields = (
        'target', 'bind',
    )


class Do(ast.stmt):
    """ Do(stmt* exprs, stmt? tail_expr) """
    _AnyExpr = typing.Union[ast.expr, ast.Expr]
    _ExprSeq = typing.Iterable[_AnyExpr]

    __slots__ = ('_blockbody', '_tail_expr')

    # For INTERNAL use only!
    _blockbody: typing.Iterator[_AnyExpr]
    _tail_expr: typing.Optional[ast.expr]

    __map_expr_stmt = functools.partial(map, lambda e: ast.Expr(e) if isinstance(e, ast.expr) else e)

    def __init__(self, *, exprs: _ExprSeq = (), tail_expr: _AnyExpr = None, **kwargs):
        self._blockbody = itertools.chain(exprs)
        self._tail_expr = tail_expr

        self.__chain_expr_to_exprs(tail_expr)

        super().__init__(kwargs=kwargs)

    @property
    def exprs(self) -> typing.Iterable[ast.Expr]:
        """
        :return: An Iterable yielding all the Do block's expressions (including the tail)
        """
        return self.__map_expr_stmt(self._tee_exprs())

    @property
    def exprs_head(self) -> typing.Iterable[ast.Expr]:
        """
        :return: Same as 'Do.exprs' except only the head (i.e. all but the tail) exprs are yielded
        """
        head: typing.Iterable[Do._AnyExpr] = ()
        if self._tail_expr is not None:     # explicit tail is present
            head = itertools.takewhile(lambda e: e is not self._tail_expr, self._tee_exprs())
        else:                               # no explicit tail - drop _blockbody[-1]
            (expr, successor) = itertools.tee(self._tee_exprs())
            next(successor, None)     # need exprs pair-wise, but mustn't consume _blockbody

            pairwise_head = itertools.takewhile(lambda args: None not in args, zip(expr, successor))
            head = itertools.starmap(lambda e, _: e, pairwise_head)       # drop zipped-in successor

        return self.__map_expr_stmt(head)

    @property
    def tail_expr(self) -> ast.Expr:
        """
        :return: either the expression specified in __init__(..., tail=<ast.expr>) or appended via Do.append(...);
             or an ast.Constant(None) => 'None' when it's not
        """

        val = self._tail_expr if self._tail_expr is not None else ast.Constant(None)
        expr: ast.Expr = ast.Expr(value=val) if val is not isinstance(val, ast.Expr) else val

        return expr

    def append(self, tail: ast.expr):
        """
        :param tail: the expression to be added at the tail of the block, while moving the previous
                tail to the back of the body's expr list head (if one was set)
        """
        if self._tail_expr is None:
            self._tail_expr = tail
        else:            # current tail must be preserved
            self.__chain_expr_to_exprs(self._tail_expr)
            self._tail_expr = tail

        self.__chain_expr_to_exprs(tail)

        return self

    def __chain_expr_to_exprs(self, expr: _AnyExpr):
        """
        :param expr: Extends internal '_blockbody' itertools.chain
        """
        self._blockbody = itertools.chain(self._blockbody, (expr, ))

        return self

    def _tee_exprs(self):
        (blockbody, exprs) = itertools.tee(self._blockbody)
        self._blockbody = blockbody

        return exprs

    @property
    def _dump_exprs(self) -> typing.List[ast.Expr]:
        return [expr for expr in map(lambda _: _, self._tee_exprs())]

    _fields = (
        "_dump_exprs",
    )
