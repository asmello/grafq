from __future__ import annotations

from grafq.language import (
    ValueRawType,
)
from .base import FieldBlueprint


class DefaultFieldBlueprint(FieldBlueprint):
    def __init__(self, field_name: str, **kwargs: ValueRawType):
        super().__init__(field_name)
        self._arguments = kwargs

    def arg(self, name: str, value: ValueRawType) -> DefaultFieldBlueprint:
        self._arguments[name] = value
        return self
