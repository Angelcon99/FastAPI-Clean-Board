from enum import Enum, auto
from typing import NamedTuple, Any


class RepoStatus(Enum):
    SUCCESS = auto()
    NOT_FOUND = auto()
    FORBIDDEN = auto()
    ALREADY_DELETED = auto()    

class RepoResult(NamedTuple):
    status: RepoStatus
    data: Any | None = None