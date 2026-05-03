-- =====================================================
-- wettkampfDB v0.3
-- Stack: MySQL 8 + FastAPI (Python) + Jinja + HTMX
--
-- Design-Prinzipien:
--   * Berechnungs-Logik liegt 100% im Python-Backend.
--     Die DB speichert nur das WAS (Werte), nicht das WIE.
--   * Cache-Tabellen vermieden: Ranglisten kommen aus VIEWs (siehe 02_views.sql).
--   * Multi-Sport möglich, weil jede Berechnungs_Art ein freier Kürzel-String ist
--     der im Backend auf eine Strategy-Klasse gemappt wird.
-- =====================================================

DROP DATABASE IF EXISTS wettkampfDB;
CREATE DATABASE wettkampfDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE wettkampfDB;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- Verein
-- -----------------------------------------------------
CREATE TABLE `Verein` (
    `idVerein`      INT          NOT NULL AUTO_INCREMENT,
    `Kuerzel`       VARCHAR(10)  NOT NULL,
    `Name`          VARCHAR(120) NOT NULL,
    `Ort`           VARCHAR(80)  NULL,
    `Logo`          MEDIUMBLOB   NULL,
    `Logo_MimeType` VARCHAR(60)  NULL,
    PRIMARY KEY (`idVerein`),
    UNIQUE KEY `UQ_Verein_Kuerzel` (`Kuerzel`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Altersklasse
-- -----------------------------------------------------
CREATE TABLE `Altersklasse` (
    `idAltersklasse` INT                       NOT NULL AUTO_INCREMENT,
    `Kuerzel`        VARCHAR(15)               NOT NULL,
    `Bezeichnung`    VARCHAR(60)               NOT NULL,
    `Alter_Von`      INT                       NULL,
    `Alter_Bis`      INT                       NULL,
    `Geschlecht`     ENUM('m','w','d','alle')  NOT NULL DEFAULT 'alle',
    PRIMARY KEY (`idAltersklasse`),
    UNIQUE KEY `UQ_Altersklasse_Kuerzel` (`Kuerzel`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Wettkampf_Tag (z.B. "Frühjahrsmeeting 2026")
-- -----------------------------------------------------
CREATE TABLE `Wettkampf_Tag` (
    `idWettkampf_Tag` INT          NOT NULL AUTO_INCREMENT,
    `Name`            VARCHAR(120) NOT NULL,
    `Wettkampf_Datum` DATE         NOT NULL,
    `Ort`             VARCHAR(120) NULL,
    `Veranstalter`    VARCHAR(120) NULL,
    `Erstellt_Am`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `Logo`            MEDIUMBLOB   NULL,
    `Logo_MimeType`   VARCHAR(60)  NULL,
    PRIMARY KEY (`idWettkampf_Tag`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Wettkampf
-- -----------------------------------------------------
CREATE TABLE `Wettkampf` (
    `idWettkampf`        INT         NOT NULL AUTO_INCREMENT,
    `Wettkampf_Tag_id`   INT         NOT NULL,
    `Wettkampf_Nr`       INT         NOT NULL,
    `Name`               VARCHAR(120) NOT NULL,
    `Altersklasse_id`    INT         NOT NULL,
    `Status`  ENUM('Entwurf','Anmeldung','Aktiv','Abgeschlossen','Archiviert')
                         NOT NULL DEFAULT 'Entwurf',
    `Typ`     ENUM('Einzel','Mannschaft','Kombination')
                         NOT NULL DEFAULT 'Einzel',
    `Mannschaft_Groesse` INT         NULL
              COMMENT 'NULL = unbegrenzt; sonst Anzahl gewerteter Mitglieder pro Team',
    PRIMARY KEY (`idWettkampf`),
    UNIQUE KEY `UQ_Wettkampf_Nr_Tag` (`Wettkampf_Nr`, `Wettkampf_Tag_id`),
    CONSTRAINT `fk_W_Tag` FOREIGN KEY (`Wettkampf_Tag_id`)
        REFERENCES `Wettkampf_Tag`(`idWettkampf_Tag`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_W_AK`  FOREIGN KEY (`Altersklasse_id`)
        REFERENCES `Altersklasse`(`idAltersklasse`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Riege (Startgruppen)
-- -----------------------------------------------------
CREATE TABLE `Riege` (
    `idRiege`        INT         NOT NULL AUTO_INCREMENT,
    `Wettkampf_id`   INT         NOT NULL,
    `Bezeichnung`    VARCHAR(60) NOT NULL,
    `Start_Zeit`     TIME        NULL,
    PRIMARY KEY (`idRiege`),
    UNIQUE KEY `UQ_Riege_Wk` (`Bezeichnung`, `Wettkampf_id`),
    CONSTRAINT `fk_R_Wk` FOREIGN KEY (`Wettkampf_id`)
        REFERENCES `Wettkampf`(`idWettkampf`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Mannschaft (Teams je Wettkampf)
-- -----------------------------------------------------
CREATE TABLE `Mannschaft` (
    `idMannschaft`   INT         NOT NULL AUTO_INCREMENT,
    `Wettkampf_id`   INT         NOT NULL,
    `Name`           VARCHAR(120) NOT NULL,
    `Verein_id`      INT         NULL,
    PRIMARY KEY (`idMannschaft`),
    UNIQUE KEY `UQ_Mannschaft_Wk` (`Name`, `Wettkampf_id`),
    CONSTRAINT `fk_M_Wk` FOREIGN KEY (`Wettkampf_id`)
        REFERENCES `Wettkampf`(`idWettkampf`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_M_V`  FOREIGN KEY (`Verein_id`)
        REFERENCES `Verein`(`idVerein`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Geraete (Stammdaten: Apparat / Disziplin)
-- -----------------------------------------------------
CREATE TABLE `Geraete` (
    `idGeraete`    INT          NOT NULL AUTO_INCREMENT,
    `Name`         VARCHAR(60)  NOT NULL,
    `Einheit`      VARCHAR(20)  NOT NULL DEFAULT 'Pkt',
    `Beschreibung` VARCHAR(255) NULL,
    PRIMARY KEY (`idGeraete`),
    UNIQUE KEY `UQ_Geraete_Name` (`Name`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Berechnungs_Art (Mapping zu Python-Strategy)
-- Beispiel-Kuerzel:
--   TURNEN_OLYMPIC_TRIM  - Standard Turnen, E-Noten Schnitt ohne Min/Max + D - Abzug
--   TURNEN_AVG           - Schnitt aller Wertungen, kein Trim
--   LA_DIRECT            - Wert * Faktor + Offset (Weite/Höhe)
--   LA_SPRINT            - Offset - (Wert * Faktor) (Zeit)
--   MANUELL              - Wert wird direkt als Score uebernommen
-- -----------------------------------------------------
CREATE TABLE `Berechnungs_Art` (
    `idBerechnungs_Art` INT          NOT NULL AUTO_INCREMENT,
    `Regel_Kuerzel`     VARCHAR(60)  NOT NULL,
    `Bezeichnung`       VARCHAR(120) NOT NULL,
    `Beschreibung`      VARCHAR(255) NULL,
    PRIMARY KEY (`idBerechnungs_Art`),
    UNIQUE KEY `UQ_Berechnung_Kuerzel` (`Regel_Kuerzel`)
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Geraete_has_Wettkampf
-- Welches Gerät wird in welchem Wettkampf wie ausgewertet
-- -----------------------------------------------------
CREATE TABLE `Geraete_has_Wettkampf` (
    `idGhW`                 INT           NOT NULL AUTO_INCREMENT,
    `Wettkampf_id`          INT           NOT NULL,
    `Geraete_id`            INT           NOT NULL,
    `Reihenfolge`           INT           NOT NULL DEFAULT 1,
    `Anzahl_Versuche`       INT           NOT NULL DEFAULT 1,
    `Berechnungs_Art_id`    INT           NOT NULL,
    `Score_Faktor`          DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    `Score_Offset`          DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    `Erwartete_Kampfrichter` INT          NOT NULL DEFAULT 1
              COMMENT 'Min. Anzahl Wertungen bevor Score fixiert wird',
    PRIMARY KEY (`idGhW`),
    UNIQUE KEY `UQ_GhW_Wk_G` (`Wettkampf_id`, `Geraete_id`),
    CONSTRAINT `fk_GhW_Wk` FOREIGN KEY (`Wettkampf_id`)
        REFERENCES `Wettkampf`(`idWettkampf`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_GhW_G`  FOREIGN KEY (`Geraete_id`)
        REFERENCES `Geraete`(`idGeraete`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_GhW_B`  FOREIGN KEY (`Berechnungs_Art_id`)
        REFERENCES `Berechnungs_Art`(`idBerechnungs_Art`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Personen (Teilnehmer)
-- -----------------------------------------------------
CREATE TABLE `Personen` (
    `idPersonen`   INT               NOT NULL AUTO_INCREMENT,
    `Vorname`      VARCHAR(60)       NOT NULL,
    `Nachname`     VARCHAR(60)       NOT NULL,
    `Geburtsdatum` DATE              NULL,
    `Verein_id`    INT               NULL,
    `Geschlecht`   ENUM('m','w','d') NULL,
    PRIMARY KEY (`idPersonen`),
    KEY `IX_Personen_Name` (`Nachname`, `Vorname`),
    CONSTRAINT `fk_P_V` FOREIGN KEY (`Verein_id`)
        REFERENCES `Verein`(`idVerein`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- user (Login)
-- Rollen:
--   admin           - alles
--   tisch           - kann an mehreren Geräten als Tisch-Kampfrichter eintragen
--                     (Eingabemaske trägt mehrere Richter-Werte gleichzeitig ein)
--   kampfrichter    - eigene Wertung pro Versuch
--   viewer          - nur Lesezugriff im internen Bereich
-- -----------------------------------------------------
CREATE TABLE `user` (
    `id`            INT          NOT NULL AUTO_INCREMENT,
    `username`      VARCHAR(80)  NOT NULL,
    `email`         VARCHAR(120) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role`          ENUM('admin','tisch','kampfrichter','viewer') NOT NULL DEFAULT 'viewer',
    `Personen_id`   INT          NULL,
    `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at`    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_login`    TIMESTAMP    NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `UQ_user_username` (`username`),
    UNIQUE KEY `UQ_user_email`    (`email`),
    CONSTRAINT `fk_user_P` FOREIGN KEY (`Personen_id`)
        REFERENCES `Personen`(`idPersonen`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Personen_has_Wettkampf (Startliste / Anmeldung)
-- -----------------------------------------------------
CREATE TABLE `Personen_has_Wettkampf` (
    `Personen_id`   INT NOT NULL,
    `Wettkampf_id`  INT NOT NULL,
    `Startnummer`   INT NULL,
    `Riege_id`      INT NULL,
    `Mannschaft_id` INT NULL,
    `Start_Status`  ENUM('Gemeldet','Gestartet','Zurueckgezogen','Disqualifiziert')
                    NOT NULL DEFAULT 'Gemeldet',
    `Status_Grund`  VARCHAR(255) NULL,
    `Angemeldet_Am` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`Personen_id`, `Wettkampf_id`),
    UNIQUE KEY `UQ_PhW_Startnr_Wk` (`Wettkampf_id`, `Startnummer`),
    CONSTRAINT `fk_PhW_P` FOREIGN KEY (`Personen_id`)
        REFERENCES `Personen`(`idPersonen`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_PhW_W` FOREIGN KEY (`Wettkampf_id`)
        REFERENCES `Wettkampf`(`idWettkampf`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_PhW_R` FOREIGN KEY (`Riege_id`)
        REFERENCES `Riege`(`idRiege`)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_PhW_M` FOREIGN KEY (`Mannschaft_id`)
        REFERENCES `Mannschaft`(`idMannschaft`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Einzel_Ergebnis (1 Zeile = 1 Versuch einer Person an einem Gerät)
-- "Score" wird vom Backend gesetzt sobald genug Kampfrichter gewertet haben
-- (oder sofort bei single-judge Geräten, wenn Anzahl >= Erwartete_Kampfrichter).
-- -----------------------------------------------------
CREATE TABLE `Einzel_Ergebnis` (
    `idEinzel_Ergebnis` INT           NOT NULL AUTO_INCREMENT,
    `Personen_id`       INT           NOT NULL,
    `Wettkampf_id`      INT           NOT NULL,
    `Geraete_id`        INT           NOT NULL,
    `Versuch_Nr`        INT           NOT NULL DEFAULT 1,
    `Score`             DECIMAL(10,3) NULL     COMMENT 'NULL solange noch nicht berechnet',
    `Ist_Gueltig`       TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '0 = Fehlversuch',
    `Status`            ENUM('Offen','In_Bewertung','Freigegeben') NOT NULL DEFAULT 'Offen',
    `Erfasst_Am`        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `Updated_At`        TIMESTAMP     NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        COMMENT 'Optimistic-Locking Token: jede Aenderung des Versuchs erhoeht die Zeit',
    `Erfasst_Von`       INT           NULL,
    PRIMARY KEY (`idEinzel_Ergebnis`),
    UNIQUE KEY `UQ_EE_PWGV` (`Personen_id`, `Wettkampf_id`, `Geraete_id`, `Versuch_Nr`),
    CONSTRAINT `fk_EE_Anmeldung` FOREIGN KEY (`Personen_id`, `Wettkampf_id`)
        REFERENCES `Personen_has_Wettkampf`(`Personen_id`, `Wettkampf_id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_EE_GhW` FOREIGN KEY (`Wettkampf_id`, `Geraete_id`)
        REFERENCES `Geraete_has_Wettkampf`(`Wettkampf_id`, `Geraete_id`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_EE_User` FOREIGN KEY (`Erfasst_Von`)
        REFERENCES `user`(`id`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Kampfrichter_Wertung
-- Eine Wertung eines Kampfrichters für einen Versuch.
-- Im Tisch-Modus trägt 1 Login (role=tisch) die Wertungen
-- mehrerer Richter ein -> "Richter_Slot" 1..N statt user_id-FK.
-- -----------------------------------------------------
CREATE TABLE `Kampfrichter_Wertung` (
    `idWertung`           INT       NOT NULL AUTO_INCREMENT,
    `Einzel_Ergebnis_id`  INT       NOT NULL,
    `Richter_user_id`     INT       NULL  COMMENT 'NULL = Tisch-Eingabe; sonst eigener Login',
    `Richter_Slot`        INT       NOT NULL DEFAULT 1
              COMMENT '1..N pro Versuch; bei eigenem Login = 1, im Tisch-Modus = Slot des Richters',
    `Erfasst_Von`         INT       NULL  COMMENT 'Welcher User hat eingetragen (Tisch-Eingabe oder Richter selbst)',
    `Erfasst_Am`          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`idWertung`),
    UNIQUE KEY `UQ_KW_Ergebnis_Slot` (`Einzel_Ergebnis_id`, `Richter_Slot`),
    CONSTRAINT `fk_KW_EE`   FOREIGN KEY (`Einzel_Ergebnis_id`)
        REFERENCES `Einzel_Ergebnis`(`idEinzel_Ergebnis`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_KW_User` FOREIGN KEY (`Richter_user_id`)
        REFERENCES `user`(`id`)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_KW_EV`   FOREIGN KEY (`Erfasst_Von`)
        REFERENCES `user`(`id`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Kampfrichter_Wertung_Detail (Key/Value je Wertung)
-- Turnen: Kriterium='D_Note' / 'E_Note' / 'Abzug'
-- LA:     Kriterium='Wert'   (oder 'Zeit', 'Weite' ...)
-- Format ist offen, weil das Backend (Berechnungs_Art) entscheidet
-- welche Kriterien Pflicht sind.
-- -----------------------------------------------------
CREATE TABLE `Kampfrichter_Wertung_Detail` (
    `idDetail`   INT           NOT NULL AUTO_INCREMENT,
    `Wertung_id` INT           NOT NULL,
    `Kriterium`  VARCHAR(50)   NOT NULL,
    `Wert`       DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (`idDetail`),
    UNIQUE KEY `UQ_KWD_Wertung_Kriterium` (`Wertung_id`, `Kriterium`),
    CONSTRAINT `fk_KWD_W` FOREIGN KEY (`Wertung_id`)
        REFERENCES `Kampfrichter_Wertung`(`idWertung`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Audit_Log (wer hat wann was gemacht)
-- -----------------------------------------------------
CREATE TABLE `Audit_Log` (
    `idAudit_Log`  BIGINT       NOT NULL AUTO_INCREMENT,
    `user_id`      INT          NULL,
    `username`     VARCHAR(80)  NULL COMMENT 'Snapshot des Namens fuer den Fall dass User geloescht wird',
    `aktion`       VARCHAR(80)  NOT NULL COMMENT 'z.B. ergebnis.save, anmeldung.update, wettkampf.delete',
    `ziel_typ`     VARCHAR(40)  NULL  COMMENT 'z.B. EinzelErgebnis, Wettkampf',
    `ziel_id`      VARCHAR(60)  NULL  COMMENT 'Primaerschluessel(-tupel) als Text',
    `details`      JSON         NULL,
    `zeitpunkt`    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`idAudit_Log`),
    KEY `IX_AL_zeit` (`zeitpunkt`),
    KEY `IX_AL_user` (`user_id`),
    KEY `IX_AL_ziel` (`ziel_typ`, `ziel_id`),
    CONSTRAINT `fk_AL_User` FOREIGN KEY (`user_id`)
        REFERENCES `user`(`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE = InnoDB;

SET FOREIGN_KEY_CHECKS = 1;
