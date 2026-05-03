-- Migration: Audit_Log nachtraeglich anlegen falls noch nicht vorhanden.
-- Wird beim DB-Init mit-ausgefuehrt; idempotent fuer Updates auf bestehende DB.
USE wettkampfDB;

CREATE TABLE IF NOT EXISTS `Audit_Log` (
    `idAudit_Log`  BIGINT       NOT NULL AUTO_INCREMENT,
    `user_id`      INT          NULL,
    `username`     VARCHAR(80)  NULL,
    `aktion`       VARCHAR(80)  NOT NULL,
    `ziel_typ`     VARCHAR(40)  NULL,
    `ziel_id`      VARCHAR(60)  NULL,
    `details`      JSON         NULL,
    `zeitpunkt`    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`idAudit_Log`),
    KEY `IX_AL_zeit` (`zeitpunkt`),
    KEY `IX_AL_user` (`user_id`),
    KEY `IX_AL_ziel` (`ziel_typ`, `ziel_id`),
    CONSTRAINT `fk_AL_User` FOREIGN KEY (`user_id`)
        REFERENCES `user`(`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;
