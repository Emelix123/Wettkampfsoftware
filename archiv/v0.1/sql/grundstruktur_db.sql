-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema wettkampfDB
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `wettkampfDB` DEFAULT CHARACTER SET utf8mb4 ;
USE `wettkampfDB` ;

-- -----------------------------------------------------
-- Table `wettkampfDB`.`Wettkampf_Tag`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Wettkampf_Tag` (
  `idWettkampf_Tag` INT NOT NULL AUTO_INCREMENT,
  `Name` VARCHAR(45) NOT NULL,
  `Erstell_Datum` DATE NOT NULL DEFAULT (CURDATE()),
  `Wettkampf_Datum` DATE NOT NULL,
  PRIMARY KEY (`idWettkampf_Tag`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Wettkampf`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Wettkampf` (
  `idWettkampf` INT NOT NULL AUTO_INCREMENT,
  `Wettkampf_Nr` INT NOT NULL,
  `Name` VARCHAR(45) NOT NULL,
  `Altersklasse` VARCHAR(45) NOT NULL,
  `Wettkampf_Tag_idWettkampf_Tag` INT NOT NULL,
  PRIMARY KEY (`idWettkampf`), -- idWettkampf allein als PK
  INDEX `fk_Wettkampf_Wettkampf_Tag_idx` (`Wettkampf_Tag_idWettkampf_Tag` ASC) VISIBLE,
  UNIQUE INDEX `UQ_WettkampfNr_Tag` (`Wettkampf_Nr` ASC, `Wettkampf_Tag_idWettkampf_Tag` ASC) VISIBLE, -- Wettkampf_Nr muss pro Tag eindeutig sein
  CONSTRAINT `fk_Wettkampf_Wettkampf_Tag`
    FOREIGN KEY (`Wettkampf_Tag_idWettkampf_Tag`)
    REFERENCES `wettkampfDB`.`Wettkampf_Tag` (`idWettkampf_Tag`)
    ON DELETE RESTRICT  -- Verhindert Löschen eines Tags, wenn noch Wettkämpfe dranhängen
    ON UPDATE CASCADE)  -- Falls sich eine Tag-ID ändern könnte (selten, aber möglich)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Geraete`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Geraete` (
  `idGeraete` INT NOT NULL AUTO_INCREMENT, -- Primärschlüssel
  `Name` VARCHAR(45) NOT NULL, -- Name des Geräts
  `Anzahl_Var` INT NOT NULL COMMENT 'Maximale Anzahl an Variablen (Var1–Var10), die für diesen Gerätetyp verwendet werden.',
  `Berechnung_Variante` INT NOT NULL DEFAULT 1 COMMENT 'Definiert die Berechnungslogik für den Score: 1 = Summe, 2 = Durchschnitt, etc.',
  `Berechnung_Variante_Beschreibung` VARCHAR(255) NULL COMMENT 'Beschreibung der verwendeten Berechnungslogik für den Score.',
  
  -- Neue Beschreibungsfelder für Var1 bis Var10:
  `Var1_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var1, z. B. "Zeit in Sekunden"',
  `Var2_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var2, z. B. "Weite in Metern"',
  `Var3_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var3',
  `Var4_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var4',
  `Var5_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var5',
  `Var6_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var6',
  `Var7_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var7',
  `Var8_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var8',
  `Var9_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var9',
  `Var10_Beschreibung` VARCHAR(100) NULL COMMENT 'Beschreibung für Var10',

  PRIMARY KEY (`idGeraete`),
  UNIQUE INDEX `Name_UNIQUE` (`Name` ASC) VISIBLE
)
ENGINE = InnoDB;



