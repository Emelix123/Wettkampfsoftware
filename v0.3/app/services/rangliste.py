"""Helper rund um die VIEWs vw_Rangliste_Einzel und vw_Mannschaft_Score_All."""
from sqlalchemy import text
from sqlalchemy.orm import Session


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
