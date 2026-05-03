-- Migration: Updated_At-Spalte fuer Optimistic Locking auf Einzel_Ergebnis.
-- Idempotent (CALL mit INFORMATION_SCHEMA-Check), laeuft auch auf bestehenden DBs.
USE wettkampfDB;
ALTER TABLE Einzel_Ergebnis ADD COLUMN Updated_At TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

DROP PROCEDURE IF EXISTS add_updated_at;
DELIMITER $$
CREATE PROCEDURE add_updated_at(IN tbl VARCHAR(64), IN col VARCHAR(64))
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = tbl
          AND COLUMN_NAME  = col
    ) THEN
        SET @s = CONCAT(
            'ALTER TABLE `', tbl, '` ADD COLUMN `', col,
            '` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ',
            'ON UPDATE CURRENT_TIMESTAMP'
        );
        PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
    END IF;
END$$
DELIMITER ;

CALL add_updated_at('Einzel_Ergebnis', 'Updated_At');

DROP PROCEDURE IF EXISTS add_updated_at;
