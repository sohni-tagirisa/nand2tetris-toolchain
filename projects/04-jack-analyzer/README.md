# Jack Syntax Analyzer

A tokenizer and recursive-descent parser for Jack. Full-parser mode emits an XML syntax tree, while tokenizer-only mode emits the token stream.

```bash
python3 src/JackAnalyzer.py examples/ArrayTest
python3 src/JackAnalyzer.py -t examples/ArrayTest
```
