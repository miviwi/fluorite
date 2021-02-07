import compiler
import fluorite

import typing
from functools import reduce
import itertools

import rply

lexer  = compiler.lexer.Lexer()
parser = compiler.parser.Parser()

tok_stream = lexer.lex(
    """
    do
            a = 3
            b = 4

            c = a*a + b*b

            Math.sqrt c         # the length of the hypot
            [
                a,
                b,
                c
            ]
    end
    """
)

(tokens, tokens2) = itertools.tee(tok_stream)
print(f"tokens =>\n"+''.join([f"\t{tok},\n" for tok in tokens2]))

tree = parser.parse(tokens).tree

print(parser._tree._unparse_source_tree() + '\n')
print(parser._tree._dump_source_tree())

ir_transformer = compiler.codetransform.IRTransformer(tree)

# my_code = compile(tree.ast_mod, "<string>", mode='exec')
#
# print(eval(my_code, {
#     'expr': 'expr =', 'Fluorite.print': print, 'Module.fun': ord,
#     'f': lambda: '[fn -> ()]', 'd': 'd', 'b': 3, 'g': 4, 'var': '"VAR!"',
#     'fn': lambda arg: f"fn({arg}) -> lambda!",
#     'list': lambda *args: list(args),
#     'a': lambda x, y: print(f"sqrt({x}^2 + {y}^2)={(x**2 + y**2)**(1/2)}"),
#
#     'Dict.new': dict,
#
#     'sqrt': lambda x: x**(1/2),
#
#     'scan': lambda *terms: list(itertools.accumulate(terms)),
# }, {}))
