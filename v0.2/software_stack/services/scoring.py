from sqlalchemy.orm import Session
import crud

# --- 1. Die Berechnungs-Regeln (Sportart-spezifisch) ---

def calc_la_sprint(wert: float, faktor: float, offset: float) -> float:
    # Leichtathletik Sprint: Score = Offset - (Wert * Faktor). 
    score = offset - (wert * faktor)
    return max(0.0, score) # Keine Minuspunkte

def calc_la_weite(wert: float, faktor: float, offset: float) -> float:
    # Leichtathletik Weite: Score = Wert * Faktor
    return wert * faktor

def calc_manuell(wert: float, faktor: float, offset: float) -> float:
    # Wert IST der Score
    return wert

# --- 2. Das Mapping (DB Kuerzel -> Python Funktion) ---
SCORING_STRATEGIES = {
    "LA_SPRINT": calc_la_sprint,
    "LA_WEITE": calc_la_weite,
    "MANUELL": calc_manuell
}

# --- 3. Der Haupt-Service (Wird von der API aufgerufen) ---
def process_new_result(db: Session, ergebnis_id: int, wert: float, regel_kuerzel: str, faktor: float, offset: float):
    # 1. Passende Berechnungsfunktion finden
    calc_func = SCORING_STRATEGIES.get(regel_kuerzel)
    
    if not calc_func:
        raise ValueError(f"Unbekanntes Regel-Kürzel: {regel_kuerzel}")
    
    # 2. Score berechnen
    calculated_score = calc_func(wert, faktor, offset)
    
    # 3. Score in der DB speichern
    updated_ergebnis = crud.update_score(db, ergebnis_id, calculated_score)
    
    # 4. HIER SPÄTER: Person_Geraet_Ergebnis aktualisieren (bester Score)
    # 5. HIER SPÄTER: Gesamt_Ergebnis (Gesamtscore) aktualisieren
    
    return updated_ergebnis