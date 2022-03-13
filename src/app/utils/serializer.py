import json
from typing import Dict, Any

from PySide2.QtCore import QFileInfo


def json_to_file(json_dict: Dict[str, Any], file_name: str):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=2)


def json_from_file(file_name: str) -> Dict[str, Any]:
    if file_name and QFileInfo(file_name).exists():
        with open(file_name, encoding="utf-8") as json_file:
            return json.load(json_file)
    else:
        return {}
