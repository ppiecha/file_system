from enum import Enum, auto

USER_NAME = "ppiecha"
APP_NAME = "File system"


class Context(Enum):
    main = auto()
    search = auto()


DEFAULT_ENCODING = "latin-1"
