# Wordle in Jack

A Wordle-style game implemented in Jack. Players have six attempts to identify each five-letter word across seven levels. A check mark denotes the correct letter in the correct position; a slash denotes a correct letter in the wrong position.

## Design

- `Main.jack` starts and disposes the game.
- `Game.jack` owns the game loop, input, scoring, rendering, and statistics.
- `WordList.jack` provides the fixed word set and instructions.
- `Util.jack` contains small reusable helpers.

The implementation is designed for Jack's limited heap and lack of garbage collection. Arrays and buffers are allocated once and reused, guesses are represented as character-code arrays, and text is rendered character by character to avoid unnecessary temporary strings.

## Run

Compile the four files in `src` with the Jack compiler, then load the resulting VM files in the Nand2Tetris VM Emulator. Precompiled VM output is preserved in `build`.

```bash
python3 ../05-jack-compiler/src/JackCompiler.py src
```

## Possible extensions

- Validate guesses against a dictionary.
- Add configurable word lengths and difficulty levels.
- Add lightweight heap instrumentation for debugging.
