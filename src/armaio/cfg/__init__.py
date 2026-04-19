from copy import deepcopy

from ._format import (
    ConfigElement,
    validate_config_types,
    format_config
)


class Config:
    def __init__(self, data: list[ConfigElement]) -> None:
        validate_config_types(data)

        self._data: list[ConfigElement] = deepcopy(data)

    def format(self) -> str:
        return format_config(self._data)
