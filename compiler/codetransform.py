import ast


class IRTransformer(ast.NodeTransformer):
    __slots__ = ('_tree', '_result')
    _tree: ast.AST
    _result: ast.Module

    def __init__(self, tree: ast.AST):
        self._tree = tree
