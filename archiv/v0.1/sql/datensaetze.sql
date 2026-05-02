-- -----------------------------------------------------
-- Datensätze für `Wettkampf_Tag`
-- -----------------------------------------------------
INSERT INTO `wettkampfDB`.`Wettkampf_Tag` (`Name`, `Erstell_Datum`, `Wettkampf_Datum`) VALUES
('Frühjahrsmeeting 2024', '2024-03-01', '2024-04-15'),
('Sommerturnfest 2024', '2024-05-10', '2024-07-20'),
('Herbstmeisterschaften 2024', '2024-08-01', '2024-10-05');

-- SELECT * FROM `wettkampfDB`.`Wettkampf_Tag`; -- Zur Überprüfung (IDs werden 1, 2, 3 sein)

-- -----------------------------------------------------
-- Datensätze für `Geraete`
-- -----------------------------------------------------
INSERT INTO `wettkampfDB`.`Geraete` (`Name`, `Anzahl_Var`, `Berechnung_Variante`, `Berechnung_Variante_Beschreibung`) VALUES
('Sprint 100m', 1, 1, 'Var1 = Zeit (Sekunden). Score = Zeit. Geringer ist besser (muss in Logik beachtet werden, hier Beispiel: Summe)'),
('Weitsprung', 3, 2, 'Var1, Var2, Var3 = Weiten der 3 Versuche (Meter). Score = Bester Versuch / 10 (Beispiel aus altem Trigger)'),
('Kugelstoßen', 1, 1, 'Var1 = Weite (Meter). Score = Weite.'),
('Hochsprung', 1, 3, 'Var1 = Höhe (Meter). Score = Höhe. (Beispiel für Berechnungsvariante 3 in sp_Calculate_Score: GREATEST)'),
('Speerwurf', 2, 1, 'Var1 = Weitester Wurf, Var2 = Zweitweitester Wurf. Score = Var1+Var2 (Beispiel).');

-- SELECT * FROM `wettkampfDB`.`Geraete`; -- Zur Überprüfung (IDs werden 1, 2, 3, 4, 5 sein)
-- Anpassen der sp_Calculate_Score für die Beispiele oben:


-- HINWEIS: Die obige sp_Calculate_Score ist immer noch sehr vereinfacht.
-- Eine bessere Lösung wäre, die Anzahl der relevanten Variablen in der Tabelle Geraete zu speichern
-- oder die Logik in der Applikation feingranularer zu steuern.
-- Für Sprint (weniger ist besser) müsste die Score-Logik umgekehrt werden oder der Score anders interpretiert werden.
-- Der Einfachheit halber nehmen wir an, höhere Scores sind immer besser in diesen Beispielen.

-- -----------------------------------------------------
-- Datensätze für `Personen`
-- -----------------------------------------------------
INSERT INTO `wettkampfDB`.`Personen` (`Vorname`, `Nachname`, `Geburtsdatum`, `Verein`, `Geschlecht`) VALUES
('Max', 'Mustermann', '1998-05-12', 'Turnverein Musterstadt', 'm'),
('Erika', 'Musterfrau', '2000-08-20', 'Sportfreunde Beispielhausen', 'w'),
('John', 'Doe', '1995-01-30', 'Athletik Club Anonym', 'm'),
('Jane', 'Smith', '2002-11-05', 'Turnverein Musterstadt', 'w'),
('Peter', 'Pan', '2005-07-15', 'Nimmerland Sport Club', 'm');

-- SELECT * FROM `wettkampfDB`.`Personen`; -- Zur Überprüfung (IDs werden 1, 2, 3, 4, 5 sein)

-- -----------------------------------------------------
-- Datensätze für `Wettkampf`
-- Annahme: idWettkampf_Tag: 1='Frühjahrsmeeting 2024', 2='Sommerturnfest 2024'
-- -----------------------------------------------------
INSERT INTO `wettkampfDB`.`Wettkampf` (`Wettkampf_Nr`, `Name`, `Altersklasse`, `Wettkampf_Tag_idWettkampf_Tag`) VALUES
(101, 'Mehrkampf U18 Männlich', 'U18M', 1),
(102, 'Mehrkampf U18 Weiblich', 'U18W', 1),
(201, 'Einzeldisziplinen Offen', 'Offen', 2),
(202, 'Team Challenge', 'Team', 2);

