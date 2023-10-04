from pyleri.node import Node
from typing import Literal
import json


def get_element_name(n: Node) -> str:
    return n.element.__class__.__name__


def assert_eq(left: object, right: object) -> None:
    if left != right:
        raise AssertionError(f"'{left}' != '{right}'")


# View the parse tree:
def view_parse_tree(res):
    def node_props(node, children) -> dict[str, object | list[dict[str, object]]]:
        return {
            'start': node.start,
            'end': node.end,
            'name': node.element.name if hasattr(node.element, 'name') else None,
            'element': node.element.__class__.__name__,
            'string': node.string,
            'children': children}

    # Recursive method to get the children of a node object:
    def get_children(children):
        return [node_props(c, get_children(c.children)) for c in children]

    start = res
    return node_props(start, get_children(start.children))


def hasname(n: Node, name: str) -> bool:
    _n = n.element.name if hasattr(
        n.element, "name") else n.element.__class__.__name__
    return _n == name


def dump(fp: str, n: Node) -> None:
    with open(fp, "w") as f:
        json.dump(view_parse_tree(n), f, indent=4)


AstType = Literal[
    "import",
    "name",
    "module",
    "src_file",
    "fn_decl",
    "integer",
    "string",
    "float",
    "char",
    "binop",
    "fn_def",
    "binop_expr",  # op, left, right
    "scope",  # expr|stmt +
    "var_assignment",  # name, expr
    "var_definition",  # name, type, expr
    "var_declaration",  # name, type
]


class AstNode:
    children: list["AstNode"]
    type: AstType

    def __init__(self, type: AstType, *children: "AstNode", value: object = None) -> None:
        self.type = type
        self.children = [*children]
        self.value = value

    def __str__(self) -> str:
        match self.type:
            case "name":
                return str(self.value)
            case "import":
                return f"import {self.children[0]}"
            case "module":
                return f"mod {self.value};"
            case _:
                return super().__str__()

    def to_dict(self, include_value: bool = True) -> dict:
        d = {"type": self.type, "children": [
            i.to_dict(include_value) for i in self.children]}
        if include_value:
            d["value"] = self.value
        return d

    def export(self, fp: str) -> None:
        with open(fp, "w") as f:
            try:
                json.dump(self.to_dict(), f, indent=4)
            except TypeError:
                json.dump(self.to_dict(False), f, indent=4)


def ex_s_import(n: Node) -> AstNode:
    assert_eq(n.element.name, "s_import")
    assert_eq(n.children[0].element.name, "k_import")
    if n.children[1].element.name == "r_identifier":
        name = AstNode("name", value=n.children[1].string)
    else:
        raise Exception()
    return AstNode("import", name)


def ex_s_module(n: Node) -> AstNode:
    assert n.children[0].element.name == "k_module"
    assert n.children[1].element.name == "r_identifier"
    name = AstNode("name", value=n.children[1].string)
    assert n.children[2].element.name == "t_open_brace"
    return AstNode("module", *[ex_s_any(i) for i in n.children[3].children], value=name)


def ex_s_name(n: Node) -> AstNode:
    match get_element_name(n.children[0]):
        case "Regex":
            return AstNode("name", value=n.string)
        case "List":
            nc = []
            for ii in n.children[0].children:
                nc.append(ii.string)
            return AstNode("name", value=".".join(nc))
        case _:
            raise Exception("invalid name")


def ex_s_binop(n: Node) -> AstNode:
    match n.children[0].element.name:
        case "t_plus":
            return AstNode("binop", value="+")
        case "t_minus":
            return AstNode("binop", value="-")
        case "t_times":
            return AstNode("binop", value="*")
        case "t_slash":
            return AstNode("binop", value="/")
        case "t_and":
            return AstNode("binop", value="&")
        case "t_or":
            return AstNode("binop", value="|")
        case _:
            dump("dbg0.json", n)
            raise Exception("invalid binop")


def ex_s_expr(n: Node) -> AstNode:
    p = n.children[0]  # Prio or This

    if hasname(p.children[0], "Choice"):
        e = p.children[0].children[0]
        if hasname(e, "s_name"):
            return ex_s_name(e)
        elif hasname(e, "r_int"):
            return AstNode("integer", value=int(e.string))
        elif hasname(e, "r_float"):
            return AstNode("float", value=float(e.string))
        elif hasname(e, "r_string"):
            return AstNode("string", value=e.string.removeprefix('"').removesuffix("'"))
        elif hasname(e, "r_char"):
            return AstNode("char", value=e.string.removeprefix("'").removesuffix("'"))
        else:
            raise Exception("invalid expression: invalid value")
    elif hasname(p.children[0], "Sequence"):
        e0 = p.children[0].children[0]
        if hasname(e0, "t_open_paren"):  # (value) or (value, value, ...)
            e1 = p.children[0].children[1]
            if hasname(e1, "This"):  # (value)
                return ex_s_expr(e1)
            elif hasname(e1, "List"):
                raise Exception("unimplemented")
            else:
                raise Exception("invalid expression")
        elif hasname(e0, "This"):  # value + value
            left = ex_s_expr(e0)
            op = ex_s_binop(p.children[0].children[1])
            right = ex_s_expr(p.children[0].children[2])
            return AstNode("binop_expr", op, left, right)
        else:
            raise Exception("invalid expression")
    elif hasname(p.children[0], "s_name"):
        return ex_s_name(p.children[0])
    else:
        raise Exception("invalid expression")
    # elif p.children[0].children[1].element.name == "s_binop":
    #     left = ex_s_expr(p.children[0].children[0])
    #     op = ex_s_binop(p.children[0].children[1])
    #     right = ex_s_expr(p.children[0].children[2])
    #     return AstNode("binop_expr", op, left, right)
    # elif p.children[0].children[0].element.name == "t_open_paren":
    #     return ex_s_expr(p.children[0].children[1])
    # else:
    #     raise Exception("invalid expression")


