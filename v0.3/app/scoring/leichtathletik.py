from .base import ScoringStrategy, ScoringInput, ScoringResult


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class LaDirect(ScoringStrategy):
    """Score = Wert * Faktor + Offset (z.B. Weite, Hoehe)."""
    code = "LA_DIRECT"
    label = "Leichtathletik Direkt"
    required_kriterien = ["Wert"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={})
        wert = _avg([v["Wert"] for v in inp.judge_values if "Wert" in v])
        score = wert * inp.faktor + inp.offset
        return ScoringResult(score=round(score, 3), breakdown={"Wert": round(wert, 3)})


class LaSprint(ScoringStrategy):
    """Score = Offset - Wert * Faktor (kleiner Wert = besser, z.B. Zeit)."""
    code = "LA_SPRINT"
    label = "Leichtathletik Sprint/Zeit"
    required_kriterien = ["Wert"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={})
        wert = _avg([v["Wert"] for v in inp.judge_values if "Wert" in v])
        score = max(0.0, inp.offset - wert * inp.faktor)
        return ScoringResult(score=round(score, 3), breakdown={"Wert": round(wert, 3)})
