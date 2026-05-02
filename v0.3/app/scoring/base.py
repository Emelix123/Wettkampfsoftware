from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoringInput:
    judge_values: list[dict[str, float]]  # eine dict je Wertung/Richter
    faktor: float = 1.0
    offset: float = 0.0
    expected_judges: int = 1


@dataclass
class ScoringResult:
    score: Optional[float]   # None = noch nicht genug Wertungen
    breakdown: dict[str, float]  # transparente Zwischenergebnisse zur Anzeige


class ScoringStrategy:
    code: str = ""
    label: str = ""
    required_kriterien: list[str] = []   # Pflichtfelder pro Wertung

    def validate(self, values: dict[str, float]) -> list[str]:
        """Prueft ob eine einzelne Richter-Wertung alle Pflicht-Kriterien hat.
        Gibt eine Liste fehlender Felder zurueck."""
        return [k for k in self.required_kriterien if k not in values]

    def compute(self, inp: ScoringInput) -> ScoringResult:  # pragma: no cover
        raise NotImplementedError