-- SELECT * FROM `wettkampfDB`.`Wettkampf`; -- Zur Überprüfung (IDs werden 1, 2, 3, 4 sein)

-- -----------------------------------------------------
-- Datensätze für `Geraete_has_Wettkampf`
-- Annahme: idGeraete: 1='Sprint 100m', 2='Weitsprung', 3='Kugelstoßen'
-- Annahme: idWettkampf: 1='Mehrkampf U18M (Frühjahr)', 2='Mehrkampf U18W (Frühjahr)', 3='Einzeldisziplinen Offen (Sommer)'
-- -----------------------------------------------------
-- Geräte für Mehrkampf U18M (Wettkampf ID 1)
INSERT INTO `wettkampfDB`.`Geraete_has_Wettkampf` (`Geraete_idGeraete`, `Wettkampf_idWettkampf`, `Anzahl_Durchfuehrungen`) VALUES
(1, 1, 1), -- Sprint 100m für Mehrkampf U18M
(2, 1, 3), -- Weitsprung (3 Versuche) für Mehrkampf U18M
(3, 1, 3); -- Kugelstoßen (3 Versuche) für Mehrkampf U18M

-- Geräte für Mehrkampf U18W (Wettkampf ID 2)
INSERT INTO `wettkampfDB`.`Geraete_has_Wettkampf` (`Geraete_idGeraete`, `Wettkampf_idWettkampf`, `Anzahl_Durchfuehrungen`) VALUES
(1, 2, 1), -- Sprint 100m für Mehrkampf U18W
(2, 2, 3); -- Weitsprung (3 Versuche) für Mehrkampf U18W

-- Geräte für Einzeldisziplinen Offen (Wettkampf ID 3)
INSERT INTO `wettkampfDB`.`Geraete_has_Wettkampf` (`Geraete_idGeraete`, `Wettkampf_idWettkampf`, `Anzahl_Durchfuehrungen`) VALUES
(1, 3, 1), -- Sprint 100m
(2, 3, 3), -- Weitsprung
(3, 3, 3), -- Kugelstoßen
(4, 3, 1), -- Hochsprung
(5, 3, 2); -- Speerwurf

-- SELECT * FROM `wettkampfDB`.`Geraete_has_Wettkampf`; -- Zur Überprüfung (IDs z.B. 1 bis 10)

-- -----------------------------------------------------
-- Datensätze für `Personen_has_Wettkampf` (Anmeldungen)
-- Annahme: idPersonen: 1='Max', 2='Erika', 3='John', 4='Jane'
-- Annahme: idWettkampf: 1='Mehrkampf U18M', 2='Mehrkampf U18W', 3='Einzeldisziplinen Offen'
-- -----------------------------------------------------
-- Max (1) meldet sich für Mehrkampf U18M (1) an
INSERT INTO `wettkampfDB`.`Personen_has_Wettkampf` (`Personen_idPersonen`, `Wettkampf_idWettkampf`) VALUES
(1, 1);

-- Erika (2) meldet sich für Mehrkampf U18W (2) an
INSERT INTO `wettkampfDB`.`Personen_has_Wettkampf` (`Personen_idPersonen`, `Wettkampf_idWettkampf`) VALUES
(2, 2);

-- John (3) meldet sich für Einzeldisziplinen Offen (3) an
INSERT INTO `wettkampfDB`.`Personen_has_Wettkampf` (`Personen_idPersonen`, `Wettkampf_idWettkampf`) VALUES
(3, 3);

-- Jane (4) meldet sich für Mehrkampf U18W (2) und Einzeldisziplinen Offen (3) an
INSERT INTO `wettkampfDB`.`Personen_has_Wettkampf` (`Personen_idPersonen`, `Wettkampf_idWettkampf`) VALUES
(4, 2),
(4, 3);

-- Peter (5) meldet sich für Mehrkampf U18M (1) an
INSERT INTO `wettkampfDB`.`Personen_has_Wettkampf` (`Personen_idPersonen`, `Wettkampf_idWettkampf`) VALUES
(5, 1);


-- SELECT * FROM `wettkampfDB`.`Personen_has_Wettkampf`; -- Zur Überprüfung

