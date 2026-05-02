from sqlalchemy.orm import Session
import models
import schemas

def create_einzel_ergebnis(db: Session, ergebnis: schemas.ErgebnisCreate):
    db_ergebnis = models.EinzelErgebnis(
        Personen_idPersonen=ergebnis.Personen_idPersonen,
        Wettkampf_idWettkampf=ergebnis.Wettkampf_idWettkampf,
        Geraete_idGeraete=ergebnis.Geraete_idGeraete,
        Versuch_Nr=ergebnis.Versuch_Nr,
        Wert=ergebnis.Wert,
        Ist_Gueltig=ergebnis.Ist_Gueltig,
        Status='Freigegeben'
    )
    db.add(db_ergebnis)
    db.commit()
    db.refresh(db_ergebnis)
    return db_ergebnis

def update_score(db: Session, ergebnis_id: int, new_score: float):
    db_ergebnis = db.query(models.EinzelErgebnis).filter(models.EinzelErgebnis.idEinzel_Ergebnis == ergebnis_id).first()
    if db_ergebnis:
        db_ergebnis.Score = new_score
        db.commit()
        db.refresh(db_ergebnis)
    return db_ergebnis

# Hier kommen später Abfragen wie: get_bester_versuch(...), get_rangliste(...) rein.