import ast
import typing


class CompilationUnit(ast.mod):
    """ CompilationUnit(stmt* body) """
    def __init__(self, body: typing.List[ast.stmt], **kwargs):
        self.body = body

        super().__init__(kwargs=kwargs)

    @property
    def ast_mod(self) -> ast.Module:
        return ast.Module(body=self.body, type_ignores=[])

    _fields = (
        'body',
    )
