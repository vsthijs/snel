# Snel programming language
I am creating a toy language, with a compiler. Inspired by Python, C and Rust.

The programming will have NO intrinsics like standard instructions. They are all defined in a standard library. With this flexibility, you can generate custom assembly.
There will be standard instructions declared in the standard library.

## Example
```
module std {
    intrinsic fn print(msg: string);
}

pub fn main () {
    std.print("Hello, World!");
    0
}
```