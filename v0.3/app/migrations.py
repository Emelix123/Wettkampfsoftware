"""Idempotente Schema-Migrationen beim App-Start.

Hintergrund: Die SQL-Skripte in /docker-entrypoint-initdb.d laufen NUR beim
allerersten Start mit leerem Volume. Wer ein bestehendes DB-Volume von einer
aelteren Version (z.B. v0.3) weiterverwendet, bekommt neue Spalten wie
user.Verein_id sonst nie — und die App antwortet dann mit 500ern
("Unknown column 'user.Verein_id'"), z.B. direkt beim Login.

Deshalb prueft die App hier bei jedem Start per INFORMATION_SCHEMA, ob alle
Spalten existieren, die die SQLAlchemy-Models erwarten, und legt fehlende
selbst an. Jede Operation ist idempotent — mehrfaches Ausfuehren ist ok.
"""
from sqlalchemy import text

from database import engine


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ),
        {"t": table, "c": column},
    ).first())


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
        ),
        {"t": table},
    ).first())


def _constraint_exists(conn, table: str, name: str) -> bool:
    return bool(conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = :t AND CONSTRAINT_NAME = :n"
        ),
        {"t": table, "n": name},
    ).first())


def _add_column(conn, table: str, column: str, ddl_rest: str) -> bool:
    """Legt die Spalte an, wenn sie fehlt. Returns True wenn angelegt."""
    if _column_exists(conn, table, column):
        return False
    conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl_rest}"))
    return True


# (Tabelle, Spalte, DDL) — alles was aeltere Volumes evtl. noch nicht haben.
_COLUMNS = [
    # 05_logos.sql
    ("Verein",        "Logo",          "MEDIUMBLOB NULL"),
    ("Verein",        "Logo_MimeType", "VARCHAR(60) NULL"),
    ("Wettkampf_Tag", "Logo",          "MEDIUMBLOB NULL"),
    ("Wettkampf_Tag", "Logo_MimeType", "VARCHAR(60) NULL"),
    # 06_concurrency.sql
    ("Einzel_Ergebnis", "Updated_At",
     "TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    # 07_v04.sql
    ("Geraete_has_Wettkampf", "Anzeige_Label",
     "VARCHAR(120) NULL COMMENT 'Optionale Beschriftung nur fuer diesen "
     "Wettkampf; NULL = Geraete.Name' AFTER `Geraete_id`"),
    ("Wettkampf_Tag", "Meldeschluss",
     "DATETIME NULL COMMENT 'Bis wann Trainer melden duerfen; "
     "NULL = solange Status Anmeldung' AFTER `Veranstalter`"),
    ("user", "Verein_id",
     "INT NULL COMMENT 'Pflicht fuer role=trainer' AFTER `Personen_id`"),
]

_SEED = [
    # Neue Berechnungs-Arten aus v0.4 (Unique-Key auf Regel_Kuerzel bzw. Name
    # vorhanden — INSERT IGNORE ist daher idempotent).
    "INSERT IGNORE INTO `Berechnungs_Art` (`Regel_Kuerzel`, `Bezeichnung`, `Beschreibung`) VALUES "
    "('RSG_STANDARD',   'RSG (D + A + E)',        'Rhythmische Sportgymnastik: D-Note + A-Note (optional) + E-Note (Trim bei >=3 Richtern) - Abzug.'),"
    "('ROPE_SPEED',     'Rope Skipping Speed',     'Zaehlwert (kleinster Wert bei mehreren Zaehlern) * Faktor + Offset.'),"
    "('ROPE_FREESTYLE', 'Rope Skipping Freestyle', 'Schwierigkeit + Praesentation (Trim bei >=3 Richtern) - Abzug.')",
    "INSERT IGNORE INTO `Geraete` (`Name`, `Einheit`, `Beschreibung`) VALUES "
    "('RSG Reifen', 'Pkt', 'RSG Handgeraet Reifen'),"
    "('RSG Ball',   'Pkt', 'RSG Handgeraet Ball'),"
    "('RSG Keulen', 'Pkt', 'RSG Handgeraet Keulen'),"
    "('RSG Band',   'Pkt', 'RSG Handgeraet Band'),"
    "('RSG Seil',   'Pkt', 'RSG Handgeraet Seil'),"
    "('Speed 30s',  'Spruenge', 'Rope Skipping Speed 30 Sekunden'),"
    "('Speed 180s', 'Spruenge', 'Rope Skipping Speed 3 Minuten'),"
    "('Freestyle',  'Pkt', 'Rope Skipping Freestyle/Kuer')",
]


def run_startup_migrations() -> None:
    """Bringt aeltere DB-Volumes auf den Stand der aktuellen Models.
    Wirft bei DB-Nichterreichbarkeit — der Aufrufer (lifespan) retried."""
    with engine.begin() as conn:
        if not _table_exists(conn, "user"):
            # Frisches Volume: die Init-Skripte des DB-Containers sind noch
            # nicht durch. Nichts tun — naechster Retry.
            raise RuntimeError("Schema noch nicht initialisiert (Tabelle 'user' fehlt)")

        applied = []
        for table, column, ddl in _COLUMNS:
            if _table_exists(conn, table) and _add_column(conn, table, column, ddl):
                applied.append(f"{table}.{column}")

        # role-ENUM um 'trainer' erweitern (MODIFY ist wiederholbar)
        role_type = conn.execute(text(
            "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = 'user' AND COLUMN_NAME = 'role'"
        )).scalar() or ""
        if "'trainer'" not in role_type:
            conn.execute(text(
                "ALTER TABLE `user` MODIFY `role` "
                "ENUM('admin','tisch','kampfrichter','trainer','viewer') "
                "NOT NULL DEFAULT 'viewer'"
            ))
            applied.append("user.role +trainer")

        if (_column_exists(conn, "user", "Verein_id")
                and not _constraint_exists(conn, "user", "fk_user_V")):
            conn.execute(text(
                "ALTER TABLE `user` ADD CONSTRAINT `fk_user_V` "
                "FOREIGN KEY (`Verein_id`) REFERENCES `Verein`(`idVerein`) "
                "ON DELETE SET NULL ON UPDATE CASCADE"
            ))
            applied.append("fk_user_V")

        for stmt in _SEED:
            conn.execute(text(stmt))

        if applied:
            print(f"[migrations] Schema aktualisiert: {', '.join(applied)}")
