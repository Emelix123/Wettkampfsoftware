"""Rope Skipping.

ROPE_SPEED:     Zaehl-Disziplinen (Speed 30s, 3min, Double Under ...).
                Bei mehreren Zaehlern zaehlt der KLEINSTE Wert (konservativ,
                wie bei abweichenden Zaehlungen ueblich).
                Score = Anzahl * Faktor + Offset.

ROPE_FREESTYLE: Kuer. Schwierigkeit + Praesentation, bei >= 3 Richtern wird
                die Praesentation getrimmt (hoechste + niedrigste raus).
                Score = (Schwierigkeit + Praesentation - Abzug) * Faktor + Offset.
"""
from .base import ScoringStrategy, ScoringInput, ScoringResult


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _avg_trim(values: list[float]) -> float:
    if len(values) >= 3:
        values = sorted(values)[1:-1]
    return _avg(values)


class RopeSpeed(ScoringStrategy):
    code = "ROPE_SPEED"
    label = "Rope Skipping Speed"
    required_kriterien = ["Anzahl"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={
                "wartet_auf_richter": float(inp.expected_judges - len(inp.judge_values)),
            })
        counts = [v["Anzahl"] for v in inp.judge_values if "Anzahl" in v]
        if not counts:
            return ScoringResult(score=None, breakdown={})
        anzahl = min(counts)
        score = anzahl * inp.faktor + inp.offset
        return ScoringResult(score=round(score, 3), breakdown={
            "Anzahl": round(anzahl, 3),
        })


class RopeFreestyle(ScoringStrategy):
    code = "ROPE_FREESTYLE"
    label = "Rope Skipping Freestyle"
    required_kriterien = ["Schwierigkeit", "Praesentation"]
    optional_kriterien = ["Abzug"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={
                "wartet_auf_richter": float(inp.expected_judges - len(inp.judge_values)),
            })
        schwierigkeit = [v["Schwierigkeit"] for v in inp.judge_values if "Schwierigkeit" in v]
        praesentation = [v["Praesentation"] for v in inp.judge_values if "Praesentation" in v]
        abzuege = [v.get("Abzug", 0.0) for v in inp.judge_values]

        s = _avg(schwierigkeit)
        p = _avg_trim(praesentation)
        abzug = _avg(abzuege)

        score = (s + p - abzug) * inp.faktor + inp.offset
        return ScoringResult(score=round(score, 3), breakdown={
            "Schwierigkeit": round(s, 3),
            "Praesentation_Schnitt_Trim": round(p, 3),
            "Abzug": round(abzug, 3),
        })