def ex_s_fndecl(n: Node) -> AstNode:
    assert_eq(n.children[0].element.name, "t_open_paren")
    assert_eq(get_element_name(n.children[1]), "List")
    args: list[tuple[str, AstNode]] = []
    for arg in n.children[1].children:
        if get_element_name(arg) == "Sequence":
            assert_eq(arg.children[0].element.name, "r_identifier")
            an = arg.children[0].string
            assert_eq(arg.children[1].element.name, "t_colon")
            assert_eq(arg.children[2].element.name, "s_expr")
            at = ex_s_expr(arg.children[2])
            args.append((an, at))

    assert_eq(n.children[2].element.name, "t_close_paren")
    assert_eq(n.children[3].element.name, "s_expr")
    return AstNode("fn_decl", ex_s_expr(n.children[3]), value=args)


def ex_s_vardec(n: Node) -> AstNode:
    r_identifier, _, s_expr = n.children
    name = AstNode("name", value=r_identifier.string)
    type = ex_s_expr(s_expr)
    return AstNode("var_declaration", name, type)


def ex_s_vardef(n: Node) -> AstNode:
    r_identifier, _, s_expr_t, _, s_expr_v = n.children
    name = AstNode("name", value=r_identifier.string)
    type = ex_s_expr(s_expr_t)
    expr = ex_s_expr(s_expr_v)
    return AstNode("var_definition", name, type, expr)


def ex_s_varass(n: Node) -> AstNode:
    assert_eq(n.children[0].element.name, "s_name")
    assert_eq(n.children[1].element.name, "t_equal")
    assert_eq(n.children[2].element.name, "s_expr")
    name = ex_s_name(n.children[0])
    expr = ex_s_expr(n.children[2])
    return AstNode("var_assignment", name, expr)


def ex_s_scope(n: Node) -> AstNode:
    assert_eq(n.element.name, "s_scope")
    assert_eq(n.children[0].element.name, "t_open_brace")
    rep = n.children[1]
    code: list[AstNode] = []
    for ii in rep.children:
        stmt = ii.children[0].children[0]
        match stmt.element.name:
            case "s_expr":
                code.append(ex_s_expr(stmt))
            case "s_vardec":
                code.append(ex_s_vardec(stmt))
            case "s_vardef":
                code.append(ex_s_vardef(stmt))
            case "s_varass":
                code.append(ex_s_varass(stmt))
            case _:
                raise Exception("invalid scope")
    return AstNode("scope", *code)


def ex_s_fndef(n: Node) -> AstNode:
    # extract name
    assert_eq(n.element.name, "s_fndef")
    assert_eq(n.children[0].element.name, "k_fn")
    assert_eq(n.children[1].element.name, "r_identifier")
    name = n.children[1].string

    # extract declaration
    assert_eq(n.children[2].element.name, "s_fndecl")
    decl = ex_s_fndecl(n.children[2])

    # extract code
    assert_eq(n.children[3].element.name, "s_scope")
    s = n.children[3]
    scope = ex_s_scope(s)

    return AstNode("fn_def", decl, scope, value=name)


def ex_s_start(n: Node) -> AstNode:
    n = n.children[0]  # idk, just works
    assert get_element_name(n.children[0]) == "Repeat"
    children = []
    for ii in n.children[0].children:
        children.append(ex_s_import(ii))

    assert get_element_name(n.children[1]) == "Repeat"
    for ii in n.children[1].children:
        children.append(ex_s_module(ii))

    return AstNode("src_file", *children)


def ex_s_any(n: Node) -> AstNode:
    match n.element.name:
        case "s_import":
            return ex_s_import(n)
        case "s_module":
            return ex_s_module(n)
        case "START":
            return ex_s_start(n)
        case "s_fndef":
            return ex_s_fndef(n)
        case "s_fndecl":
            return ex_s_fndecl(n)
        case "s_scope":
            return ex_s_scope(n)
        case _:
            raise Exception(f"UNHANDLED: '{n.element.name}'")
