from dataclasses import dataclass, field
from typing import List


@dataclass
class Query:
    query: str
    target: str
    subdir: str
    offset: int = 0
    limit: int = 10


@dataclass
class Config:
    uid: str
    passwd: str
    saveroot: str
    limit: int = 10
    queries: List[Query] = field(default_factory=list)
