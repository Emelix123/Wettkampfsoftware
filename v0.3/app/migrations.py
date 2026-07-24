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


def _index_exists(conn, table: str, name: str) -> bool:
    return bool(conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "  AND TABLE_NAME = :t AND INDEX_NAME = :n"
        ),
        {"t": table, "n": name},
    ).first())


def _fk_exists(conn, table: str, name: str) -> bool:
    return bool(conn.execute(
        text(
            "SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = :t "
            "  AND CONSTRAINT_NAME = :n AND CONSTRAINT_TYPE = 'FOREIGN KEY'"
        ),
        {"t": table, "n": name},
    ).first())


def _convert_charset_utf8mb4(conn) -> list[str]:
    """Stellt Datenbank + alle Tabellen auf utf8mb4 um. Behebt Umlaut-'?'
    bei aelteren Volumes, die noch latin1/utf8mb3 sind. Idempotent: schon
    korrekte Tabellen werden uebersprungen (kein teurer Rebuild bei jedem Start)."""
    applied: list[str] = []
    dbname = conn.execute(text("SELECT DATABASE()")).scalar()
    # DB-Default anheben (betrifft neu angelegte Tabellen/Spalten)
    conn.execute(text(
        f"ALTER DATABASE `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    ))
    rows = conn.execute(text(
        "SELECT TABLE_NAME, TABLE_COLLATION FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'"
    )).mappings().all()
    for r in rows:
        coll = r["TABLE_COLLATION"] or ""
        if not coll.startswith("utf8mb4"):
            conn.execute(text(
                f"ALTER TABLE `{r['TABLE_NAME']}` "
                f"CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
            applied.append(f"charset:{r['TABLE_NAME']}")
    return applied


def _migrate_riegen_to_tag(conn) -> list[str]:
    """v0.6: Riegen gelten wettkampfuebergreifend (am Wettkampftag).
    Fuegt Wettkampf_Tag_id hinzu, backfillt aus dem Wettkampf, fuehrt
    gleichnamige Riegen desselben Tags zusammen und haengt die FK/Unique um.
    Alles idempotent."""
    if not _table_exists(conn, "Riege"):
        return []
    applied: list[str] = []
    if not _column_exists(conn, "Riege", "Wettkampf_Tag_id"):
        conn.execute(text(
            "ALTER TABLE `Riege` ADD COLUMN `Wettkampf_Tag_id` INT NULL AFTER `idRiege`"
        ))
        applied.append("Riege.Wettkampf_Tag_id")
    # Backfill: Tag aus dem zugeordneten Wettkampf ziehen
    conn.execute(text(
        "UPDATE `Riege` r JOIN `Wettkampf` w ON w.idWettkampf = r.Wettkampf_id "
        "SET r.Wettkampf_Tag_id = w.Wettkampf_Tag_id "
        "WHERE r.Wettkampf_Tag_id IS NULL AND r.Wettkampf_id IS NOT NULL"
    ))
    # Alte FK/Unique auf Wettkampf entfernen, Wettkampf_id nullbar machen,
    # FK mit ON DELETE SET NULL neu setzen (Riege ueberlebt Wettkampf-Loeschung).
    # Nur einmal noetig — laeuft nur, solange die Spalte noch NOT NULL ist.
    nullable = conn.execute(text(
        "SELECT IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'Riege' "
        "  AND COLUMN_NAME = 'Wettkampf_id'"
    )).scalar()
    if nullable == "NO":
        if _fk_exists(conn, "Riege", "fk_R_Wk"):
            conn.execute(text("ALTER TABLE `Riege` DROP FOREIGN KEY `fk_R_Wk`"))
        if _index_exists(conn, "Riege", "UQ_Riege_Wk"):
            conn.execute(text("ALTER TABLE `Riege` DROP INDEX `UQ_Riege_Wk`"))
        conn.execute(text("ALTER TABLE `Riege` MODIFY `Wettkampf_id` INT NULL"))
        if not _fk_exists(conn, "Riege", "fk_R_Wk"):
            conn.execute(text(
                "ALTER TABLE `Riege` ADD CONSTRAINT `fk_R_Wk` "
                "FOREIGN KEY (`Wettkampf_id`) REFERENCES `Wettkampf`(`idWettkampf`) "
                "ON DELETE SET NULL ON UPDATE CASCADE"
            ))
        applied.append("Riege.Wettkampf_id->NULL")
    if not _fk_exists(conn, "Riege", "fk_R_Tag"):
        conn.execute(text(
            "ALTER TABLE `Riege` ADD CONSTRAINT `fk_R_Tag` "
            "FOREIGN KEY (`Wettkampf_Tag_id`) REFERENCES `Wettkampf_Tag`(`idWettkampf_Tag`) "
            "ON DELETE CASCADE ON UPDATE CASCADE"
        ))
    # Gleichnamige Riegen desselben Tags zusammenfuehren (Anmeldungen umbiegen)
    dupes = conn.execute(text(
        "SELECT Wettkampf_Tag_id, Bezeichnung, MIN(idRiege) AS keep_id "
        "FROM `Riege` WHERE Wettkampf_Tag_id IS NOT NULL "
        "GROUP BY Wettkampf_Tag_id, Bezeichnung HAVING COUNT(*) > 1"
    )).mappings().all()
    for d in dupes:
        others = conn.execute(text(
            "SELECT idRiege FROM `Riege` WHERE Wettkampf_Tag_id = :tag "
            "AND Bezeichnung = :bez AND idRiege <> :keep"
        ), {"tag": d["Wettkampf_Tag_id"], "bez": d["Bezeichnung"], "keep": d["keep_id"]}).scalars().all()
        for oid in others:
            conn.execute(text(
                "UPDATE `Personen_has_Wettkampf` SET Riege_id = :keep WHERE Riege_id = :oid"
            ), {"keep": d["keep_id"], "oid": oid})
            conn.execute(text("DELETE FROM `Riege` WHERE idRiege = :oid"), {"oid": oid})
        applied.append(f"Riege-Merge:{d['Bezeichnung']}")
    if not _index_exists(conn, "Riege", "UQ_Riege_Tag"):
        conn.execute(text(
            "ALTER TABLE `Riege` ADD UNIQUE KEY `UQ_Riege_Tag` "
            "(`Bezeichnung`, `Wettkampf_Tag_id`)"
        ))
        applied.append("Riege.UQ_Riege_Tag")
    return applied


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
    # Turnen mit 1 Kampfrichter (v0.5)
    "INSERT IGNORE INTO `Berechnungs_Art` (`Regel_Kuerzel`, `Bezeichnung`, `Beschreibung`) VALUES "
    "('TURNEN_DE_PENALTY',     'Turnen: D + E - Penalty (1 KR)',            'D-Note + E-Note - Penalty (optional). Fuer 1 Kampfrichter; bei mehreren wird gemittelt.'),"
    "('TURNEN_DE_PENALTY_B10', 'Turnen: D + (10 - E-Abzug) - Penalty (1 KR)', 'Kampfrichter traegt nur den E-Abzug ein, System rechnet E = 10 - Abzug. Score = D + E - Penalty.')",
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

        # v0.6: Riegen wettkampfuebergreifend (am Wettkampftag)
        applied += _migrate_riegen_to_tag(conn)

        for stmt in _SEED:
            conn.execute(text(stmt))

        # Umlaut-Fix ganz am Ende, damit auch neu angelegte Spalten utf8mb4 sind.
        applied += _convert_charset_utf8mb4(conn)

        if applied:
            print(f"[migrations] Schema aktualisiert: {', '.join(applied)}")
