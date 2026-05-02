-- Active: 1746771350228@@localhost@3307@wettkampfDB
-- -----------------------------------------------------
-- Stored Procedure für Score Berechnung (optional, aber empfohlen für Wartbarkeit)
-- Passen Sie die Logik hier an Ihre spezifischen Berechnungsvorschriften an!
-- -----------------------------------------------------
DELIMITER $$
CREATE PROCEDURE `sp_Calculate_Score`(
    IN p_Berechnung_Variante INT,
    IN p_Var1 DECIMAL(10,3), IN p_Var2 DECIMAL(10,3), IN p_Var3 DECIMAL(10,3),
    IN p_Var4 DECIMAL(10,3), IN p_Var5 DECIMAL(10,3), IN p_Var6 DECIMAL(10,3),
    IN p_Var7 DECIMAL(10,3), IN p_Var8 DECIMAL(10,3), IN p_Var9 DECIMAL(10,3),
    IN p_Var10 DECIMAL(10,3),
    OUT p_Score DECIMAL(10,3)
)
BEGIN
    -- Score abhängig von Variante berechnen
    -- Dies ist nur eine Beispielimplementierung basierend auf Ihrem Original-Trigger.
    IF p_Berechnung_Variante = 1 THEN
        SET p_Score = IFNULL(p_Var1,0) + IFNULL(p_Var2,0) + IFNULL(p_Var10,0);
    ELSEIF p_Berechnung_Variante = 2 THEN
        SET p_Score = (IFNULL(p_Var1,0) + IFNULL(p_Var10,0)) / 10; -- Ihre ursprüngliche Logik
    -- Fügen Sie hier weitere Berechnungsvarianten hinzu:
    -- ELSEIF p_Berechnung_Variante = 3 THEN
    -- SET p_Score = ... ;
    ELSE
        SET p_Score = 0; -- Standardwert oder Fehlerfall
    END IF;
END$$
DELIMITER ;

-- -----------------------------------------------------
-- Trigger `wettkampfDB`.`trg_Einzel_Ergebnis_before_insert`
-- Berechnet den Score für ein neues Einzelergebnis.
-- -----------------------------------------------------
DELIMITER $$
CREATE TRIGGER `trg_Einzel_Ergebnis_before_insert`
BEFORE INSERT ON `Einzel_Ergebnis`
FOR EACH ROW
BEGIN
  DECLARE v_berechnung_variante INT;

  -- Hole die Berechnung_Variante vom zugehörigen Gerät
  SELECT g.Berechnung_Variante
  INTO v_berechnung_variante
  FROM Geraete g
  JOIN Geraete_has_Wettkampf ghw ON g.idGeraete = ghw.Geraete_idGeraete
  WHERE ghw.idGeraete_Wettkampf = NEW.Geraete_Wettkampf_idGeraete_Wettkampf;

  -- Rufe Stored Procedure auf oder implementiere Logik direkt
  CALL sp_Calculate_Score(
      v_berechnung_variante,
      NEW.Var1, NEW.Var2, NEW.Var3, NEW.Var4, NEW.Var5,
      NEW.Var6, NEW.Var7, NEW.Var8, NEW.Var9, NEW.Var10,
      NEW.Score -- OUT-Parameter, der NEW.Score setzt
  );
  /* -- Alternative: Direkte Implementierung (wenn keine SP verwendet wird)
  IF v_berechnung_variante = 1 THEN
    SET NEW.Score = IFNULL(NEW.Var1,0) + IFNULL(NEW.Var2,0) + IFNULL(NEW.Var10,0);
  ELSEIF v_berechnung_variante = 2 THEN
    SET NEW.Score = (IFNULL(NEW.Var1,0) + IFNULL(NEW.Var10,0)) / 10;
  ELSE
    SET NEW.Score = 0;
  END IF;
  */
END$$
DELIMITER ;

