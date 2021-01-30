import ast


class CodeGen:
    __slots__ = ('_ast', )

    def __init__(self, _ast: ast.AST):
        self._ast = _ast
