-- =====================================================
-- Migration v0.6 (idempotent) — zur manuellen Anwendung.
-- Fuer laufende Installationen macht app/migrations.py beim Start dasselbe
-- automatisch (fresh UND bestehende Volumes).
--
--   * Umlaut-Fix: Datenbank + alle Tabellen auf utf8mb4 umstellen.
--   * Riegen gelten wettkampfuebergreifend (am Wettkampftag):
--       - Neue Spalte Riege.Wettkampf_Tag_id
--       - Backfill aus dem zugeordneten Wettkampf
--       - gleichnamige Riegen desselben Tags zusammenfuehren
--       - Wettkampf_id nullbar, FK ON DELETE SET NULL
--
-- Manuell einspielen:
--   docker compose exec -T db mysql -uwettkampf -p wettkampfDB < db/09_v06.sql
-- =====================================================
USE wettkampfDB;

-- --- Umlaut-Fix: alles auf utf8mb4 -------------------------------------------
ALTER DATABASE `wettkampfDB` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Bei Bedarf pro Tabelle (Beispiel):
--   ALTER TABLE `Personen` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- (Die App konvertiert beim Start automatisch alle Tabellen, die noch nicht
--  utf8mb4 sind.)

-- --- Riegen wettkampfuebergreifend -------------------------------------------
ALTER TABLE `Riege` ADD COLUMN IF NOT EXISTS `Wettkampf_Tag_id` INT NULL AFTER `idRiege`;

UPDATE `Riege` r
  JOIN `Wettkampf` w ON w.idWettkampf = r.Wettkampf_id
  SET r.Wettkampf_Tag_id = w.Wettkampf_Tag_id
  WHERE r.Wettkampf_Tag_id IS NULL AND r.Wettkampf_id IS NOT NULL;

-- FK/Unique umhaengen (siehe migrations.py fuer die idempotente Variante).
-- ALTER TABLE `Riege` DROP FOREIGN KEY `fk_R_Wk`;
-- ALTER TABLE `Riege` DROP INDEX `UQ_Riege_Wk`;
-- ALTER TABLE `Riege` MODIFY `Wettkampf_id` INT NULL;
-- ALTER TABLE `Riege` ADD CONSTRAINT `fk_R_Wk`  FOREIGN KEY (`Wettkampf_id`)
--     REFERENCES `Wettkampf`(`idWettkampf`)   ON DELETE SET NULL ON UPDATE CASCADE;
-- ALTER TABLE `Riege` ADD CONSTRAINT `fk_R_Tag` FOREIGN KEY (`Wettkampf_Tag_id`)
--     REFERENCES `Wettkampf_Tag`(`idWettkampf_Tag`) ON DELETE CASCADE ON UPDATE CASCADE;
-- ALTER TABLE `Riege` ADD UNIQUE KEY `UQ_Riege_Tag` (`Bezeichnung`, `Wettkampf_Tag_id`);
