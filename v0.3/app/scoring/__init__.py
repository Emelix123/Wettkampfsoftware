"""Scoring engine.

Jeder Wettkampf weist seinen Geraeten eine Berechnungs_Art zu (z.B.
"TURNEN_OLYMPIC_TRIM"). Hier wird das Kuerzel auf eine Strategy-Klasse
gemappt, die aus den Kampfrichter-Wertungen einen finalen Score macht.

Eine Strategy beschreibt:
  * required_kriterien: welche Felder pro Wertung Pflicht sind
                        (z.B. ["D_Note", "E_Note"] oder ["Wert"])
  * compute(values, faktor, offset, expected_judges) -> Optional[float]
        values: List[Dict[Kriterium, Wert]] — eine Dict je Richter
        Returns None wenn noch nicht genug Wertungen da sind.
"""

from .base import ScoringStrategy, ScoringInput, ScoringResult
from .turnen import TurnenOlympicTrim, TurnenAvg
from .leichtathletik import LaDirect, LaSprint
from .manuell import Manuell

REGISTRY: dict[str, ScoringStrategy] = {
    "TURNEN_OLYMPIC_TRIM": TurnenOlympicTrim(),
    "TURNEN_AVG":          TurnenAvg(),
    "LA_DIRECT":           LaDirect(),
    "LA_SPRINT":           LaSprint(),
    "MANUELL":             Manuell(),
}


def get_strategy(regel_kuerzel: str) -> ScoringStrategy:
    s = REGISTRY.get(regel_kuerzel)
    if not s:
        raise ValueError(f"Unbekanntes Berechnungs-Kuerzel: {regel_kuerzel}")
    return s
