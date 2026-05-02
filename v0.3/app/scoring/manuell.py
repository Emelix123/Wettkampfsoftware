from .base import ScoringStrategy, ScoringInput, ScoringResult


class Manuell(ScoringStrategy):
    code = "MANUELL"
    label = "Manuell"
    required_kriterien = ["Wert"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if not inp.judge_values:
            return ScoringResult(score=None, breakdown={})
        wert = inp.judge_values[0].get("Wert", 0.0)
        return ScoringResult(score=round(wert, 3), breakdown={"Wert": wert})
