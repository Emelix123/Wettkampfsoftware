USE wettkampfDB;

-- =====================================================
-- Demo-Daten (optional). Wird nur geladen wenn LOAD_DEMO=1.
-- Spielwiese fuer Tests: 1 Wettkampftag, 2 Wettkaempfe Turnen,
-- ein paar Athleten, eine Mannschaft, eine Riege.
-- =====================================================

INSERT INTO `Verein` (`Kuerzel`, `Name`, `Ort`) VALUES
('TVM', 'Turnverein Musterstadt', 'Musterstadt'),
('SFB', 'Sportfreunde Beispiel',  'Beispielort');

INSERT INTO `Wettkampf_Tag` (`Name`, `Wettkampf_Datum`, `Ort`, `Veranstalter`) VALUES
('Demo-Turnfest 2026', '2026-06-01', 'Musterstadt', 'TV Musterstadt');

SET @tag := LAST_INSERT_ID();

-- Wettkampf 1: Boden + Reck (Einzel)
INSERT INTO `Wettkampf` (`Wettkampf_Tag_id`, `Wettkampf_Nr`, `Name`, `Altersklasse_id`, `Status`, `Typ`)
SELECT @tag, 101, 'Mehrkampf Maennlich Offen', a.idAltersklasse, 'Aktiv', 'Einzel'
FROM Altersklasse a WHERE a.Kuerzel='Offen';
SET @wk1 := LAST_INSERT_ID();

-- Wettkampf 2: Boden + Schwebebalken (Mannschaft, beste 2 von max 3)
INSERT INTO `Wettkampf` (`Wettkampf_Tag_id`, `Wettkampf_Nr`, `Name`, `Altersklasse_id`, `Status`, `Typ`, `Mannschaft_Groesse`)
SELECT @tag, 102, 'Team Challenge', a.idAltersklasse, 'Anmeldung', 'Mannschaft', 2
FROM Altersklasse a WHERE a.Kuerzel='Offen';
SET @wk2 := LAST_INSERT_ID();

-- Geraete-Zuordnung Wk1 (Turnen olympisch trim, 3 Richter)
INSERT INTO `Geraete_has_Wettkampf` (`Wettkampf_id`, `Geraete_id`, `Reihenfolge`, `Anzahl_Versuche`, `Berechnungs_Art_id`, `Erwartete_Kampfrichter`)
SELECT @wk1, g.idGeraete, 1, 1, b.idBerechnungs_Art, 3
FROM Geraete g, Berechnungs_Art b
WHERE g.Name='Boden' AND b.Regel_Kuerzel='TURNEN_OLYMPIC_TRIM';

INSERT INTO `Geraete_has_Wettkampf` (`Wettkampf_id`, `Geraete_id`, `Reihenfolge`, `Anzahl_Versuche`, `Berechnungs_Art_id`, `Erwartete_Kampfrichter`)
SELECT @wk1, g.idGeraete, 2, 1, b.idBerechnungs_Art, 3
FROM Geraete g, Berechnungs_Art b
WHERE g.Name='Reck' AND b.Regel_Kuerzel='TURNEN_OLYMPIC_TRIM';

-- Geraete-Zuordnung Wk2 (Schnitt aller, 2 Richter)
INSERT INTO `Geraete_has_Wettkampf` (`Wettkampf_id`, `Geraete_id`, `Reihenfolge`, `Anzahl_Versuche`, `Berechnungs_Art_id`, `Erwartete_Kampfrichter`)
SELECT @wk2, g.idGeraete, 1, 1, b.idBerechnungs_Art, 2
FROM Geraete g, Berechnungs_Art b
WHERE g.Name='Boden' AND b.Regel_Kuerzel='TURNEN_AVG';

INSERT INTO `Geraete_has_Wettkampf` (`Wettkampf_id`, `Geraete_id`, `Reihenfolge`, `Anzahl_Versuche`, `Berechnungs_Art_id`, `Erwartete_Kampfrichter`)
SELECT @wk2, g.idGeraete, 2, 1, b.idBerechnungs_Art, 2
FROM Geraete g, Berechnungs_Art b
WHERE g.Name='Schwebebalken' AND b.Regel_Kuerzel='TURNEN_AVG';

-- Riege
INSERT INTO `Riege` (`Wettkampf_id`, `Bezeichnung`, `Start_Zeit`)
VALUES (@wk1, 'Riege 1', '09:00:00'),
       (@wk2, 'Riege 1', '11:00:00');

-- Mannschaft
INSERT INTO `Mannschaft` (`Wettkampf_id`, `Name`, `Verein_id`)
SELECT @wk2, 'Team Musterstadt', v.idVerein FROM Verein v WHERE v.Kuerzel='TVM';
SET @team := LAST_INSERT_ID();

-- Personen
INSERT INTO `Personen` (`Vorname`, `Nachname`, `Geburtsdatum`, `Verein_id`, `Geschlecht`)
SELECT 'Max',  'Mustermann', '2000-01-01', v.idVerein, 'm' FROM Verein v WHERE v.Kuerzel='TVM';
SET @p1 := LAST_INSERT_ID();
INSERT INTO `Personen` (`Vorname`, `Nachname`, `Geburtsdatum`, `Verein_id`, `Geschlecht`)
SELECT 'Tim',  'Tester',     '2001-02-02', v.idVerein, 'm' FROM Verein v WHERE v.Kuerzel='TVM';
SET @p2 := LAST_INSERT_ID();
INSERT INTO `Personen` (`Vorname`, `Nachname`, `Geburtsdatum`, `Verein_id`, `Geschlecht`)
SELECT 'Jan',  'Beispiel',   '1999-03-03', v.idVerein, 'm' FROM Verein v WHERE v.Kuerzel='SFB';
SET @p3 := LAST_INSERT_ID();

-- Anmeldungen Wk1 (Einzel)
INSERT INTO `Personen_has_Wettkampf` (`Personen_id`, `Wettkampf_id`, `Startnummer`, `Riege_id`, `Start_Status`)
SELECT @p1, @wk1, 1, r.idRiege, 'Gestartet' FROM Riege r WHERE r.Wettkampf_id=@wk1;
INSERT INTO `Personen_has_Wettkampf` (`Personen_id`, `Wettkampf_id`, `Startnummer`, `Riege_id`, `Start_Status`)
SELECT @p2, @wk1, 2, r.idRiege, 'Gestartet' FROM Riege r WHERE r.Wettkampf_id=@wk1;
INSERT INTO `Personen_has_Wettkampf` (`Personen_id`, `Wettkampf_id`, `Startnummer`, `Riege_id`, `Start_Status`)
SELECT @p3, @wk1, 3, r.idRiege, 'Gestartet' FROM Riege r WHERE r.Wettkampf_id=@wk1;

-- Anmeldungen Wk2 (Mannschaft)
INSERT INTO `Personen_has_Wettkampf` (`Personen_id`, `Wettkampf_id`, `Startnummer`, `Riege_id`, `Mannschaft_id`, `Start_Status`)
SELECT @p1, @wk2, 1, r.idRiege, @team, 'Gemeldet' FROM Riege r WHERE r.Wettkampf_id=@wk2;
INSERT INTO `Personen_has_Wettkampf` (`Personen_id`, `Wettkampf_id`, `Startnummer`, `Riege_id`, `Mannschaft_id`, `Start_Status`)
SELECT @p2, @wk2, 2, r.idRiege, @team, 'Gemeldet' FROM Riege r WHERE r.Wettkampf_id=@wk2;
