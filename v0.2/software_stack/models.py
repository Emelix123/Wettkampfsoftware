from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base

class EinzelErgebnis(Base):
    __tablename__ = "Einzel_Ergebnis"

    idEinzel_Ergebnis = Column(Integer, primary_key=True, index=True)
    Personen_idPersonen = Column(Integer, nullable=False)
    Wettkampf_idWettkampf = Column(Integer, nullable=False)
    Geraete_idGeraete = Column(Integer, nullable=False)
    Versuch_Nr = Column(Integer, default=1)
    Wert = Column(Float, nullable=True)
    Score = Column(Float, default=0.0)
    Ist_Gueltig = Column(Boolean, default=True)
    Status = Column(Enum('Ausstehend','In_Bewertung','Freigegeben'), default='Ausstehend')

class BerechnungsArt(Base):
    __tablename__ = "Berechnungs_Art"
    idBerechnungs_Art = Column(Integer, primary_key=True)
    Regel_Kuerzel = Column(String(50), unique=True)