import rply
import ast
import typing
import itertools
import functools

from .lexer import TokenTag, Lexer
from .tree import ParseTreesData

import py


_VariantList = lambda a, b, c=None, d=None: typing.List[typing.Union[a, b, c, d]]

_TokenStream = typing.Iterable[rply.token.Token]

_Token = rply.token.Token
_Tree  = ast.AST
_TokenOrTree = typing.Union[_Token, _Tree]
_ExprList = typing.List[ast.expr]

_ProdTermsTokens = typing.List[_Token]
_ProdTermsTrees  = typing.List[_Tree]

_ProdTermsTokOrTree = _VariantList(_Token, _Tree)
_ProdTermsTreeLists = _VariantList(_ProdTermsTrees, _Tree)


class OpAssoc:
    NONASSOC = "nonassoc"
    LEFT     = "left"
    RIGHT    = "right"


class Parser:
    __slots__ = ('_parser', '_token_stream', '_tree')
    _token_stream: typing.Optional[_TokenStream]
    _tree: typing.Optional[ParseTreesData]     # Caches the result of a parse

    def __init__(self, token_stream: _TokenStream = None):
        self._parser = Parser.__build_parser()
        self._token_stream = token_stream

        self._tree = None

    def parse(self, token_stream: typing.Iterable[_Token] = None):
        self._token_stream = token_stream if token_stream is not None else self._token_stream

        assert self._token_stream, 'Parser.parse() called without source token stream assigned!'

        self._tree = ParseTreesData()
        self._parser.parse(iter(self._token_stream), state=self._tree)

        return self

    @property
    def tree(self) -> py.CompilationUnit:
        if self._tree is not None:
            return self._tree.source_tree

        return self.parse().tree     # cache the parse tree and return it...

    @classmethod
    def __build_parser(cls):
        pg = rply.ParserGenerator(
            Lexer.TOKEN_TAGS,

            precedence=[
                # (OpAssoc.NONASSOC,  [TokenTag.LBRACE, TokenTag.RBRACE]),
                (OpAssoc.NONASSOC,   [TokenTag.NOPARENSAPPLY]),
                (OpAssoc.NONASSOC,   [TokenTag.PARENSAPPLY]),
                (OpAssoc.RIGHT,      [TokenTag.FNAPPLY]),
                (OpAssoc.LEFT,       [TokenTag.COMMA]),
                (OpAssoc.LEFT,       [TokenTag.PLUS, TokenTag.MINUS]),
                (OpAssoc.LEFT,       [TokenTag.MULT, TokenTag.DIV]),
                (OpAssoc.LEFT,       [TokenTag.BINARYOP]),
                (OpAssoc.NONASSOC,   [TokenTag.LPAREN, TokenTag.RPAREN]),
                # (OpAssoc.RIGHT,     [TokenTag.UNARYAPPLY]),
                (OpAssoc.NONASSOC,   [TokenTag.UNARYOP]),
                (OpAssoc.LEFT,       [TokenTag.DOT]),
            ]
        )

        @pg.production("main : exprs")
        def main(tree: ParseTreesData, p: typing.List[_ProdTermsTrees]):
            prologue: typing.List[ast.AST] = []
            code: typing.List[ast.AST] = []

            exprs: typing.List[ast.AST] = p[0]
            for expr in exprs:
                if isinstance(expr, ast.Expr) and isinstance(expr.value, ast.FunctionDef):
                    func: ast.FunctionDef = expr.value
                    prologue.append(func)

                    name = ast.Name(id=func.name, ctx=ast.Load())
                    call = ast.Call(func=name, args=[], keywords=[])
                    code.append(ast.Expr(value=call))
                else:
                    code.append(expr)

            tree.source_tree = (node for node in itertools.chain(prologue, code))

        @pg.production(f"exprs : exprs {TokenTag.LF} expr-or-fn-apply")
        @pg.production(f"exprs : exprs ; expr-or-fn-apply")
        @pg.production(f"exprs : expr-or-fn-apply")
        def exprs_(_state, p: _ProdTermsTrees):
            tail_expr = p[-1]
            exprs_head = p[0] if p[0] is not tail_expr else []

            return exprs_head + [tail_expr]

        @pg.production(f"expr-or-fn-apply : expr")
        @pg.production(f"expr-or-fn-apply : match-expr")
        @pg.production(f"expr-or-fn-apply : fn-apply")
        def expr_or_fn_apply(_state, p: _ProdTermsTrees):
            # return Parser.__build_const_node(p[0], ast.Expr)
            return p[0]

        @pg.production(f"keyword : {TokenTag.KW} expr-or-fn-apply")
        def keyword(_state, p: _ProdTermsTokens):
            kw = p[0].getstr()

            name = ':' + kw[:-1]     # strip off the trailing ':' and put it at the front
            val  = Parser.__build_const_node(p[1], ast.Expr)

            return (name, val)

        @pg.production(f"atom : {TokenTag.ATOM}")
        def atom_unqual(_state, p: _ProdTermsTokens):
            return py.FlAtom(p[0].getstr())

        @pg.production(f"id : {TokenTag.ID}")
        def id_unqual(_state, p: _ProdTermsTokens):
            return py.Symbol(p[0].getstr())

        @pg.production(f"number : {TokenTag.NUM}")
        def number(_state, p: _ProdTermsTokens):
            tok_num = p[0].getstr()

            return Parser.__build_const_node(int(tok_num), py.FlInteger)

        @typing.overload
        @pg.production(f"expr : literal")
        def expr(_state, p: _ProdTermsTokOrTree):
            return Parser.__build_const_node(p[0], ast.Expr)

        @typing.overload
        @pg.production(f"expr : id")
        def expr(_state, p: _ProdTermsTrees):
            return Parser.__build_const_node(p[0], ast.Expr)

        @pg.production(f"literal : number")
        def number(_state, p: _ProdTermsTrees):
            return p[0]

        @pg.production(f"literal : atom")
        def atom(_state, p: _ProdTermsTrees):
            return Parser.__build_const_node(p[0], ast.Expr)

        @pg.production(f"literal : tuple")
        def tuple_(_state, p: _ProdTermsTrees):
            return Parser.__build_const_node(p[0], ast.Expr)

        @pg.production(f"literal : list")
        def list_(_state, p: _ProdTermsTrees):
            return Parser.__build_const_node(p[0], ast.Expr)

        @pg.production(f"literal : keyword-list")
        def keyword_list(_state, p: _ProdTermsTrees):
            return Parser.__build_const_node(p[0], ast.Expr)

        @pg.production( "tuple : { tuple-items }")
        @pg.production( "tuple : { tuple-items , }")
        def tuple_(_state, p: _VariantList(_ProdTermsTreeLists, _Token)):
            return py.FlTuple(p[1])

        @pg.production( "tuple : { }")
        @pg.production( "tuple : { LF }")
        def tuple_(_state, _p):
            return py.FlTuple([])

        @pg.production(f"tuple-items : tuple-items , expr-or-fn-apply")
        @pg.production(f"tuple-items : expr-or-fn-apply")
        def tuple_items(_state, p: _VariantList(_ProdTermsTrees, _Tree)):
            tail_item: ast.expr = p[-1]
            items_head: _ExprList = p[0] if p[0] is not p[-1] else []

            return items_head + [tail_item]

        @pg.production(f"list : list-open list-items list-close")
        def list_(_state, p: _ProdTermsTreeLists):
            return py.FlList(p[1])

        @pg.production(f"list : [ ]")
        def list_(_state, _p):
            return py.FlList([])

        @pg.production(f"list-open : [")
        @pg.production(f"list-open : [ {TokenTag.LF}")
        def list_open(_state, _p):
            return None

        @pg.production(f"list-close : ]")
        @pg.production(f"list-close : {TokenTag.LF} ]")
        @pg.production(f"list-close : , list-close")
        def list_close(_state, _p):
            return None

        @pg.production(f"list-items : list-items , list-item")
        @pg.production(f"list-items : list-items , {TokenTag.LF} list-item")
        @pg.production(f"list-items : list-items {TokenTag.LF} list-item")
        @pg.production(f"list-items : list-item")
        def list_items(_state, p: _ProdTermsTreeLists):
            tail_item: ast.expr = p[-1]
            items_head: _ExprList = p[0] if p[0] is not p[-1] else []

            # print(f"list_items: tail_item={tail_item} items_head={items_head}")

            return items_head + [tail_item]

        @pg.production(f"list-item : expr-or-fn-apply")
        def list_item(_state, p: _ProdTermsTrees):
            return p[0]

        @pg.production(f"keyword-list : kw-list-open keyword-list-items kw-list-close")
        def keyword_list(_state, p: _ProdTermsTreeLists):
            items: _ProdTermsTrees = p[1]

            return py.FlList(items)

        @pg.production(f"kw-list-open : [")
        @pg.production(f"kw-list-open : [ {TokenTag.LF}")
        def kw_list_open(_state, _p):
            return None

        @pg.production(f"kw-list-close : ]")
        @pg.production(f"kw-list-close : {TokenTag.LF} ]")
        @pg.production(f"kw-list-close : , kw-list-close")
        def kw_list_close(_state, _p):
            return None

        @pg.production(f"keyword-list-items : keyword-list-items , keyword-list-item")
        @pg.production(f"keyword-list-items : keyword-list-items , {TokenTag.LF} keyword-list-item")
        @pg.production(f"keyword-list-items : keyword-list-items {TokenTag.LF} keyword-list-item")
        @pg.production(f"keyword-list-items : keyword-list-item")
        def keyword_list_items(_state, p: _ProdTermsTreeLists):
            tail_item: ast.expr = p[-1]
            items_head: _ExprList = p[0] if p[0] is not p[-1] else []

            return items_head + [tail_item]

        @pg.production(f"keyword-list-item : keyword")
        def keyword_list_item(_state, p: _ProdTermsTokens):
            (name, val) = p[0]

            return py.FlTuple([typing.cast(py.FlAtom, name), val])

        @pg.production(f"fn-apply : fn-apply_noparens", precedence=TokenTag.NOPARENSAPPLY)
        @pg.production(f"fn-apply : fn-apply_parens", precedence=TokenTag.PARENSAPPLY)
        @pg.production(f"fn-apply : fn-apply0")
        def fn_apply_(_state, p: _ProdTermsTrees):
            return p[0]

        @pg.production(f"fn-apply_parens : fn-id {TokenTag.FNAPPLY} ( fn-args )")
        def fn_apply_parens(_state, p: _ProdTermsTreeLists):
            func: py.FlAtom = p[0]
            arg_nodes: _ExprList = p[-2]

            (args, kws) = itertools.tee(arg_nodes)
            args = itertools.filterfalse(Parser.__is_keyword, args)
            kws  = filter(Parser.__is_keyword, kws)

            return ast.Call(func=func, args=list(args), keywords=list(kws))

        @pg.production(f"fn-apply_noparens : fn-id {TokenTag.FNAPPLY} fn-args")
        def fn_apply_noparens(_state, p: _ProdTermsTreeLists):
            func: py.FlAtom = p[0]
            arg_nodes: _ExprList = p[-1]

            (args, kws) = itertools.tee(arg_nodes)
            args = itertools.filterfalse(Parser.__is_keyword, args)
            kws  = filter(Parser.__is_keyword, kws)

            return ast.Call(func=func, args=list(args), keywords=list(kws))

        @pg.production(f"fn-apply0 : fn-id {TokenTag.FNAPPLY} ( )")
        def fn_apply0(_state, p: _ProdTermsTokOrTree):
            return ast.Call(func=typing.cast(py.FlAtom, p[0]), args=[], keywords=[])

        @pg.production(f"fn-id : id")
        def fn_id_unqual(_state, p: _ProdTermsTrees):
            return typing.cast(py.Symbol, p[0])

        @pg.production(f"fn-id : fn-module . id")
        def fn_id_qual(_state, p: _ProdTermsTreeLists):
            path_tail: str= p[-1].name
            module_path: typing.List[py.FlAtom] = p[0]

            return py.QualSymbol(symbol=py.FlAtom(path_tail), module=module_path)

        @pg.production(f"fn-module : fn-module . atom")
        @pg.production(f"fn-module : atom")
        def fn_module(_state, p: _ProdTermsTreeLists):
            path_tail: py.FlAtom = p[-1]
            path_head: typing.List[py.FlAtom] = p[0] if p[0] is not p[-1] else []

            return path_head + [path_tail]

        @pg.production(f"fn-args : fn-args , fn-arg")
        @pg.production(f"fn-args : fn-arg")
        def fn_args(_state, p: typing.List[py.FlAtom]):
            # Concatenate all the arguments and filter out ','...
            return p[0]+[p[-1]] if len(p) > 1 else [p[0]]

        @pg.production(f"fn-arg : expr-or-fn-apply")
        def fn_arg(_state, p: _ProdTermsTokens):
            return p[0]

        @pg.production(f"fn-arg : ( fn-apply )")
        def fn_arg(_state, p: _ProdTermsTokens):
            return p[1]

        @pg.production(f"fn-arg : keyword")
        def fn_arg_keyword(_state, p):
            (name, val) = p[0]
            return (name, val)

        @pg.production(f"expr : primary-expr")
        def expr_primary(_state, p: _ProdTermsTrees):
            return p[0]

        @pg.production(f"expr : do-block")
        def expr_do(_state, p: typing.Iterable[typing.Tuple[ast.FunctionDef, ast.Call]]):
            body = p[0]

            return body

        @pg.production(f"do-block : do-block-open exprs do-block-close")
        def do_block(_state, p: typing.Tuple[int, typing.List[ast.expr]]):
            exprs = p[1]
            block = py.Do(exprs=exprs, tail_expr=(exprs[-1] if len(exprs) > 1 else None))

            return block

        @pg.production(f"do-block-open : {TokenTag.DO} {TokenTag.LF}")
        def do_block_open(_state, p: _ProdTermsTokens):
            tok_do = p[0]
            tok_do_pos = tok_do.getsourcepos()

            return tok_do_pos.idx       # Unique name

        @pg.production(f"do-block-close : {TokenTag.LF} {TokenTag.END}")
        def do_block_close(_state, p: _ProdTermsTokens):
            return None

        @pg.production(f"expr : ( expr )")
        def expr_parens(_state, p: _ProdTermsTokens):
            #print(f"expr_parens:p={p}")

            return Parser.__build_const_node(p[1])

        #@pg.production(f"primary-expr : expr binary-op expr")#, precedence=TokenTag.BINARYOP)
        @pg.production(f"primary-expr : expr badd expr", precedence=TokenTag.PLUS)
        @pg.production(f"primary-expr : expr bsub expr", precedence=TokenTag.MINUS)
        @pg.production(f"primary-expr : expr bmult expr", precedence=TokenTag.MULT)
        @pg.production(f"primary-expr : expr bdiv expr", precedence=TokenTag.DIV)
        def primary_expr(_state, p: _ProdTermsTrees):
            (lhs, op, rhs) = p

            return ast.BinOp(left=lhs, op=op, right=rhs)

        @pg.production(f"match-expr : expr = expr")
        def match_expr(_state, p: _ProdTermsTokOrTree):
            lhs: ast.expr
            rhs: ast.expr
            (lhs, _, rhs) = p

            return py.Match(target=lhs, bind=rhs)

        @pg.production(f"expr : unary-expr", precedence=TokenTag.UNARYOP)
        def unary_expr(_state, p: _ProdTermsTrees):
            return p[0]

        @pg.production(f"badd : {TokenTag.PLUS}")
        def op_add(*args): return ast.Add()

        @pg.production(f"bsub : {TokenTag.MINUS}")
        def op_sub(*args): return ast.Sub()

        @pg.production(f"bmult : {TokenTag.MULT}")
        def op_mult(*args): return ast.Mult()

        @pg.production(f"bdiv : {TokenTag.DIV}")
        def op_div(*args): return ast.Div()

        @pg.production(f"unary-expr : unary-op expr", precedence=TokenTag.UNARYOP)
        def unary_expr(_state, p: _ProdTermsTrees):
            (op, val) = p

            return ast.UnaryOp(op=op, operand=val)

        @pg.production(f"unary-op : {TokenTag.PLUS}")
        def unary_op_plus(*args): return ast.UAdd()

        @pg.production(f"unary-op : {TokenTag.MINUS}")
        def unary_op_neg(*args): return ast.USub()

        # Silence "unused token" warnings ->
        @pg.production(f"""
            --synth-toks : {TokenTag.UNARYOP}
                         | {TokenTag.NOPARENSAPPLY} {TokenTag.PARENSAPPLY} {TokenTag.UNARYAPPLY}
        """)
        def __synthetic_tokens(*args):
            raise AssertionError("Precedence-defining synthetic token used in a production!")

        #   ...and the resulting 'unused production' warning
        @pg.production(f"main : --synth-toks")
        def __main(*args): ...          # The rply.Parser is guaranteed to NEVER reduce by this rule

        return pg.build()

    @staticmethod
    def __build_const_node(
            val: typing.Any,
            make_node: typing.Callable[[typing.Any], ast.AST] = lambda val: ast.Constant(val)
    ) -> ast.AST:
        if isinstance(val, ast.AST):
            return val

        return make_node(val)

    # @staticmethod
    # def __build_qual_symbol(name: str):
    #     # module = atoms[:-1] if len(atoms) > 1 else ()
    #     # name = atoms[-1]

    #     return py.FlAtom(name)

    @staticmethod
    def __is_token(val):
        return isinstance(val, rply.token.Token)

    @staticmethod
    def __is_keyword(node):
        return isinstance(node, ast.keyword)
