# Snel programming language
I am creating a toy language, with a compiler. Inspired by Python, C and Rust.

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