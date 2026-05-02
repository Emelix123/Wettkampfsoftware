from pydantic import BaseModel, ConfigDict
from typing import Optional

# Das schickt das React-Frontend (z.B. Kampfrichter tippt Wert ein)
class ErgebnisCreate(BaseModel):
    Personen_idPersonen: int
    Wettkampf_idWettkampf: int
    Geraete_idGeraete: int
    Versuch_Nr: int
    Wert: float
    Ist_Gueltig: bool = True

# Das schickt die API an React zurück (inklusive DB-ID und Score)
class ErgebnisResponse(ErgebnisCreate):
    idEinzel_Ergebnis: int
    Score: float
    Status: str

    model_config = ConfigDict(from_attributes=True) # Wichtig für SQLAlchemy