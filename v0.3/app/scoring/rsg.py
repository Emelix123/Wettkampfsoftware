"""Rhythmische Sportgymnastik.

Score = (D + A + E - Abzug) * Faktor + Offset
  * D_Note  (Pflicht)  — Schwierigkeit, Schnitt aller D-Richter
  * E_Note  (Pflicht)  — Ausfuehrung, Trim (hoechste+niedrigste raus) ab 3 Richtern
  * A_Note  (optional) — Artistik; wird nur einbezogen wenn eingetragen
  * Abzug   (optional) — neutrale Abzuege (Zeit, Linie, ...)

Wer ohne A-Note arbeitet, laesst das Feld einfach leer — es zaehlt dann 0.
"""
from .base import ScoringStrategy, ScoringInput, ScoringResult


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _avg_trim(values: list[float]) -> float:
    if len(values) >= 3:
        values = sorted(values)[1:-1]
    return _avg(values)


class RsgStandard(ScoringStrategy):
    code = "RSG_STANDARD"
    label = "RSG (D + A + E)"
    required_kriterien = ["D_Note", "E_Note"]
    optional_kriterien = ["A_Note", "Abzug"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={
                "wartet_auf_richter": float(inp.expected_judges - len(inp.judge_values)),
            })
        d_notes = [v["D_Note"] for v in inp.judge_values if "D_Note" in v]
        e_notes = [v["E_Note"] for v in inp.judge_values if "E_Note" in v]
        a_notes = [v["A_Note"] for v in inp.judge_values if "A_Note" in v]
        abzuege = [v.get("Abzug", 0.0) for v in inp.judge_values]

        d = _avg(d_notes)
        e = _avg_trim(e_notes)
        a = _avg(a_notes)
        abzug = _avg(abzuege)

        score = (d + a + e - abzug) * inp.faktor + inp.offset
        breakdown = {
            "D_Note": round(d, 3),
            "E_Note_Schnitt_Trim": round(e, 3),
            "Abzug": round(abzug, 3),
        }
        if a_notes:
            breakdown["A_Note"] = round(a, 3)
        return ScoringResult(score=round(score, 3), breakdown=breakdown)
