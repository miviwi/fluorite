import compiler
import fluorite

import typing
from functools import reduce
import itertools

import rply

lexer  = compiler.lexer.Lexer()
parser = compiler.parser.Parser()

tokens = lexer._lexer.lex(
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
    # "print(scan 1, 2, (int 3/2), -4, (sqrt 5))"
    # """
    # do
    #         print a, list(), fn 5/2, g
    # end
    # """
    #"print list fn([kw: f()]), var"
# end)
# """
    # "[1, 2, 3, 4, 5]"
    # "Fluorite.func(); Fluorite.Kernel.say :hello"
    # "print expr, fn(), ((4-10 + 200) / 2), range(5, 6)"
    # """print [
    #      this: 1
    #      is: 2
    #      mylist: 3
    #  ]
    #  print {1, 2, 3}"""
    #"fn a b, g ; print d, ((Module.fun(f)) + 3), { 1, 2, 3 }"#; unary :symbol + 6"
    # "{ 1*4, 2*5, 3*6 }; { 2, }; { 3, 4 }; { 5, 6, }; { 7, 8, 9 }; { }"
)

Token = rply.token.Token
TokenTag = compiler.lexer.TokenTag
def insert_fnapply(tokens_out: typing.List[Token],
                   toks: typing.Tuple[Token, Token]):
    (token, lookahead) = toks

    if lookahead is None:
        return tokens_out + [token]

    tok_fnapply = rply.token.Token(TokenTag.FNAPPLY, '')

    if (token.gettokentype(), lookahead.gettokentype()) == (TokenTag.ID, TokenTag.LPAREN):
        token_pos = token.getsourcepos()
        lookahead_pos = lookahead.getsourcepos()

        token_end = token_pos.idx + len(token.getstr())   # One past the index of final id character

        if token_end == lookahead_pos.idx:  # Check if there is no whitespace between the id and '('
            return tokens_out + [token, tok_fnapply]
    elif token.gettokentype() == TokenTag.ID and \
            lookahead.gettokentype() in {
                TokenTag.ID, TokenTag.ATOM, TokenTag.KW,
                TokenTag.NUM,
                # TokenTag.PLUS, TokenTag.MINUS,              # unary ops
                TokenTag.LBRACE, TokenTag.LSQRBRACKET,      # collection literals
    }:
        return tokens_out + [token, tok_fnapply]

    return tokens_out + [token]


tok_a, tok_b = itertools.tee(itertools.chain(tokens, [None]))
next(tok_b, None)

(tokens, tokens2) = itertools.tee(reduce(insert_fnapply, zip(tok_a, tok_b), []))
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
