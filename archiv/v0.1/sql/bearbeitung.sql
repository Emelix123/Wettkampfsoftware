-- a) Verein von 'Max Mustermann' (Person ID 1) ändern
UPDATE `wettkampfDB`.`Personen`
SET `Verein` = 'Neuer Sportclub XY'
WHERE `idPersonen` = 1;
-- SELECT * FROM `wettkampfDB`.`Personen` WHERE `idPersonen` = 1;

-- b) Wettkampfdatum des 'Frühjahrsmeeting 2024' (Tag ID 1) ändern
UPDATE `wettkampfDB`.`Wettkampf_Tag`
SET `Wettkampf_Datum` = '2024-04-20'
WHERE `idWettkampf_Tag` = 1;
-- SELECT * FROM `wettkampfDB`.`Wettkampf_Tag` WHERE `idWettkampf_Tag` = 1;

-- c) Anzahl der Durchführungen für Weitsprung im 'Mehrkampf U18M' ändern
-- Annahme: idGeraete_Wettkampf für Weitsprung im Wettkampf 1 ist 2 (bitte prüfen!)
UPDATE `wettkampfDB`.`Geraete_has_Wettkampf`
SET `Anzahl_Durchfuehrungen` = 4
WHERE `idGeraete_Wettkampf` = 2;
-- SELECT * FROM `wettkampfDB`.`Geraete_has_Wettkampf` WHERE `idGeraete_Wettkampf` = 2;

-- d) Ein Einzelergebnis von Max Mustermann (Person ID 1) korrigieren
-- Annahme: idEinzel_Ergebnis für Max' Sprint (idGeraete_Wettkampf=1) ist X (bitte ID des Eintrags prüfen!)
-- Suchen Sie zuerst die ID des Einzelergebnisses:
-- SELECT idEinzel_Ergebnis FROM Einzel_Ergebnis WHERE Personen_idPersonen = 1 AND Geraete_Wettkampf_idGeraete_Wettkampf = 1;
-- Angenommen, die gefundene idEinzel_Ergebnis ist 1
UPDATE `wettkampfDB`.`Einzel_Ergebnis`
SET `Var1` = 12.35 -- Schnellere Zeit
WHERE `idEinzel_Ergebnis` = 1;
-- Nach diesem Update werden die Trigger automatisch:
-- 1. Den `Score` in `Einzel_Ergebnis` für diesen Eintrag neu berechnen.
-- 2. Den `GesamtScore` für Max Mustermann im entsprechenden Wettkampf in `Gesamt_Ergebnisse` aktualisieren.
-- SELECT * FROM `wettkampfDB`.`Einzel_Ergebnis` WHERE `idEinzel_Ergebnis` = 1;
-- SELECT ge.* FROM `wettkampfDB`.`Gesamt_Ergebnisse` ge JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen WHERE p.idPersonen = 1;

-- a) Eine Person (z.B. 'Peter Pan', Person ID 5) abmelden von einem Wettkampf
-- Annahme: Peter (5) ist für Wettkampf 1 (Mehrkampf U18M) angemeldet.
DELETE FROM `wettkampfDB`.`Personen_has_Wettkampf`
WHERE `Personen_idPersonen` = 5 AND `Wettkampf_idWettkampf` = 1;
-- Dadurch werden auch seine Einzelergebnisse und Gesamtergebnisse für DIESEN Wettkampf
-- gelöscht, wenn die ON DELETE CASCADE-Regeln von Einzel_Ergebnis auf Personen_has_Wettkampf
-- oder von Gesamt_Ergebnisse auf Personen_has_Wettkampf zeigen würden.
-- In unserem aktuellen Schema werden Ergebnisse durch Löschen der Anmeldung NICHT direkt gelöscht.
-- Ergebnisse werden gelöscht, wenn die Person selbst gelöscht wird oder der Wettkampf/Geräteeinsatz.

-- b) Ein bestimmtes Einzelergebnis löschen
-- Annahme: Das Kugelstoß-Ergebnis von John Doe (Person 3) im Wettkampf 3 (idGeraete_Wettkampf=8) soll gelöscht werden.
-- SELECT idEinzel_Ergebnis FROM Einzel_Ergebnis WHERE Personen_idPersonen = 3 AND Geraete_Wettkampf_idGeraete_Wettkampf = 8;
-- Angenommen, die ID ist 8.
DELETE FROM `wettkampfDB`.`Einzel_Ergebnis`
WHERE `idEinzel_Ergebnis` = 8;
-- Die Trigger aktualisieren danach das Gesamtergebnis von John Doe.

-- c) Eine Person komplett löschen (z.B. 'Peter Pan', Person ID 5)
-- ACHTUNG: Dies löscht die Person und DANK `ON DELETE CASCADE` auch:
-- - Alle ihre Anmeldungen in `Personen_has_Wettkampf`.
-- - Alle ihre Ergebnisse in `Einzel_Ergebnis`.
-- - Alle ihre Einträge in `Gesamt_Ergebnisse`.
DELETE FROM `wettkampfDB`.`Personen`
WHERE `idPersonen` = 5;
-- SELECT * FROM `wettkampfDB`.`Personen` WHERE `idPersonen` = 5;
-- SELECT * FROM `wettkampfDB`.`Personen_has_Wettkampf` WHERE `Personen_idPersonen` = 5;
-- SELECT * FROM `wettkampfDB`.`Einzel_Ergebnis` WHERE `Personen_idPersonen` = 5;
-- SELECT * FROM `wettkampfDB`.`Gesamt_Ergebnisse` WHERE `Personen_idPersonen` = 5;

-- d) Versuch, einen Wettkampftag zu löschen, der noch Wettkämpfe hat (sollte fehlschlagen wegen ON DELETE RESTRICT)
-- Annahme: Wettkampf_Tag ID 1 ('Frühjahrsmeeting 2024') hat noch Wettkämpfe.
-- Dieser Befehl wird einen Fehler wegen der Foreign Key Constraint produzieren.
-- DELETE FROM `wettkampfDB`.`Wettkampf_Tag`
-- WHERE `idWettkampf_Tag` = 1;

-- Um ihn zu löschen, müssten zuerst alle abhängigen Wettkämpfe gelöscht (oder einem anderen Tag zugeordnet) werden.
-- Beispiel: Erst abhängige Wettkämpfe löschen (was wiederum deren Anmeldungen, Geräteeinsätze etc. kaskadierend löscht)
-- DELETE FROM `wettkampfDB`.`Wettkampf` WHERE `Wettkampf_Tag_idWettkampf_Tag` = 1;
-- DELETE FROM `wettkampfDB`.`Wettkampf_Tag` WHERE `idWettkampf_Tag` = 1; -- Jetzt erfolgreich