import rply

import re
import itertools
import functools
import typing


class TokenTag:
    NUM = "NUM"

    ID   = "ID"
    ATOM = "ATOM"
    KW   = "KW"

    PLUS  = "+"
    MINUS = "-"
    MULT  = "*"
    DIV   = "/"

    EQUAL = "="

    BINARYOP = "BINARYOP"

    LF = "LF"
    SEMICOLON = ";"

    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LSQRBRACKET = "["
    RSQRBRACKET = "]"

    COMMA = ","

    DOT = "."

    DO = "DO"
    FN = "FN"
    COND = "COND"
    CASE = "CASE"
    END = "END"

    # synthetic tokens for precedence table
    UNARYOP = "UNARYOP"

    NOPARENSAPPLY = "NOPARENSAPPLY"
    PARENSAPPLY   = "PARENSAPPLY"
    UNARYAPPLY    = "UNARYAPPLY"

    FNAPPLY = "FNAPPLY"


Token = rply.token.Token


class Lexer:
    __BAR = '|'
    TOKENS = [
        (TokenTag.NUM, r"\d+"),

        # need reserved keywords at the top...
        (TokenTag.DO, r"do"),
        (TokenTag.END, r"end"),

        (TokenTag.KW, r"[a-z]\w*:"),
        (TokenTag.ID, r"[a-z_]\w*"),
        (TokenTag.ATOM, r"(:[a-z]|[A-Z])\w*"),

        (TokenTag.PLUS, r"\+"),
        (TokenTag.MINUS, r"-"),
        (TokenTag.MULT, r"\*"),
        (TokenTag.DIV, r"/"),

        (TokenTag.EQUAL, r"="),

        (TokenTag.LF, r"\n\s*"),
        (TokenTag.SEMICOLON, r";"),

        (TokenTag.LPAREN, r"\("),
        (TokenTag.RPAREN, r"\)"),
        (TokenTag.LBRACE, r"{"),
        (TokenTag.RBRACE, r"}"),
        (TokenTag.LSQRBRACKET, r"\["),
        (TokenTag.RSQRBRACKET, r"\]"),

        (TokenTag.COMMA, r","),

        (TokenTag.DOT, r"\."),

        # Inserted by a transform on the token stream,
        #   as it is dependant on surrounding tokens
        #   and the whitespace (or lack thereof) between
        (TokenTag.FNAPPLY, r"(?=.)$"),

        # Synthetic tokens for precedence table
        (TokenTag.UNARYOP, r"(?=.)$"),

        (TokenTag.NOPARENSAPPLY, r"(?=.)$"),
        (TokenTag.PARENSAPPLY, r"(?=.)$"),
        (TokenTag.UNARYAPPLY, r"(?=.)$"),

        # --- Internal ---
        (__BAR, r"(?=.)$"),
    ]

    TOKEN_TAGS = dict(TOKENS).keys()    # stores all the TokenTags

    _LEADING_WHITESPACE  = re.compile(r"^\s+")
    _TRAILING_WHITESPACE = re.compile(r"\s+$")

    _COMMENT = re.compile(r"#[^\n]*")

    __slots__ = ('_lexer', )
    _lexer: rply.lexer.Lexer

    def __init__(self):
        self._lexer = Lexer.__build_lexer()

    def lex(self, source: str) -> rply.lexer.LexerStream:
        stream = self._lexer.lex(source)

        toks1, toks2 = itertools.tee(itertools.chain(stream, [None]))
        next(toks2, None)

        yield from functools.reduce(Lexer.__insert_fnapply, zip(toks1, toks2), [])

    @classmethod
    def tokens_list(cls):
        return cls.TOKENS.keys()

    @classmethod
    def __build_lexer(cls):
        lg = rply.LexerGenerator()

        for tok, exp in cls.TOKENS:
            lg.add(tok, exp)


        lg.ignore(Lexer._LEADING_WHITESPACE)
        lg.ignore(re.compile(r"[ \t]+"))
        lg.ignore(Lexer._COMMENT)
        # lg.ignore(re.compile(r"(?<=\s)[ \t]+(?=\n\s+)[ \t\n]+"))
        lg.ignore(Lexer._TRAILING_WHITESPACE)

        return lg.build()

    @staticmethod
    def __insert_fnapply(toks_out: typing.List[Token],
                         t: typing.Tuple[Token, typing.Union[Token, None]]):
        (token, lookahead) = t
        # print(f"{len(toks_out)}: ({token}, {lookahead})")

        if lookahead is None:       # None is used as end of stream marker
            return toks_out + [token]

        (tok_type, lahead_type) = (token.gettokentype(), lookahead.gettokentype())

        tok_fnapply = Token(TokenTag.FNAPPLY, '')
        tok_lf      = Token(TokenTag.LF, '')

        if (tok_type, lahead_type) == (TokenTag.ID, TokenTag.LPAREN):
            token_pos, lookahead_pos = token.getsourcepos(), lookahead.getsourcepos()

            token_end = token_pos.idx + len(token.getstr())

            if token_end == lookahead_pos.idx:   # Insert a FNAPPLY when there is no space between the function name and '('
                return toks_out + [token, tok_fnapply]
        elif tok_type == TokenTag.ID and lahead_type in {
                    TokenTag.ID, TokenTag.ATOM, TokenTag.KW,
                    TokenTag.NUM,
                    # TokenTag.PLUS, TokenTag.MINUS,              # unary ops
                    TokenTag.LBRACE, TokenTag.LSQRBRACKET,      # collection literals
        }:
            return toks_out + [token, tok_fnapply]   #  ...and between two adjacent terms (no operator inbetween)
        elif tok_type == TokenTag.LF:
            return toks_out + [tok_lf]

        return toks_out + [token]
