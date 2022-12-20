import json
from typing import Dict, Any

from PySide6.QtCore import QFileInfo

from src.app.utils.constant import DEFAULT_ENCODING


def json_to_file(json_dict: Dict[str, Any], file_name: str):
    with open(file_name, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=2)


def json_from_file(file_name: str) -> Dict[str, Any]:
    info = QFileInfo(file_name)
    if file_name and info.exists():
        with open(file_name, encoding=DEFAULT_ENCODING) as json_file:
            return json.load(json_file)
    else:
        return {}
