"""Helper rund um die VIEWs vw_Rangliste_Einzel und vw_Mannschaft_Score_All."""
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from models import Geraete, GeraeteHasWettkampf


def riegen_fortschritt(db: Session, wettkampf_id: int) -> dict:
    """Gibt fuer jede Riege im Wettkampf zurueck: an welchen Geraeten wieviele
    Versuche schon eingetragen sind. Zur 'Wo ist welche Riege gerade'-Anzeige.
    Returns: {riege_id: {'bezeichnung': str, 'start_zeit': time|None,
                          'mitglieder': int, 'pro_geraet': {geraet_id: count}}}
    """
    rows = db.execute(text("""
        SELECT
            phw.Riege_id, COUNT(DISTINCT phw.Personen_id) AS mitglieder
        FROM Personen_has_Wettkampf phw
        WHERE phw.Wettkampf_id = :wid
          AND phw.Riege_id IS NOT NULL
        GROUP BY phw.Riege_id
    """), {"wid": wettkampf_id}).mappings().all()
    mitglieder = {r["Riege_id"]: r["mitglieder"] for r in rows}

    rows = db.execute(text("""
        SELECT
            phw.Riege_id, ee.Geraete_id,
            COUNT(DISTINCT ee.Personen_id) AS personen_mit_versuch
        FROM Einzel_Ergebnis ee
        JOIN Personen_has_Wettkampf phw
              ON phw.Personen_id   = ee.Personen_id
             AND phw.Wettkampf_id  = ee.Wettkampf_id
        WHERE ee.Wettkampf_id = :wid
          AND phw.Riege_id IS NOT NULL
        GROUP BY phw.Riege_id, ee.Geraete_id
    """), {"wid": wettkampf_id}).mappings().all()
    pro_geraet: dict = {}
    for r in rows:
        pro_geraet.setdefault(r["Riege_id"], {})[r["Geraete_id"]] = r["personen_mit_versuch"]

    from models import Riege
    riegen = (
        db.query(Riege).filter_by(Wettkampf_id=wettkampf_id)
        .order_by(Riege.Start_Zeit, Riege.Bezeichnung).all()
    )
    out = {}
    for r in riegen:
        out[r.idRiege] = {
            "bezeichnung": r.Bezeichnung,
            "start_zeit": r.Start_Zeit,
            "mitglieder": mitglieder.get(r.idRiege, 0),
            "pro_geraet": pro_geraet.get(r.idRiege, {}),
        }
    return out


def einzel_rangliste(db: Session, wettkampf_id: int) -> list[dict]:
    rows = db.execute(text("""
        SELECT Platz, Personen_id, Vorname, Nachname, Geschlecht,
               Verein_Kuerzel, Verein_Name,
               GesamtScore, Anzahl_Geraete_Gewertet
        FROM vw_Rangliste_Einzel
        WHERE Wettkampf_id = :wid
        ORDER BY Platz, Nachname
    """), {"wid": wettkampf_id}).mappings().all()
    return [dict(r) for r in rows]


def geraete_des_wettkampfs(db: Session, wettkampf_id: int) -> list[Geraete]:
    """Geraete in der Reihenfolge wie sie im Wettkampf zugeordnet sind."""
    rows = (
        db.query(Geraete, GeraeteHasWettkampf.Reihenfolge)
        .join(GeraeteHasWettkampf, GeraeteHasWettkampf.Geraete_id == Geraete.idGeraete)
        .filter(GeraeteHasWettkampf.Wettkampf_id == wettkampf_id)
        .order_by(GeraeteHasWettkampf.Reihenfolge)
        .all()
    )
    return [r[0] for r in rows]