-- -----------------------------------------------------
-- Table `wettkampfDB`.`Geraete_has_Wettkampf`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Geraete_has_Wettkampf` (
  `idGeraete_Wettkampf` INT NOT NULL AUTO_INCREMENT, -- Neuer Surrogate Key als PK
  `Geraete_idGeraete` INT NOT NULL,
  `Wettkampf_idWettkampf` INT NOT NULL,
  `Anzahl_Durchfuehrungen` INT NOT NULL DEFAULT 1 COMMENT 'Wie oft dieses Gerät im Wettkampf durchlaufen wird oder wie viele Wertungen eingehen (z.B. 3 Versuche). Die Spalte "Anzahl" aus dem Original wurde so interpretiert.',
  `Reihenfolge` INT NULL COMMENT 'Reihenfolge des Geräts im Wettkampf, falls relevant (z.B. 1=erstes Gerät, 2=zweites Gerät etc.).',
  PRIMARY KEY (`idGeraete_Wettkampf`),
  INDEX `fk_Geraete_has_Wettkampf_Wettkampf1_idx` (`Wettkampf_idWettkampf` ASC) VISIBLE,
  INDEX `fk_Geraete_has_Wettkampf_Geraete1_idx` (`Geraete_idGeraete` ASC) VISIBLE,
  UNIQUE INDEX `UQ_Geraet_Wettkampf` (`Geraete_idGeraete` ASC, `Wettkampf_idWettkampf` ASC) VISIBLE, -- Stellt Eindeutigkeit der Gerätekombination pro Wettkampf sicher
  CONSTRAINT `fk_Geraete_has_Wettkampf_Geraete1`
    FOREIGN KEY (`Geraete_idGeraete`)
    REFERENCES `wettkampfDB`.`Geraete` (`idGeraete`)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Geraete_has_Wettkampf_Wettkampf1`
    FOREIGN KEY (`Wettkampf_idWettkampf`)
    REFERENCES `wettkampfDB`.`Wettkampf` (`idWettkampf`)
    ON DELETE RESTRICT 
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Personen`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Personen` (
  `idPersonen` INT NOT NULL AUTO_INCREMENT,
  `Vorname` VARCHAR(45) NOT NULL, -- Üblicherweise NOT NULL
  `Nachname` VARCHAR(45) NOT NULL, -- Üblicherweise NOT NULL
  `Geburtsdatum` DATE NULL,
  `Verein` VARCHAR(45) NULL,
  `Geschlecht` ENUM('m', 'w', 'd') NULL COMMENT 'männlich, weiblich, divers', -- Beispiel für eine sinnvolle Erweiterung
  PRIMARY KEY (`idPersonen`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Personen_has_Wettkampf` (Anmeldung zum Wettkampf)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Personen_has_Wettkampf` (
  `Personen_idPersonen` INT NOT NULL,
  `Wettkampf_idWettkampf` INT NOT NULL, 
  `Riege` INT COMMENT 'Riege des Teilnehmers im Wettkampf',
  PRIMARY KEY (`Personen_idPersonen`, `Wettkampf_idWettkampf`),
  INDEX `fk_Personen_has_Wettkampf_Wettkampf1_idx` (`Wettkampf_idWettkampf` ASC) VISIBLE,
  INDEX `fk_Personen_has_Wettkampf_Personen1_idx` (`Personen_idPersonen` ASC) VISIBLE,
  CONSTRAINT `fk_Personen_has_Wettkampf_Personen1`
    FOREIGN KEY (`Personen_idPersonen`)
    REFERENCES `wettkampfDB`.`Personen` (`idPersonen`)
    ON DELETE CASCADE -- Wenn Person gelöscht wird, werden auch ihre Wettkampfanmeldungen gelöscht
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Personen_has_Wettkampf_Wettkampf1`
    FOREIGN KEY (`Wettkampf_idWettkampf`)
    REFERENCES `wettkampfDB`.`Wettkampf` (`idWettkampf`)
    ON DELETE CASCADE -- Wenn Wettkampf gelöscht wird, werden auch die Anmeldungen dazu gelöscht
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Einzel_Ergebnis`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Einzel_Ergebnis` (
  `idEinzel_Ergebnis` INT NOT NULL AUTO_INCREMENT, -- Korrigierter Name, alleiniger PK
  `Geraete_Wettkampf_idGeraete_Wettkampf` INT NOT NULL COMMENT 'FK zu Geraete_has_Wettkampf, spezifiziert das Gerät und den Wettkampfkontext',
  `Personen_idPersonen` INT NOT NULL,
  `Versuch_Nr` INT NULL DEFAULT 1 COMMENT 'Nummer des Versuchs, falls mehrere Versuche pro Gerät/Person erlaubt sind. Relevant für den UNIQUE Constraint.',
  `Var1` DECIMAL(10,3) NULL DEFAULT 0, -- Präzision ggf. anpassen (z.B. 10,3 für Zeiten oder Punkte)
  `Var2` DECIMAL(10,3) NULL DEFAULT 0,
  `Var3` DECIMAL(10,3) NULL DEFAULT 0,
  `Var4` DECIMAL(10,3) NULL DEFAULT 0,
  `Var5` DECIMAL(10,3) NULL DEFAULT 0,
  `Var6` DECIMAL(10,3) NULL DEFAULT 0,
  `Var7` DECIMAL(10,3) NULL DEFAULT 0,
  `Var8` DECIMAL(10,3) NULL DEFAULT 0,
  `Var9` DECIMAL(10,3) NULL DEFAULT 0,
  `Var10` DECIMAL(10,3) NULL DEFAULT 0,
  `Score` DECIMAL(10,3) NULL DEFAULT 0 COMMENT 'Berechneter Score für dieses Einzelergebnis',
  `Erfasst_Am` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Zeitpunkt der Erfassung des Ergebnisses',
  PRIMARY KEY (`idEinzel_Ergebnis`),
  INDEX `fk_Einzel_Ergebnis_Personen1_idx` (`Personen_idPersonen` ASC) VISIBLE,
  INDEX `fk_Einzel_Ergebnis_Geraete_Wettkampf1_idx` (`Geraete_Wettkampf_idGeraete_Wettkampf` ASC) VISIBLE,
  UNIQUE INDEX `UQ_Person_Geraet_Wettkampf_Versuch` (`Personen_idPersonen`, `Geraete_Wettkampf_idGeraete_Wettkampf`, `Versuch_Nr` ASC) VISIBLE
    COMMENT 'Stellt sicher, dass eine Person pro Gerät im Wettkampf und pro Versuch nur ein Ergebnis hat.',
  CONSTRAINT `fk_Einzel_Ergebnis_Personen1`
    FOREIGN KEY (`Personen_idPersonen`)
    REFERENCES `wettkampfDB`.`Personen` (`idPersonen`)
    ON DELETE CASCADE -- Wenn Person gelöscht, auch ihre Einzelergebnisse löschen
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Einzel_Ergebnis_Geraete_Wettkampf1`
    FOREIGN KEY (`Geraete_Wettkampf_idGeraete_Wettkampf`)
    REFERENCES `wettkampfDB`.`Geraete_has_Wettkampf` (`idGeraete_Wettkampf`)
    ON DELETE CASCADE -- Wenn der spezifische Geräteeinsatz im Wettkampf gelöscht wird, werden auch die Ergebnisse gelöscht
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `wettkampfDB`.`Gesamt_Ergebnisse`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `wettkampfDB`.`Gesamt_Ergebnisse`; -- Vorhandene Tabelle sicher löschen

CREATE TABLE IF NOT EXISTS `wettkampfDB`.`Gesamt_Ergebnisse` ( -- Korrigierter Name
  `idGesamt_Ergebnisse` INT NOT NULL AUTO_INCREMENT,
  `GesamtScore` DECIMAL(10,3) NULL, -- Präzision an Einzel_Ergebnis.Score angepasst
  `Berechnet_Am` DATETIME NULL,
  `Personen_idPersonen` INT NOT NULL,
  `Wettkampf_idWettkampf` INT NOT NULL,
  PRIMARY KEY (`idGesamt_Ergebnisse`),
  UNIQUE INDEX `UQ_Person_Wettkampf` (`Personen_idPersonen` ASC, `Wettkampf_idWettkampf` ASC) VISIBLE, -- Stellt sicher, dass pro Person und Wettkampf nur ein Gesamtergebnis existiert
  INDEX `fk_Gesamt_Ergebnisse_Personen1_idx` (`Personen_idPersonen` ASC) VISIBLE,
  INDEX `fk_Gesamt_Ergebnisse_Wettkampf1_idx` (`Wettkampf_idWettkampf` ASC) VISIBLE,
  CONSTRAINT `fk_Gesamt_Ergebnisse_Personen1`
    FOREIGN KEY (`Personen_idPersonen`)
    REFERENCES `wettkampfDB`.`Personen` (`idPersonen`)
    ON DELETE CASCADE -- Wenn Person gelöscht, auch Gesamtergebnis löschen
    ON UPDATE CASCADE,
  CONSTRAINT `fk_Gesamt_Ergebnisse_Wettkampf1`
    FOREIGN KEY (`Wettkampf_idWettkampf`)
    REFERENCES `wettkampfDB`.`Wettkampf` (`idWettkampf`)
    ON DELETE CASCADE -- Wenn Wettkampf gelöscht, auch Gesamtergebnisse löschen
    ON UPDATE CASCADE
) ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `wettkampfDB`.`user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `wettkampfDB`.`user`; -- Vorhandene Tabelle sicher löschen
-- Tabelle für Benutzerkonten, falls benötigt
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(200) NOT NULL,
    role ENUM('admin', 'user', 'kampfrichter') NOT NULL DEFAULT 'user'
);
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

