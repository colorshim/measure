from __future__ import annotations

from typing import Any, NamedTuple


class PowerMeter:
    def get_power(self) -> PowerMeasurementResult:
        pass

    def get_questions(self) -> list[dict]:
        return []

    def process_answers(self, answers: dict[str, Any]):
        pass


class PowerMeasurementResult(NamedTuple):
    power: float
    updated: float
