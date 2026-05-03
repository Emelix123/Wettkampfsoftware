from datetime import date, datetime, time
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, LargeBinary, Time, Enum, ForeignKey,
    JSON, Numeric, SmallInteger, UniqueConstraint, ForeignKeyConstraint, text,
)
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database import Base


class Verein(Base):
    __tablename__ = "Verein"
    idVerein: Mapped[int] = mapped_column(primary_key=True)
    Kuerzel: Mapped[str] = mapped_column(String(10), unique=True)
    Name: Mapped[str] = mapped_column(String(120))
    Ort: Mapped[Optional[str]] = mapped_column(String(80))
    Logo: Mapped[Optional[bytes]] = mapped_column(MEDIUMBLOB, nullable=True)
    Logo_MimeType: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)


class Altersklasse(Base):
    __tablename__ = "Altersklasse"
    idAltersklasse: Mapped[int] = mapped_column(primary_key=True)
    Kuerzel: Mapped[str] = mapped_column(String(15), unique=True)
    Bezeichnung: Mapped[str] = mapped_column(String(60))
    Alter_Von: Mapped[Optional[int]]
    Alter_Bis: Mapped[Optional[int]]
    Geschlecht: Mapped[str] = mapped_column(
        Enum("m", "w", "d", "alle"), default="alle"
    )


class WettkampfTag(Base):
    __tablename__ = "Wettkampf_Tag"
    idWettkampf_Tag: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(120))
    Wettkampf_Datum: Mapped[date]
    Ort: Mapped[Optional[str]] = mapped_column(String(120))
    Veranstalter: Mapped[Optional[str]] = mapped_column(String(120))
    Erstellt_Am: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    Logo: Mapped[Optional[bytes]] = mapped_column(MEDIUMBLOB, nullable=True)
    Logo_MimeType: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    wettkaempfe: Mapped[List["Wettkampf"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class Wettkampf(Base):
    __tablename__ = "Wettkampf"
    idWettkampf: Mapped[int] = mapped_column(primary_key=True)
    Wettkampf_Tag_id: Mapped[int] = mapped_column(ForeignKey("Wettkampf_Tag.idWettkampf_Tag"))
    Wettkampf_Nr: Mapped[int]
    Name: Mapped[str] = mapped_column(String(120))
    Altersklasse_id: Mapped[int] = mapped_column(ForeignKey("Altersklasse.idAltersklasse"))
    Status: Mapped[str] = mapped_column(
        Enum("Entwurf", "Anmeldung", "Aktiv", "Abgeschlossen", "Archiviert"),
        default="Entwurf",
    )
    Typ: Mapped[str] = mapped_column(
        Enum("Einzel", "Mannschaft", "Kombination"), default="Einzel"
    )
    Mannschaft_Groesse: Mapped[Optional[int]]

    tag: Mapped[WettkampfTag] = relationship(back_populates="wettkaempfe")
    altersklasse: Mapped[Altersklasse] = relationship()
    geraete_zuordnung: Mapped[List["GeraeteHasWettkampf"]] = relationship(
        back_populates="wettkampf", cascade="all, delete-orphan"
    )
    riegen: Mapped[List["Riege"]] = relationship(back_populates="wettkampf", cascade="all, delete-orphan")
    mannschaften: Mapped[List["Mannschaft"]] = relationship(back_populates="wettkampf", cascade="all, delete-orphan")
    anmeldungen: Mapped[List["PersonenHasWettkampf"]] = relationship(back_populates="wettkampf", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("Wettkampf_Nr", "Wettkampf_Tag_id"),)


class Riege(Base):
    __tablename__ = "Riege"
    idRiege: Mapped[int] = mapped_column(primary_key=True)
    Wettkampf_id: Mapped[int] = mapped_column(ForeignKey("Wettkampf.idWettkampf"))
    Bezeichnung: Mapped[str] = mapped_column(String(60))
    Start_Zeit: Mapped[Optional[time]]

    wettkampf: Mapped[Wettkampf] = relationship(back_populates="riegen")


class Mannschaft(Base):
    __tablename__ = "Mannschaft"
    idMannschaft: Mapped[int] = mapped_column(primary_key=True)
    Wettkampf_id: Mapped[int] = mapped_column(ForeignKey("Wettkampf.idWettkampf"))
    Name: Mapped[str] = mapped_column(String(120))
    Verein_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Verein.idVerein"))

    wettkampf: Mapped[Wettkampf] = relationship(back_populates="mannschaften")
    verein: Mapped[Optional[Verein]] = relationship()


class Geraete(Base):
    __tablename__ = "Geraete"
    idGeraete: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(60), unique=True)
    Einheit: Mapped[str] = mapped_column(String(20), default="Pkt")
    Beschreibung: Mapped[Optional[str]] = mapped_column(String(255))


class BerechnungsArt(Base):
    __tablename__ = "Berechnungs_Art"
    idBerechnungs_Art: Mapped[int] = mapped_column(primary_key=True)
    Regel_Kuerzel: Mapped[str] = mapped_column(String(60), unique=True)
    Bezeichnung: Mapped[str] = mapped_column(String(120))
    Beschreibung: Mapped[Optional[str]] = mapped_column(String(255))


class GeraeteHasWettkampf(Base):
    __tablename__ = "Geraete_has_Wettkampf"
    idGhW: Mapped[int] = mapped_column(primary_key=True)
    Wettkampf_id: Mapped[int] = mapped_column(ForeignKey("Wettkampf.idWettkampf"))
    Geraete_id: Mapped[int] = mapped_column(ForeignKey("Geraete.idGeraete"))
    Reihenfolge: Mapped[int] = mapped_column(default=1)
    Anzahl_Versuche: Mapped[int] = mapped_column(default=1)
    Berechnungs_Art_id: Mapped[int] = mapped_column(ForeignKey("Berechnungs_Art.idBerechnungs_Art"))
    Score_Faktor: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0)
    Score_Offset: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0)
    Erwartete_Kampfrichter: Mapped[int] = mapped_column(default=1)

    wettkampf: Mapped[Wettkampf] = relationship(back_populates="geraete_zuordnung")
    geraet: Mapped[Geraete] = relationship()
    berechnung: Mapped[BerechnungsArt] = relationship()

    __table_args__ = (UniqueConstraint("Wettkampf_id", "Geraete_id"),)