-- -----------------------------------------------------
-- Trigger `wettkampfDB`.`trg_Einzel_Ergebnis_before_update`
-- Berechnet den Score neu, wenn relevante Daten eines Einzelergebnisses geändert werden.
-- -----------------------------------------------------
DELIMITER $$
CREATE TRIGGER `trg_Einzel_Ergebnis_before_update`
BEFORE UPDATE ON `Einzel_Ergebnis`
FOR EACH ROW
BEGIN
  DECLARE v_berechnung_variante INT;

  -- Berechne Score nur neu, wenn sich eine der Variablen oder die Gerätezuordnung geändert hat.
  IF NOT (NEW.Var1 <=> OLD.Var1 AND NEW.Var2 <=> OLD.Var2 AND NEW.Var3 <=> OLD.Var3 AND
          NEW.Var4 <=> OLD.Var4 AND NEW.Var5 <=> OLD.Var5 AND NEW.Var6 <=> OLD.Var6 AND
          NEW.Var7 <=> OLD.Var7 AND NEW.Var8 <=> OLD.Var8 AND NEW.Var9 <=> OLD.Var9 AND
          NEW.Var10 <=> OLD.Var10 AND
          NEW.Geraete_Wettkampf_idGeraete_Wettkampf <=> OLD.Geraete_Wettkampf_idGeraete_Wettkampf)
  THEN
    SELECT g.Berechnung_Variante
    INTO v_berechnung_variante
    FROM Geraete g
    JOIN Geraete_has_Wettkampf ghw ON g.idGeraete = ghw.Geraete_idGeraete
    WHERE ghw.idGeraete_Wettkampf = NEW.Geraete_Wettkampf_idGeraete_Wettkampf;

    CALL sp_Calculate_Score(
        v_berechnung_variante,
        NEW.Var1, NEW.Var2, NEW.Var3, NEW.Var4, NEW.Var5,
        NEW.Var6, NEW.Var7, NEW.Var8, NEW.Var9, NEW.Var10,
        NEW.Score -- OUT-Parameter
    );
  -- ELSE
    -- SET NEW.Score = OLD.Score; -- Keine relevanten Änderungen, Score bleibt gleich (optional, da Score nicht geändert wurde)
  END IF;
END$$
DELIMITER ;

-- -----------------------------------------------------
-- Trigger `wettkampfDB`.`trg_Einzel_Ergebnis_after_insert`
-- Aktualisiert/Erstellt das Gesamtergebnis nach dem Einfügen eines Einzelergebnisses.
-- -----------------------------------------------------
DELIMITER ; -- Wichtig: Delimiter zurücksetzen vor dem nächsten CREATE TRIGGER Block mit neuem Delimiter
DELIMITER $$
CREATE TRIGGER `trg_Einzel_Ergebnis_after_insert`
AFTER INSERT ON `Einzel_Ergebnis`
FOR EACH ROW
BEGIN
    DECLARE v_gesamt_score DECIMAL(10,3);
    DECLARE v_wettkampf_id INT;

    -- Finde die Wettkampf_id basierend auf dem neuen Einzel_Ergebnis
    SELECT ghw.Wettkampf_idWettkampf
    INTO v_wettkampf_id
    FROM Geraete_has_Wettkampf ghw
    WHERE ghw.idGeraete_Wettkampf = NEW.Geraete_Wettkampf_idGeraete_Wettkampf;

    -- Berechne den neuen Gesamtscore für die betroffene Person und den Wettkampf
    -- Es werden alle Einzelergebnisse dieser Person für diesen Wettkampf summiert
    SELECT SUM(ee.Score)
    INTO v_gesamt_score
    FROM Einzel_Ergebnis ee
    JOIN Geraete_has_Wettkampf ghw ON ee.Geraete_Wettkampf_idGeraete_Wettkampf = ghw.idGeraete_Wettkampf
    WHERE ee.Personen_idPersonen = NEW.Personen_idPersonen
      AND ghw.Wettkampf_idWettkampf = v_wettkampf_id;

    -- Füge den neuen Gesamtscore ein oder aktualisiere den bestehenden
    INSERT INTO Gesamt_Ergebnisse (
        Personen_idPersonen,
        Wettkampf_idWettkampf,
        GesamtScore,
        Berechnet_Am
    )
    VALUES (
        NEW.Personen_idPersonen,
        v_wettkampf_id,
        IFNULL(v_gesamt_score, 0), -- Falls SUM NULL ergibt (keine Scores), setze 0
        NOW()
    )
    ON DUPLICATE KEY UPDATE
        GesamtScore = IFNULL(v_gesamt_score, 0),
        Berechnet_Am = NOW();
