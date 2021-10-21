from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    line: int
    column: int


@dataclass
class OperationError:
    message: str
    locations: Optional[list[Location]] = None
    path: Optional[list[str]] = None


class OperationErrors(Exception):

    def __init__(self, errors: list[dict]):
        self.errors = [
            OperationError(
                error['message'],
                locations=[Location(location['line'], location['column']) for location in error.get('locations', ())],
                path=error.get('path')
            )
            for error in errors
        ]
