# File System

> File system browser


###Testing
Non-audio tests
```bash
pytest -vv -k "test and not test_play"
```
Audio tests
```bash
pytest -vv -k "test_play"
```
Code formatting
```bash
black src -l 120 --target-version py310
```