# File System

> Windows file system browser  
> Simplifies browsing source code written in various programming languages
### Requirements
Python >= 3.9 \
Windows >= 10 \
see ***requirements.txt*** file
### Installation
pywin32 post install script (copies required DLLs) \
https://github.com/mhammond/pywin32/blob/main/pywin32_postinstall.py
```commandline
pip install -r requirements.txt
```
### Testing
```commandline
pytest -vv
```
### Code formatting
```commandline
black src -l 120 --target-version py310
```
### Quality check
```commandline
pylint src
```
## Features

- Tree-based with tabs
- Each tab contains only required subtree to simplify navigation 
- Tree-based favorites panel
- Search dialog window integrated with navigation window
- Integration with Notepad++ to view/edit files
- Integration with VS Code to view/edit files and open folder with file
- Integration with built-in Windows FileExplorer
- Integration with Git and Chrome (opens repository URL)
- Supported all basic file/folder operations
- Option to create multiple files, folders and whole paths at once
- Option to open multiple files/folders at once 
- Option to create file from clipboard content
- Option to duplicate content of file/folder under different name in the same location
- Option to copy multiple items name/path at once
