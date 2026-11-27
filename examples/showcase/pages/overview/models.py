from enum import Enum


class Range(str, Enum):
    D7 = "7d"
    D30 = "30d"
    D90 = "90d"

    @property
    def days(self) -> int:
        return int(self.value[:-1])
