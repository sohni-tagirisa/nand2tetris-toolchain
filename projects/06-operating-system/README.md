# Jack Operating System

Implementations of the eight core Jack OS classes:

- `Array` — allocation and disposal
- `Keyboard` — keyboard input and line/integer reading
- `Math` — arithmetic, comparison, square root, and bit operations
- `Memory` — heap allocation and direct memory access
- `Output` — character rendering and text output
- `Screen` — pixels, lines, rectangles, and circles
- `String` — mutable strings and integer conversion
- `Sys` — initialization, waiting, halting, and error handling

The `tests` directory contains the available Nand2Tetris fixtures and expected outputs, while `examples/Pong` provides a representative Jack application. Each OS class passes its component test independently.

## Known limitation

Loading all eight custom OS classes together still produces an integration failure. The individual implementations and fixtures are retained so the cross-component issue can be reproduced and investigated.