END$$
DELIMITER ;

-- -----------------------------------------------------
-- Trigger `wettkampfDB`.`trg_Einzel_Ergebnis_after_update`
-- Aktualisiert die Gesamtergebnisse, wenn ein Einzelergebnis geändert wurde.
-- Berücksichtigt auch Änderungen der Person oder des Wettkampfs des Einzelergebnisses.
-- -----------------------------------------------------
DELIMITER $$
CREATE TRIGGER `trg_Einzel_Ergebnis_after_update`
AFTER UPDATE ON `Einzel_Ergebnis`
FOR EACH ROW
BEGIN
    DECLARE v_gesamt_score_new DECIMAL(10,3);
    DECLARE v_gesamt_score_old DECIMAL(10,3);
    DECLARE v_wettkampf_id_new INT;
    DECLARE v_wettkampf_id_old INT;

    -- Nur ausführen, wenn sich der Score, die Person oder die Gerätezuordnung (und damit potenziell der Wettkampf) geändert hat.
    IF NOT (NEW.Score <=> OLD.Score AND
            NEW.Personen_idPersonen <=> OLD.Personen_idPersonen AND
            NEW.Geraete_Wettkampf_idGeraete_Wettkampf <=> OLD.Geraete_Wettkampf_idGeraete_Wettkampf)
    THEN
        -- Ermittle Wettkampf-ID für den NEUEN Zustand des Einzelergebnisses
        SELECT ghw.Wettkampf_idWettkampf
        INTO v_wettkampf_id_new
        FROM Geraete_has_Wettkampf ghw
        WHERE ghw.idGeraete_Wettkampf = NEW.Geraete_Wettkampf_idGeraete_Wettkampf;

        -- Aktualisiere/Erstelle den Gesamtscore für die NEUE Kombination (Person, Wettkampf)
        SELECT SUM(ee.Score)
        INTO v_gesamt_score_new
        FROM Einzel_Ergebnis ee
        JOIN Geraete_has_Wettkampf ghw ON ee.Geraete_Wettkampf_idGeraete_Wettkampf = ghw.idGeraete_Wettkampf
        WHERE ee.Personen_idPersonen = NEW.Personen_idPersonen
          AND ghw.Wettkampf_idWettkampf = v_wettkampf_id_new;

        INSERT INTO Gesamt_Ergebnisse (
            Personen_idPersonen,
            Wettkampf_idWettkampf,
            GesamtScore,
            Berechnet_Am
        )
        VALUES (
            NEW.Personen_idPersonen,
            v_wettkampf_id_new,
            IFNULL(v_gesamt_score_new, 0),
            NOW()
        )
        ON DUPLICATE KEY UPDATE
            GesamtScore = IFNULL(v_gesamt_score_new, 0),
            Berechnet_Am = NOW();

        -- Wenn sich die Person oder die Gerätezuordnung (und damit potenziell der Wettkampf) geändert hat,
        -- muss auch der Gesamtscore für die ALTE Kombination (Person, Wettkampf) neu berechnet werden.
        IF OLD.Personen_idPersonen != NEW.Personen_idPersonen OR
           OLD.Geraete_Wettkampf_idGeraete_Wettkampf != NEW.Geraete_Wettkampf_idGeraete_Wettkampf
        THEN
            -- Ermittle Wettkampf-ID für den ALTEN Zustand des Einzelergebnisses
            SELECT ghw.Wettkampf_idWettkampf
            INTO v_wettkampf_id_old
            FROM Geraete_has_Wettkampf ghw
            WHERE ghw.idGeraete_Wettkampf = OLD.Geraete_Wettkampf_idGeraete_Wettkampf;

            SELECT SUM(ee.Score)
            INTO v_gesamt_score_old
            FROM Einzel_Ergebnis ee
            JOIN Geraete_has_Wettkampf ghw ON ee.Geraete_Wettkampf_idGeraete_Wettkampf = ghw.idGeraete_Wettkampf
            WHERE ee.Personen_idPersonen = OLD.Personen_idPersonen
              AND ghw.Wettkampf_idWettkampf = v_wettkampf_id_old;

            IF v_gesamt_score_old IS NOT NULL AND v_gesamt_score_old > 0 THEN -- Nur aktualisieren, wenn noch Scores vorhanden sind
                UPDATE Gesamt_Ergebnisse
                SET GesamtScore = v_gesamt_score_old,
                    Berechnet_Am = NOW()
                WHERE Personen_idPersonen = OLD.Personen_idPersonen
                  AND Wettkampf_idWettkampf = v_wettkampf_id_old;
            ELSE -- Wenn keine Einzelergebnisse mehr für die alte Kombination existieren oder Summe 0 ist
                DELETE FROM Gesamt_Ergebnisse
                WHERE Personen_idPersonen = OLD.Personen_idPersonen
                  AND Wettkampf_idWettkampf = v_wettkampf_id_old;
            END IF;
        END IF;
    END IF;
