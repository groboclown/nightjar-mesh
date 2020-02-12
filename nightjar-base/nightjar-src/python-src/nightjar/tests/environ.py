
from typing import Dict, Set
import os


class Environ:
    prev: Dict[str, str] = {}
    replace: Dict[str, str] = {}
    remove: Set[str] = set()

    def __enter__(self) -> None:
        self.prev = dict(os.environ)
        os.environ.update(self.replace)
        for key in self.remove:
            del os.environ[key]

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        for key in self.replace.keys():
            del os.environ[key]
        os.environ.update(self.prev)
