-- Migration: Logo-Spalten fuer Verein und Wettkampftag.
-- Idempotent: prueft erst ob Spalte existiert (per INFORMATION_SCHEMA).
USE wettkampfDB;

DROP PROCEDURE IF EXISTS add_logo_column;
DELIMITER $$
CREATE PROCEDURE add_logo_column(IN tbl VARCHAR(64), IN col VARCHAR(64))
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = tbl
          AND COLUMN_NAME  = col
    ) THEN
        SET @s = CONCAT('ALTER TABLE `', tbl, '` ADD COLUMN `', col, '` MEDIUMBLOB NULL');
        PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
    END IF;
END$$
DELIMITER ;

CALL add_logo_column('Verein',        'Logo');
CALL add_logo_column('Verein',        'Logo_MimeType');
CALL add_logo_column('Wettkampf_Tag', 'Logo');
CALL add_logo_column('Wettkampf_Tag', 'Logo_MimeType');

DROP PROCEDURE IF EXISTS add_logo_column;

-- Logo_MimeType muss VARCHAR sein, nicht BLOB. Korrigieren falls die
-- Prozedur falsch lief.
ALTER TABLE `Verein`        MODIFY `Logo_MimeType` VARCHAR(60) NULL;
ALTER TABLE `Wettkampf_Tag` MODIFY `Logo_MimeType` VARCHAR(60) NULL;
