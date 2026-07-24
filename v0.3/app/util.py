"""Kleine, wiederverwendbare Helfer ohne DB-/Framework-Abhaengigkeiten."""
from datetime import date, datetime
from typing import Optional


def parse_birthdate(value: Optional[str]) -> Optional[date]:
    """Parst ein Geburtsdatum tolerant. Akzeptiert:
        * leer / None          -> None
        * ISO 'JJJJ-MM-TT'
        * deutsch 'TT.MM.JJJJ' oder 'TT/MM/JJJJ'
        * nur Jahr 'JJJJ'      -> 1. Januar des Jahres

    Bei der Meldung reicht oft das Geburtsjahr (Altersklassen richten sich
    nach dem Jahrgang). Ein reines Jahr wird deshalb als 1. Januar gespeichert.

    Wirft ValueError nur, wenn gar kein Format passt — die Aufrufer fangen das
    ab und zeigen eine freundliche Meldung statt eines 500ers.
    """
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    # Nur Jahrgang (z.B. "2015")
    if s.isdigit() and len(s) == 4:
        year = int(s)
        if 1900 <= year <= date.today().year:
            return date(year, 1, 1)
        raise ValueError(f"Jahr {year} ist unplausibel.")
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Letzter Versuch: Pythons ISO-Parser (nimmt in 3.11+ mehr Varianten)
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"Geburtsdatum '{s}' nicht erkannt (Format: JJJJ-MM-TT oder nur JJJJ).")
