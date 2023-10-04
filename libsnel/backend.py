import os
import subprocess


#
# {64: (lower 32, lower 16, lower 8)}
#
registers = {"rax": ("eax", "ax", "al"),
             "rbx": ("ebx", "bx", "bl"),
             "rcx": ("ecx", "cx", "cl"),
             "rdx": ("edx", "dx", "dl"),
             "rsi": ("esi", "si", "sil"),
             "rdi": ("edi", "di", "dil"),
             "rbp": ("ebp", "bp", "bpl"),
             "rsp": ("esp", "sp", "spl")}


def is_register(r: str) -> bool:
    for ii in registers:
        if r in [ii, *registers[ii]]:
            return True
    return False


class WBuffer:
    def __init__(self) -> None:
        self.buf = ""

    def __call__(self, *value: str, sep: str = " ", end="\n") -> None:
        self.buf += sep.join(value) + end

    def __str__(self) -> str:
        return self.buf

    def replace(self, old: str, new: str) -> None:
        self.buf = self.buf.replace(old, new)


class Function:
    code: list[str]

    def __init__(self, name: str) -> None:
        self.name = name
        self.code = []

    def add_code(self, inst: str) -> None:
        self.code.append(inst)

    def add_labl(self, name: str) -> None:
        self.code.append(f".{name}:")

    def op_2(self, op: str, a: str, b: str) -> None:
        if op not in ["mov", "add", "sub", "div", "mul", "or", "xor", "and"]:
            raise Exception()
        self.add_code(f"{op} {a}, {b}")

    def op_ret(self) -> None:
        self.add_code("ret")

    def op_push(self, src: str) -> None:
        self.add_code(f"push {src}")

    def op_pop(self, dst: str) -> None:
        self.add_code(f"pop {dst}")

    def op_mov(self, dst: str, src: str) -> None:
        self.op_2("mov", dst, src)

    def op_syscall(self, nr: int, *args: str | int) -> None:
        self.op_mov("rax", str(nr))
        regs = ["rdi", "rsi", "rdx", "r10", "r8", "r9"]
        for c, arg in enumerate(args):
            self.op_mov(regs[c], str(arg))
        self.add_code("syscall")

    def op_syscall_write(self, fd: str | int, buff: str, buff_len: str | int) -> None:
        self.op_syscall(1, fd, buff, buff_len)

    def fasm(self) -> str:
        buff = f"{self.name}:"
        for inst in self.code:
            if inst.startswith("."):
                buff += f"\n{inst}"
            else:
                buff += f"\n    {inst}"
        return buff


class Constant:
    def __init__(self, name: str, data: str, asm: str | None = None) -> None:
        self.name = name
        self.data = data
        self.length = len(data)
        self.asm = asm if asm else self.data

    def fasm(self) -> str:
        return f"{self.name} db {self.asm}"


class Module:
    functions: list[Function]
    constants: list[Constant]
    name: str
    entry_point: Function | None

    def __init__(self, name: str) -> None:
        self.name = name
        self.functions = []
        self.constants = []
        self.entry_point = None

    def add_function(self, fn: Function) -> None:
        self.functions.append(fn)

    def add_constant(self, const: Constant) -> None:
        self.constants.append(const)

    def find_symbol(self, name: str) -> Function | Constant:
        for ii in self.functions:
            if ii.name == name:
                return ii
        for ii in self.constants:
            if ii.name == name:
                return ii
        raise NameError(name)

    def set_entry_point(self, symbol: str) -> None:
        fn = self.find_symbol(symbol)
        if type(fn) == Function:
            self.entry_point = fn
        else:
            raise Exception()

    def fasm(self) -> str:
        code = WBuffer()

        code(f"format ELF64 executable")
        if self.entry_point:
            code(f"entry {self.entry_point.name}")

        code(f"segment readable executable")
        for fn in self.functions:
            code(fn.fasm())

        code(f"segment readable writable")
        for cn in self.constants:
            code(cn.fasm())

        for cn in self.constants:
            code.replace(f"$${cn.name}.len$$", str(cn.length))

        return str(code)

    def compile(self, name: str | None = None, debug: bool = True) -> None:
        if not name:
            name = self.name

        with open(name+".asm", "w") as f:
            f.write(self.fasm())

        if subprocess.call(["fasm", name+".asm"]) != 0:
            raise Exception("failed to assemble using fasm")

        subprocess.call(["chmod", "+x", name])
        if not debug:
            os.remove(name+".asm")


__all__ = ["Module", "Function"]
