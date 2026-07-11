-- =====================================================
-- Migration v0.4 (idempotent):
--   * Geraete_has_Wettkampf.Anzeige_Label  (Feld-Beschriftung pro Wettkampf)
--   * user.role um 'trainer' erweitert + user.Verein_id
--   * Wettkampf_Tag.Meldeschluss
--   * Neue Berechnungs-Arten (RSG, Rope Skipping)
--
-- Docker fuehrt die Scripts in /docker-entrypoint-initdb.d NUR beim
-- allerersten Start (leeres Volume) aus. Fuer eine BESTEHENDE DB dieses
-- Script manuell einspielen:
--   docker compose exec -T db mysql -uwettkampf -p wettkampfDB < db/07_v04.sql
-- =====================================================
USE wettkampfDB;

DROP PROCEDURE IF EXISTS v04_add_column;
DELIMITER $$
CREATE PROCEDURE v04_add_column(IN tbl VARCHAR(64), IN col VARCHAR(64), IN ddl_rest TEXT)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = tbl
          AND COLUMN_NAME  = col
    ) THEN
        SET @s = CONCAT('ALTER TABLE `', tbl, '` ADD COLUMN `', col, '` ', ddl_rest);
        PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
    END IF;
END$$
DELIMITER ;

CALL v04_add_column('Geraete_has_Wettkampf', 'Anzeige_Label',
    'VARCHAR(120) NULL COMMENT ''Optionale Beschriftung nur fuer diesen Wettkampf; NULL = Geraete.Name'' AFTER `Geraete_id`');
CALL v04_add_column('Wettkampf_Tag', 'Meldeschluss',
    'DATETIME NULL COMMENT ''Bis wann Trainer melden duerfen; NULL = solange Status Anmeldung'' AFTER `Veranstalter`');
CALL v04_add_column('user', 'Verein_id',
    'INT NULL COMMENT ''Pflicht fuer role=trainer'' AFTER `Personen_id`');

DROP PROCEDURE IF EXISTS v04_add_column;

-- role-ENUM erweitern (MODIFY ist wiederholbar / idempotent)
ALTER TABLE `user`
    MODIFY `role` ENUM('admin','tisch','kampfrichter','trainer','viewer') NOT NULL DEFAULT 'viewer';

-- FK user -> Verein nur anlegen wenn er fehlt
DROP PROCEDURE IF EXISTS v04_add_fk_user_verein;
DELIMITER $$
CREATE PROCEDURE v04_add_fk_user_verein()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME        = 'user'
          AND CONSTRAINT_NAME   = 'fk_user_V'
    ) THEN
        ALTER TABLE `user`
            ADD CONSTRAINT `fk_user_V` FOREIGN KEY (`Verein_id`)
            REFERENCES `Verein`(`idVerein`)
            ON DELETE SET NULL ON UPDATE CASCADE;
    END IF;
END$$
DELIMITER ;
CALL v04_add_fk_user_verein();
DROP PROCEDURE IF EXISTS v04_add_fk_user_verein;

-- Neue Berechnungs-Arten (INSERT IGNORE: existierende bleiben unangetastet)
INSERT IGNORE INTO `Berechnungs_Art` (`Regel_Kuerzel`, `Bezeichnung`, `Beschreibung`) VALUES
('RSG_STANDARD',   'RSG (D + A + E)',              'Rhythmische Sportgymnastik: D-Note + A-Note (optional) + E-Note (Trim bei >=3 Richtern) - Abzug.'),
('ROPE_SPEED',     'Rope Skipping Speed',           'Zaehlwert (kleinster Wert bei mehreren Zaehlern) * Faktor + Offset.'),
('ROPE_FREESTYLE', 'Rope Skipping Freestyle',       'Schwierigkeit + Praesentation (Trim bei >=3 Richtern) - Abzug.');

-- Beispiel-Geraete fuer die neuen Sportarten (optional, nur wenn nicht vorhanden)
INSERT IGNORE INTO `Geraete` (`Name`, `Einheit`, `Beschreibung`) VALUES
('RSG Reifen',      'Pkt',  'RSG Handgeraet Reifen'),
('RSG Ball',        'Pkt',  'RSG Handgeraet Ball'),
('RSG Keulen',      'Pkt',  'RSG Handgeraet Keulen'),
('RSG Band',        'Pkt',  'RSG Handgeraet Band'),
('RSG Seil',        'Pkt',  'RSG Handgeraet Seil'),
('Speed 30s',       'Spruenge', 'Rope Skipping Speed 30 Sekunden'),
('Speed 180s',      'Spruenge', 'Rope Skipping Speed 3 Minuten'),
('Freestyle',       'Pkt',  'Rope Skipping Freestyle/Kuer');