class Personen(Base):
    __tablename__ = "Personen"
    idPersonen: Mapped[int] = mapped_column(primary_key=True)
    Vorname: Mapped[str] = mapped_column(String(60))
    Nachname: Mapped[str] = mapped_column(String(60))
    Geburtsdatum: Mapped[Optional[date]]
    Verein_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Verein.idVerein"))
    Geschlecht: Mapped[Optional[str]] = mapped_column(Enum("m", "w", "d"))

    verein: Mapped[Optional[Verein]] = relationship()


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        Enum("admin", "tisch", "kampfrichter", "viewer"), default="viewer"
    )
    Personen_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Personen.idPersonen"))
    is_active: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    last_login: Mapped[Optional[datetime]]


class PersonenHasWettkampf(Base):
    __tablename__ = "Personen_has_Wettkampf"
    Personen_id: Mapped[int] = mapped_column(ForeignKey("Personen.idPersonen"), primary_key=True)
    Wettkampf_id: Mapped[int] = mapped_column(ForeignKey("Wettkampf.idWettkampf"), primary_key=True)
    Startnummer: Mapped[Optional[int]]
    Riege_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Riege.idRiege"))
    Mannschaft_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Mannschaft.idMannschaft"))
    Start_Status: Mapped[str] = mapped_column(
        Enum("Gemeldet", "Gestartet", "Zurueckgezogen", "Disqualifiziert"),
        default="Gemeldet",
    )
    Status_Grund: Mapped[Optional[str]] = mapped_column(String(255))
    Angemeldet_Am: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    person: Mapped[Personen] = relationship()
    wettkampf: Mapped[Wettkampf] = relationship(back_populates="anmeldungen")
    riege: Mapped[Optional[Riege]] = relationship()
    mannschaft: Mapped[Optional[Mannschaft]] = relationship()


class EinzelErgebnis(Base):
    __tablename__ = "Einzel_Ergebnis"
    idEinzel_Ergebnis: Mapped[int] = mapped_column(primary_key=True)
    Personen_id: Mapped[int]
    Wettkampf_id: Mapped[int]
    Geraete_id: Mapped[int]
    Versuch_Nr: Mapped[int] = mapped_column(default=1)
    Score: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    Ist_Gueltig: Mapped[int] = mapped_column(SmallInteger, default=1)
    Status: Mapped[str] = mapped_column(
        Enum("Offen", "In_Bewertung", "Freigegeben"), default="Offen"
    )
    Erfasst_Am: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    Updated_At: Mapped[Optional[datetime]] = mapped_column(
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )
    Erfasst_Von: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))

    wertungen: Mapped[List["KampfrichterWertung"]] = relationship(
        back_populates="ergebnis", cascade="all, delete-orphan"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["Personen_id", "Wettkampf_id"],
            ["Personen_has_Wettkampf.Personen_id", "Personen_has_Wettkampf.Wettkampf_id"],
        ),
        ForeignKeyConstraint(
            ["Wettkampf_id", "Geraete_id"],
            ["Geraete_has_Wettkampf.Wettkampf_id", "Geraete_has_Wettkampf.Geraete_id"],
        ),
        UniqueConstraint("Personen_id", "Wettkampf_id", "Geraete_id", "Versuch_Nr"),
    )


class KampfrichterWertung(Base):
    __tablename__ = "Kampfrichter_Wertung"
    idWertung: Mapped[int] = mapped_column(primary_key=True)
    Einzel_Ergebnis_id: Mapped[int] = mapped_column(ForeignKey("Einzel_Ergebnis.idEinzel_Ergebnis"))
    Richter_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    Richter_Slot: Mapped[int] = mapped_column(default=1)
    Erfasst_Von: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    Erfasst_Am: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))

    ergebnis: Mapped[EinzelErgebnis] = relationship(back_populates="wertungen")
    details: Mapped[List["KampfrichterWertungDetail"]] = relationship(
        back_populates="wertung", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("Einzel_Ergebnis_id", "Richter_Slot"),)


class KampfrichterWertungDetail(Base):
    __tablename__ = "Kampfrichter_Wertung_Detail"
    idDetail: Mapped[int] = mapped_column(primary_key=True)
    Wertung_id: Mapped[int] = mapped_column(ForeignKey("Kampfrichter_Wertung.idWertung"))
    Kriterium: Mapped[str] = mapped_column(String(50))
    Wert: Mapped[float] = mapped_column(Numeric(10, 3))

    wertung: Mapped[KampfrichterWertung] = relationship(back_populates="details")

    __table_args__ = (UniqueConstraint("Wertung_id", "Kriterium"),)


class AuditLog(Base):
    __tablename__ = "Audit_Log"
    idAudit_Log: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    username: Mapped[Optional[str]] = mapped_column(String(80))
    aktion: Mapped[str] = mapped_column(String(80))
    ziel_typ: Mapped[Optional[str]] = mapped_column(String(40))
    ziel_id: Mapped[Optional[str]] = mapped_column(String(60))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    zeitpunkt: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