END$$
DELIMITER ;

-- -----------------------------------------------------
-- Trigger `wettkampfDB`.`trg_Einzel_Ergebnis_after_delete`
-- Aktualisiert das Gesamtergebnis nach dem Löschen eines Einzelergebnisses.
-- -----------------------------------------------------
DELIMITER $$
CREATE TRIGGER `trg_Einzel_Ergebnis_after_delete`
AFTER DELETE ON `Einzel_Ergebnis`
FOR EACH ROW
BEGIN
    DECLARE v_gesamt_score DECIMAL(10,3);
    DECLARE v_wettkampf_id INT;

    -- Finde die Wettkampf_id basierend auf dem gelöschten Einzel_Ergebnis
    SELECT ghw.Wettkampf_idWettkampf
    INTO v_wettkampf_id
    FROM Geraete_has_Wettkampf ghw
    WHERE ghw.idGeraete_Wettkampf = OLD.Geraete_Wettkampf_idGeraete_Wettkampf;

    -- Berechne den neuen Gesamtscore für die betroffene Kombination
    SELECT SUM(ee.Score)
    INTO v_gesamt_score
    FROM Einzel_Ergebnis ee
    JOIN Geraete_has_Wettkampf ghw ON ee.Geraete_Wettkampf_idGeraete_Wettkampf = ghw.idGeraete_Wettkampf
    WHERE ee.Personen_idPersonen = OLD.Personen_idPersonen
      AND ghw.Wettkampf_idWettkampf = v_wettkampf_id;

    IF v_gesamt_score IS NOT NULL AND v_gesamt_score > 0 THEN -- Nur aktualisieren, wenn noch Scores vorhanden sind
        UPDATE Gesamt_Ergebnisse
        SET GesamtScore = v_gesamt_score,
            Berechnet_Am = NOW()
        WHERE Personen_idPersonen = OLD.Personen_idPersonen
          AND Wettkampf_idWettkampf = v_wettkampf_id;
    ELSE
        -- Wenn keine Einzelergebnisse mehr für diese Kombination vorhanden sind oder Summe 0 ist,
        -- lösche den Eintrag aus Gesamt_Ergebnisse
        DELETE FROM Gesamt_Ergebnisse
        WHERE Personen_idPersonen = OLD.Personen_idPersonen
          AND Wettkampf_idWettkampf = v_wettkampf_id;
    END IF;
END$$
DELIMITER ;