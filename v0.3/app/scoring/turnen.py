from .base import ScoringStrategy, ScoringInput, ScoringResult


def _avg_e_with_trim(e_notes: list[float]) -> float:
    if not e_notes:
        return 0.0
    if len(e_notes) >= 3:
        trimmed = sorted(e_notes)[1:-1]
    else:
        trimmed = e_notes
    return sum(trimmed) / len(trimmed)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class TurnenOlympicTrim(ScoringStrategy):
    code = "TURNEN_OLYMPIC_TRIM"
    label = "Turnen Olympisch (E-Note Trim)"
    required_kriterien = ["D_Note", "E_Note"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={
                "wartet_auf_richter": float(inp.expected_judges - len(inp.judge_values)),
            })
        d_notes = [v["D_Note"] for v in inp.judge_values if "D_Note" in v]
        e_notes = [v["E_Note"] for v in inp.judge_values if "E_Note" in v]
        abzuege = [v.get("Abzug", 0.0) for v in inp.judge_values]

        d = _avg(d_notes)              # D-Note ist meist gleich, Schnitt schadet nicht
        e = _avg_e_with_trim(e_notes)
        abzug = _avg(abzuege)

        score = (d + e - abzug) * inp.faktor + inp.offset
        return ScoringResult(score=round(score, 3), breakdown={
            "D_Note": round(d, 3),
            "E_Note_Schnitt_Trim": round(e, 3),
            "Abzug": round(abzug, 3),
        })


class TurnenAvg(ScoringStrategy):
    code = "TURNEN_AVG"
    label = "Turnen Schnitt aller Wertungen"
    required_kriterien = ["D_Note", "E_Note"]

    def compute(self, inp: ScoringInput) -> ScoringResult:
        if len(inp.judge_values) < inp.expected_judges:
            return ScoringResult(score=None, breakdown={
                "wartet_auf_richter": float(inp.expected_judges - len(inp.judge_values)),
            })
        d_notes = [v["D_Note"] for v in inp.judge_values if "D_Note" in v]
        e_notes = [v["E_Note"] for v in inp.judge_values if "E_Note" in v]
        abzuege = [v.get("Abzug", 0.0) for v in inp.judge_values]

        d = _avg(d_notes)
        e = _avg(e_notes)
        abzug = _avg(abzuege)

        score = (d + e - abzug) * inp.faktor + inp.offset
        return ScoringResult(score=round(score, 3), breakdown={
            "D_Note": round(d, 3),
            "E_Note_Schnitt": round(e, 3),
            "Abzug": round(abzug, 3),
        })