def einzel_rangliste_mit_geraeten(db: Session, wettkampf_id: int) -> tuple[list[dict], list[Geraete]]:
    """Gibt (rangliste, geraete) zurueck. Jede Zeile enthaelt zusaetzlich
    `geraete_scores`: dict[geraet_id, BesterScore | None]."""
    geraete = geraete_des_wettkampfs(db, wettkampf_id)
    base = einzel_rangliste(db, wettkampf_id)
    if not base:
        return base, geraete
    pids = [r["Personen_id"] for r in base]
    rows = db.execute(
        text("""
            SELECT Personen_id, Geraete_id, BesterScore
            FROM vw_Person_Geraet_Best
            WHERE Wettkampf_id = :wid
              AND Personen_id IN :pids
        """).bindparams(bindparam('pids', expanding=True)),
        {"wid": wettkampf_id, "pids": pids},
    ).mappings().all()
    by_pid: dict[int, dict[int, float]] = {}
    for r in rows:
        by_pid.setdefault(r["Personen_id"], {})[r["Geraete_id"]] = float(r["BesterScore"])
    out = []
    for r in base:
        scores = by_pid.get(r["Personen_id"], {})
        r2 = dict(r)
        r2["geraete_scores"] = {g.idGeraete: scores.get(g.idGeraete) for g in geraete}
        out.append(r2)
    return out, geraete


def mannschaft_rangliste(db: Session, wettkampf_id: int, top_n: int | None) -> list[dict]:
    """Wenn top_n gesetzt: Backend summiert die besten N pro Team aus
    vw_Gesamt_Ergebnisse selbst (statt der View vw_Mannschaft_Score_All).
    """
    if top_n is None:
        rows = db.execute(text("""
            SELECT idMannschaft, Mannschaft_Name,
                   IFNULL(GesamtScore_Alle, 0) AS GesamtScore,
                   Mitglieder_Gesamt
            FROM vw_Mannschaft_Score_All
            WHERE Wettkampf_id = :wid
            ORDER BY GesamtScore DESC
        """), {"wid": wettkampf_id}).mappings().all()
        return [dict(r, Platz=i+1) for i, r in enumerate(rows)]
    # Top-N: hol je Mitglied den GesamtScore und summiere die besten N pro Team
    rows = db.execute(text("""
        SELECT m.idMannschaft, m.Name AS Mannschaft_Name,
               COUNT(g.Personen_id) AS Mitglieder_Gesamt,
               g.Personen_id, g.GesamtScore
        FROM Mannschaft m
        LEFT JOIN Personen_has_Wettkampf phw
               ON phw.Mannschaft_id = m.idMannschaft
              AND phw.Wettkampf_id  = m.Wettkampf_id
        LEFT JOIN vw_Gesamt_Ergebnisse g
               ON g.Personen_id  = phw.Personen_id
              AND g.Wettkampf_id = phw.Wettkampf_id
        WHERE m.Wettkampf_id = :wid
        GROUP BY m.idMannschaft, m.Name, g.Personen_id, g.GesamtScore
    """), {"wid": wettkampf_id}).mappings().all()

    by_team: dict[int, dict] = {}
    for r in rows:
        team = by_team.setdefault(r["idMannschaft"], {
            "idMannschaft": r["idMannschaft"],
            "Mannschaft_Name": r["Mannschaft_Name"],
            "scores": [],
            "Mitglieder_Gesamt": 0,
        })
        if r["GesamtScore"] is not None:
            team["scores"].append(float(r["GesamtScore"]))
            team["Mitglieder_Gesamt"] += 1

    result = []
    for t in by_team.values():
        sorted_scores = sorted(t["scores"], reverse=True)[:top_n]
        result.append({
            "idMannschaft": t["idMannschaft"],
            "Mannschaft_Name": t["Mannschaft_Name"],
            "Mitglieder_Gesamt": t["Mitglieder_Gesamt"],
            "GesamtScore": round(sum(sorted_scores), 3),
        })
    result.sort(key=lambda x: x["GesamtScore"], reverse=True)
    for i, r in enumerate(result):
        r["Platz"] = i + 1
    return result
