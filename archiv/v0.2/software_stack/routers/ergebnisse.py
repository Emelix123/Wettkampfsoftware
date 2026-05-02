from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
from services import scoring

router = APIRouter(
    prefix="/ergebnisse",
    tags=["Ergebnisse"]
)

@router.post("/", response_model=schemas.ErgebnisResponse)
def erstelle_ergebnis(ergebnis_in: schemas.ErgebnisCreate, db: Session = Depends(get_db)):
    
    # 1. Roh-Ergebnis in die DB schreiben (Wert speichern, Score ist 0)
    db_ergebnis = crud.create_einzel_ergebnis(db, ergebnis_in)
    
    # 2. In einer echten App würdest du jetzt über Geraete_has_Wettkampf 
    #    die Faktoren (Faktor, Offset, RegelKuerzel) aus der DB holen.
    #    Hier als Dummy-Werte für das Beispiel:
    dummy_kuerzel = "LA_SPRINT"
    dummy_faktor = 1.0
    dummy_offset = 30.0
    
    if ergebnis_in.Ist_Gueltig:
        # 3. Berechnung starten und Score updaten
        db_ergebnis = scoring.process_new_result(
            db=db, 
            ergebnis_id=db_ergebnis.idEinzel_Ergebnis,
            wert=ergebnis_in.Wert,
            regel_kuerzel=dummy_kuerzel,
            faktor=dummy_faktor,
            offset=dummy_offset
        )
        
    return db_ergebnis