-- -----------------------------------------------------
-- Datensätze für `Einzel_Ergebnis`
-- Annahme: idPersonen: 1='Max', 2='Erika', 3='John', 4='Jane', 5='Peter'
-- Annahme: idGeraete_Wettkampf (Beispiel IDs, bitte mit den tatsächlichen IDs aus Ihrer DB abgleichen!):
--  Für Wettkampf 1 (U18M):
--    Sprint (Gerät 1, Wettkampf 1) -> idGeraete_Wettkampf = 1 (angenommen)
--    Weitsprung (Gerät 2, Wettkampf 1) -> idGeraete_Wettkampf = 2 (angenommen)
--    Kugelstoßen (Gerät 3, Wettkampf 1) -> idGeraete_Wettkampf = 3 (angenommen)
--  Für Wettkampf 2 (U18W):
--    Sprint (Gerät 1, Wettkampf 2) -> idGeraete_Wettkampf = 4 (angenommen)
--    Weitsprung (Gerät 2, Wettkampf 2) -> idGeraete_Wettkampf = 5 (angenommen)
--  Für Wettkampf 3 (Offen):
--    Sprint (Gerät 1, Wettkampf 3) -> idGeraete_Wettkampf = 6 (angenommen)
--    Kugelstoßen (Gerät 3, Wettkampf 3) -> idGeraete_Wettkampf = 8 (angenommen)
--    Speerwurf (Gerät 5, Wettkampf 3) -> idGeraete_Wettkampf = 10 (angenommen)
--
-- WICHTIG: Die IDs für `Geraete_Wettkampf_idGeraete_Wettkampf` müssen Sie nach dem Einfügen
-- der Daten in `Geraete_has_Wettkampf` überprüfen und hier korrekt einsetzen!
-- Beispiel-Abfrage zur Ermittlung der IDs:
-- SELECT gw.idGeraete_Wettkampf, g.Name AS GeraetName, w.Name AS WettkampfName
-- FROM Geraete_has_Wettkampf gw
-- JOIN Geraete g ON gw.Geraete_idGeraete = g.idGeraete
-- JOIN Wettkampf w ON gw.Wettkampf_idWettkampf = w.idWettkampf;
--
-- Angenommene IDs für die Beispiele:
-- Max (Person 1) im Wettkampf 1 (U18M):
--   Sprint (idGeraete_Wettkampf=1):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(1, 1, 1, 12.50); -- Zeit für Sprint
--   Weitsprung (idGeraete_Wettkampf=2):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`, `Var2`, `Var3`) VALUES
(2, 1, 1, 5.20, 5.35, 5.10); -- Weiten für Weitsprung (Trigger nimmt besten)
--   Kugelstoßen (idGeraete_Wettkampf=3):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(3, 1, 1, 10.50); -- Weite Kugelstoßen

-- Peter (Person 5) im Wettkampf 1 (U18M):
--   Sprint (idGeraete_Wettkampf=1):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(1, 5, 1, 11.90);
--   Weitsprung (idGeraete_Wettkampf=2):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`, `Var2`, `Var3`) VALUES
(2, 5, 1, 5.80, 0.00, 5.75); -- Ein ungültiger Versuch

-- Erika (Person 2) im Wettkampf 2 (U18W):
--   Sprint (idGeraete_Wettkampf=4):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(4, 2, 1, 13.10);
--   Weitsprung (idGeraete_Wettkampf=5):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`, `Var2`, `Var3`) VALUES
(5, 2, 1, 4.80, 4.95, 4.88);

-- John (Person 3) im Wettkampf 3 (Offen):
--   Kugelstoßen (idGeraete_Wettkampf=8):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(8, 3, 1, 14.20);

-- Jane (Person 4) im Wettkampf 2 (U18W):
--   Sprint (idGeraete_Wettkampf=4):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`) VALUES
(4, 4, 1, 12.80);

-- Jane (Person 4) im Wettkampf 3 (Offen):
--   Speerwurf (idGeraete_Wettkampf=10):
INSERT INTO `wettkampfDB`.`Einzel_Ergebnis` (`Geraete_Wettkampf_idGeraete_Wettkampf`, `Personen_idPersonen`, `Versuch_Nr`, `Var1`, `Var2`) VALUES
(10, 4, 1, 35.50, 33.20); -- Weiten für Speerwurf

-- SELECT * FROM `wettkampfDB`.`Einzel_Ergebnis`;
-- SELECT * FROM `wettkampfDB`.`Gesamt_Ergebnisse`; -- Diese Tabelle sollte durch die Trigger automatisch befüllt worden sein.