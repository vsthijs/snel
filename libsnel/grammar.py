from pyleri import Grammar, Regex, Sequence, Keyword, Token, Repeat, Choice, THIS, Prio, Optional, List
from typing import TypeVar
import json
from .atree import AstNode, ex_s_any


T = TypeVar("T")


def flatten_list(l: list[list[T]]) -> list[T]:
    return [item for sublist in l for item in sublist]


class SnelGrammar(Grammar):
    r_identifier = Regex("[A-Za-z_][A-Za-z0-9_]*")
    r_int = Regex("-?[0-9]+")
    r_float = Regex("-?[0-9]+(,[0-9]+)?")
    r_string = Regex(r"\".*\"")
    r_char = Regex(r"'.'")

    k_fn = Keyword("fn")
    # k_type = Keyword("type")
    # k_const = Keyword("const")
    k_module = Keyword("module")
    k_import = Keyword("import")
    k_from = Keyword("from")

    t_open_paren = Token("(")
    t_close_paren = Token(")")
    # t_open_sqbrace = Token("[")
    # t_close_sqbrace = Token("]")
    t_open_brace = Token("{")
    t_close_brace = Token("}")
    t_semi_colon = Token(";")
    t_colon = Token(":")
    # t_comma = Token(",")
    t_equal = Token("=")
    t_plus = Token("+")
    t_minus = Token("-")
    t_times = Token("*")
    t_slash = Token("/")
    t_and = Token("&")
    t_or = Token("|")
    # t_open_arrow = Token("<")
    # t_close_arrow = Token(">")

    s_name = Choice(List(r_identifier, "."), r_identifier)

    s_binop = Choice(t_plus, t_minus, t_times, t_slash, t_and, t_or)
    s_expr = Prio(Choice(s_name, r_int, r_float, r_string, r_char),  # value
                  Sequence(t_open_paren, THIS, t_close_paren),  # (value)
                  Sequence(THIS, s_binop, THIS),  # value + value
                  Sequence(t_open_paren, List(THIS),
                           t_close_paren),  # (value, value)
                  )
    s_fndecl = Sequence(t_open_paren, List(Sequence(
        r_identifier, t_colon, s_expr)), t_close_paren, s_expr)  # (arg: type) return_type
    s_vardec = Sequence(r_identifier, t_colon, s_expr,)  # name:type
    s_vardef = Sequence(r_identifier, t_colon, s_expr,
                        t_equal, s_expr)  # name:type=value
    s_varass = Sequence(s_name, t_equal, s_expr,)  # name=value
    s_scope = Sequence(t_open_brace, Repeat(
        Sequence(Choice(s_expr, s_vardec, s_vardef, s_varass), t_semi_colon)), Optional(s_expr), t_close_brace)  # ex: { a = b(...); a}
    s_fndef = Sequence(k_fn, r_identifier, s_fndecl, s_scope)

    s_module = Sequence(k_module, r_identifier, t_open_brace,
                        Repeat(s_fndef), t_close_brace)

    s_import = Sequence(k_import, r_identifier, k_from,
                        r_string, t_semi_colon)

    START = Sequence(Repeat(s_import), Repeat(s_module))


GRAM = SnelGrammar()


def parse_file(fpath: str) -> AstNode:
    with open(fpath) as f:
        fcontent = f.read()
        tree = GRAM.parse(fcontent)
    if not tree.is_valid:
        print(fcontent[max(0, tree.pos-20):min(len(fcontent), tree.pos+20)])
        print(fcontent[max(0, tree.pos-20):min(len(fcontent), tree.pos)], "<- here")
        print(tree.as_str())
        raise SyntaxError()

    return ex_s_any(tree.tree)
