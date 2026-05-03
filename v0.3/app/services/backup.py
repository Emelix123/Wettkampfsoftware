"""JSON-Snapshot eines Wettkampftags inklusive aller Wettkaempfe,
Anmeldungen, Riegen, Mannschaften, Versuche und Wertungen.

Format: ein dict, in eine .json-Datei serialisierbar.
Wiederherstellen ist nicht eingebaut (das wuerde IDs neu erzeugen muessen
und Konflikte mit bestehenden Daten haben). Die Datei dient als
Beweisstueck / Notfall-Wiederherstellung per Hand.
"""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy.orm import Session

from models import (
    WettkampfTag, Wettkampf, Riege, Mannschaft, GeraeteHasWettkampf,
    PersonenHasWettkampf, EinzelErgebnis, KampfrichterWertung,
)


def _ser(o):
    if isinstance(o, (date, datetime, time)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    if hasattr(o, "__dict__"):
        return {k: v for k, v in o.__dict__.items() if not k.startswith("_")}
    return str(o)


def snapshot_tag(db: Session, tag_id: int) -> dict:
    tag = db.get(WettkampfTag, tag_id)
    if not tag:
        return {}
    out = {
        "exported_at": datetime.utcnow().isoformat(),
        "schema_version": "v0.3",
        "wettkampf_tag": {
            "id": tag.idWettkampf_Tag,
            "name": tag.Name,
            "datum": str(tag.Wettkampf_Datum),
            "ort": tag.Ort,
            "veranstalter": tag.Veranstalter,
        },
        "wettkaempfe": [],
    }
    for w in tag.wettkaempfe:
        wk_block = {
            "id": w.idWettkampf, "nr": w.Wettkampf_Nr, "name": w.Name,
            "altersklasse": w.altersklasse.Kuerzel if w.altersklasse else None,
            "status": w.Status, "typ": w.Typ,
            "mannschaft_groesse": w.Mannschaft_Groesse,
            "geraete": [], "riegen": [], "mannschaften": [],
            "anmeldungen": [], "ergebnisse": [],
        }
        for g in w.geraete_zuordnung:
            wk_block["geraete"].append({
                "id_ghw": g.idGhW,
                "geraet": g.geraet.Name,
                "berechnung": g.berechnung.Regel_Kuerzel,
                "reihenfolge": g.Reihenfolge,
                "anzahl_versuche": g.Anzahl_Versuche,
                "erwartete_kampfrichter": g.Erwartete_Kampfrichter,
                "score_faktor": float(g.Score_Faktor),
                "score_offset": float(g.Score_Offset),
            })
        for r in w.riegen:
            wk_block["riegen"].append({
                "id": r.idRiege, "bezeichnung": r.Bezeichnung,
                "start_zeit": str(r.Start_Zeit) if r.Start_Zeit else None,
            })
        for m in w.mannschaften:
            wk_block["mannschaften"].append({
                "id": m.idMannschaft, "name": m.Name,
                "verein_kuerzel": m.verein.Kuerzel if m.verein else None,
            })
        for a in w.anmeldungen:
            wk_block["anmeldungen"].append({
                "person": f"{a.person.Vorname} {a.person.Nachname}",
                "verein": a.person.verein.Kuerzel if a.person.verein else None,
                "geburtsdatum": str(a.person.Geburtsdatum) if a.person.Geburtsdatum else None,
                "startnummer": a.Startnummer,
                "riege": a.riege.Bezeichnung if a.riege else None,
                "mannschaft": a.mannschaft.Name if a.mannschaft else None,
                "status": a.Start_Status, "status_grund": a.Status_Grund,
            })

        ergebnisse = (
            db.query(EinzelErgebnis)
            .filter_by(Wettkampf_id=w.idWettkampf)
            .order_by(EinzelErgebnis.Personen_id, EinzelErgebnis.Geraete_id,
                      EinzelErgebnis.Versuch_Nr)
            .all()
        )
        for ee in ergebnisse:
            block = {
                "person_id": ee.Personen_id,
                "geraet_id": ee.Geraete_id,
                "versuch_nr": ee.Versuch_Nr,
                "score": float(ee.Score) if ee.Score is not None else None,
                "ist_gueltig": bool(ee.Ist_Gueltig),
                "status": ee.Status,
                "erfasst_am": str(ee.Erfasst_Am),
                "wertungen": [],
            }
            for kw in ee.wertungen:
                block["wertungen"].append({
                    "slot": kw.Richter_Slot,
                    "richter_user_id": kw.Richter_user_id,
                    "details": {d.Kriterium: float(d.Wert) for d in kw.details},
                })
            wk_block["ergebnisse"].append(block)
        out["wettkaempfe"].append(wk_block)
    return out
