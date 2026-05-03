"""Berechnet den Score eines Versuchs aus den vorhandenen Richter-Wertungen
und speichert ihn in Einzel_Ergebnis."""
from sqlalchemy.orm import Session

from models import (
    EinzelErgebnis, GeraeteHasWettkampf, KampfrichterWertung,
)
from scoring import get_strategy
from scoring.base import ScoringInput


def recalc_alle_versuche_fuer_ghw(db: Session, ghw: GeraeteHasWettkampf) -> int:
    """Rechnet ALLE bestehenden Versuche fuer ein Geraet+Wettkampf neu durch.
    Wird gebraucht wenn der Admin nachtraeglich Faktor / Offset / Berechnungs-Art
    aendert. Returns: Anzahl der neu berechneten Versuche."""
    versuche = (
        db.query(EinzelErgebnis)
        .filter_by(Wettkampf_id=ghw.Wettkampf_id, Geraete_id=ghw.Geraete_id)
        .all()
    )
    for ee in versuche:
        recalc_versuch(db, ee)
    return len(versuche)


def recalc_versuch(db: Session, ergebnis: EinzelErgebnis) -> EinzelErgebnis:
    ghw = (
        db.query(GeraeteHasWettkampf)
        .filter_by(Wettkampf_id=ergebnis.Wettkampf_id, Geraete_id=ergebnis.Geraete_id)
        .one()
    )
    strategy = get_strategy(ghw.berechnung.Regel_Kuerzel)

    wertungen = (
        db.query(KampfrichterWertung)
        .filter_by(Einzel_Ergebnis_id=ergebnis.idEinzel_Ergebnis)
        .all()
    )

    judge_values: list[dict[str, float]] = []
    for w in wertungen:
        d = {detail.Kriterium: float(detail.Wert) for detail in w.details}
        judge_values.append(d)

    if not ergebnis.Ist_Gueltig:
        ergebnis.Score = 0.0
        ergebnis.Status = "Freigegeben"
        db.commit()
        db.refresh(ergebnis)
        return ergebnis

    result = strategy.compute(
        ScoringInput(
            judge_values=judge_values,
            faktor=float(ghw.Score_Faktor),
            offset=float(ghw.Score_Offset),
            expected_judges=ghw.Erwartete_Kampfrichter,
        )
    )

    if result.score is None:
        ergebnis.Status = "In_Bewertung"
        ergebnis.Score = None
    else:
        ergebnis.Score = result.score
        ergebnis.Status = "Freigegeben"

    db.commit()
    db.refresh(ergebnis)
    return ergebnis
