-- a) Alle Wettkampftage anzeigen
SELECT * FROM `wettkampfDB`.`Wettkampf_Tag`;

-- b) Alle Geräte, sortiert nach Name
SELECT * FROM `wettkampfDB`.`Geraete` ORDER BY `Name`;

-- c) Alle Personen aus dem 'Turnverein Musterstadt'
SELECT `Vorname`, `Nachname`, `Geburtsdatum`
FROM `wettkampfDB`.`Personen`
WHERE `Verein` = 'Turnverein Musterstadt';

-- d) Alle Wettkämpfe, die am 'Frühjahrsmeeting 2024' stattfinden (JOIN)
SELECT w.`Wettkampf_Nr`, w.`Name` AS WettkampfName, w.`Altersklasse`, wt.`Name` AS TagName, wt.`Wettkampf_Datum`
FROM `wettkampfDB`.`Wettkampf` w
JOIN `wettkampfDB`.`Wettkampf_Tag` wt ON w.`Wettkampf_Tag_idWettkampf_Tag` = wt.`idWettkampf_Tag`
WHERE wt.`Name` = 'Frühjahrsmeeting 2024';

-- e) Alle Geräte, die im Wettkampf 'Mehrkampf U18 Männlich' verwendet werden (mehrere JOINs)
SELECT g.`Name` AS GeraetName, g.`Berechnung_Variante_Beschreibung`, ghw.`Anzahl_Durchfuehrungen`
FROM `wettkampfDB`.`Geraete` g
JOIN `wettkampfDB`.`Geraete_has_Wettkampf` ghw ON g.`idGeraete` = ghw.`Geraete_idGeraete`
JOIN `wettkampfDB`.`Wettkampf` w ON ghw.`Wettkampf_idWettkampf` = w.`idWettkampf`
WHERE w.`Name` = 'Mehrkampf U18 Männlich';

-- f) Alle Teilnehmer (Personen) des Wettkampfs 'Mehrkampf U18 Weiblich'
SELECT p.`Vorname`, p.`Nachname`, p.`Verein`
FROM `wettkampfDB`.`Personen` p
JOIN `wettkampfDB`.`Personen_has_Wettkampf` phw ON p.`idPersonen` = phw.`Personen_idPersonen`
JOIN `wettkampfDB`.`Wettkampf` w ON phw.`Wettkampf_idWettkampf` = w.`idWettkampf`
WHERE w.`Name` = 'Mehrkampf U18 Weiblich';

-- g) Einzelergebnisse von 'Max Mustermann' für den Wettkampf 'Mehrkampf U18 Männlich'
SELECT p.`Vorname`, p.`Nachname`, g.`Name` AS Geraet, ee.`Var1`, ee.`Var2`, ee.`Var3`, ee.`Score`, w.`Name` AS Wettkampf
FROM `wettkampfDB`.`Einzel_Ergebnis` ee
JOIN `wettkampfDB`.`Personen` p ON ee.`Personen_idPersonen` = p.`idPersonen`
JOIN `wettkampfDB`.`Geraete_has_Wettkampf` ghw ON ee.`Geraete_Wettkampf_idGeraete_Wettkampf` = ghw.`idGeraete_Wettkampf`
JOIN `wettkampfDB`.`Geraete` g ON ghw.`Geraete_idGeraete` = g.`idGeraete`
JOIN `wettkampfDB`.`Wettkampf` w ON ghw.`Wettkampf_idWettkampf` = w.`idWettkampf`
WHERE p.`Vorname` = 'Max' AND p.`Nachname` = 'Mustermann' AND w.`Name` = 'Mehrkampf U18 Männlich';

-- h) Gesamtergebnisse (Rangliste) für den Wettkampf 'Mehrkampf U18 Männlich'
SELECT p.`Vorname`, p.`Nachname`, p.`Verein`, ge.`GesamtScore`, ge.`Berechnet_Am`
FROM `wettkampfDB`.`Gesamt_Ergebnisse` ge
JOIN `wettkampfDB`.`Personen` p ON ge.`Personen_idPersonen` = p.`idPersonen`
JOIN `wettkampfDB`.`Wettkampf` w ON ge.`Wettkampf_idWettkampf` = w.`idWettkampf`
WHERE w.`Name` = 'Mehrkampf U18 Männlich'
ORDER BY ge.`GesamtScore` DESC; -- DESC für höhere Scores sind besser, ASC wenn niedriger besser (z.B. Zeit)

-- i) Anzahl der Teilnehmer pro Wettkampf
SELECT w.`Name` AS WettkampfName, COUNT(phw.`Personen_idPersonen`) AS AnzahlTeilnehmer
FROM `wettkampfDB`.`Wettkampf` w
LEFT JOIN `wettkampfDB`.`Personen_has_Wettkampf` phw ON w.`idWettkampf` = phw.`Wettkampf_idWettkampf`
GROUP BY w.`idWettkampf`, w.`Name`
ORDER BY AnzahlTeilnehmer DESC;

-- j) Durchschnittlicher Score pro Gerät im Wettkampf 'Einzeldisziplinen Offen'
SELECT g.`Name` AS GeraetName, AVG(ee.`Score`) AS DurchschnittsScore
FROM `wettkampfDB`.`Einzel_Ergebnis` ee
JOIN `wettkampfDB`.`Geraete_has_Wettkampf` ghw ON ee.`Geraete_Wettkampf_idGeraete_Wettkampf` = ghw.`idGeraete_Wettkampf`
JOIN `wettkampfDB`.`Geraete` g ON ghw.`Geraete_idGeraete` = g.`idGeraete`
JOIN `wettkampfDB`.`Wettkampf` w ON ghw.`Wettkampf_idWettkampf` = w.`idWettkampf`
WHERE w.`Name` = 'Einzeldisziplinen Offen'
GROUP BY g.`idGeraete`, g.`Name`
ORDER BY DurchschnittsScore DESC;

SELECT idPersonen FROM Personen WHERE Vorname = 'Emil' AND Nachname = 'Mertz' AND Geburtsdatum = '2005-09-15';

SELECT * FROM Personen;

INSERT INTO Personen (Vorname, Nachname, Geburtsdatum, Verein, Geschlecht) VALUES ('Emil', 'Mertz', '2005-09-15', 'TV Kork', 'm');

INSERT INTO Personen_has_Wettkampf (Personen_idPersonen, Wettkampf_idWettkampf, Riege) VALUES (5, 4, 5);

SELECT
    RANK() OVER (ORDER BY ge.GesamtScore DESC) AS Platz,
    p.Vorname,
    p.Nachname,
    p.Verein,
    ge.GesamtScore,
    w.Name AS WettkampfName
FROM Gesamt_Ergebnisse ge
JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen
JOIN Wettkampf w ON ge.Wettkampf_idWettkampf = w.idWettkampf
WHERE ge.Wettkampf_idWettkampf = 2
ORDER BY Platz;

SELECT
    w.Name AS WettkampfName,
    RANK() OVER (PARTITION BY ge.Wettkampf_idWettkampf ORDER BY ge.GesamtScore DESC) AS Platz,
    p.Vorname,
    p.Nachname,
    p.Verein,
    ge.GesamtScore
FROM Gesamt_Ergebnisse ge
JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen
JOIN Wettkampf w ON ge.Wettkampf_idWettkampf = w.idWettkampf
WHERE w.Wettkampf_Tag_idWettkampf_Tag = %s
ORDER BY w.Name, Platz;

SELECT
    w.Name AS WettkampfName,
    RANK() OVER (PARTITION BY ge.Wettkampf_idWettkampf ORDER BY ge.GesamtScore DESC) AS Platz,
    p.Vorname,
    p.Nachname,
    p.Verein,
    ge.GesamtScore
FROM Gesamt_Ergebnisse ge
JOIN Personen p ON ge.Personen_idPersonen = p.idPersonen
JOIN Wettkampf w ON ge.Wettkampf_idWettkampf = w.idWettkampf
WHERE w.Wettkampf_Tag_idWettkampf_Tag = 1
ORDER BY w.Name, Platz;

SELECT idGeraete_Wettkampf 
            FROM Geraete_has_Wettkampf 
            WHERE Wettkampf_idWettkampf = 1 AND Geraete_idGeraete = 1;

SELECT 
    p.idPersonen, p.Vorname, p.Nachname, p.Verein, phw.Riege,
    ee.idEinzel_Ergebnis
FROM Personen p
JOIN Personen_has_Wettkampf phw ON p.idPersonen = phw.Personen_idPersonen
LEFT JOIN Einzel_Ergebnis ee ON p.idPersonen = ee.Personen_idPersonen 
    AND ee.Geraete_Wettkampf_idGeraete_Wettkampf = 1
WHERE phw.Wettkampf_idWettkampf = 1

INSERT INTO Einzel_Ergebnis 
            (Geraete_Wettkampf_idGeraete_Wettkampf, Personen_idPersonen, Versuch_Nr, 
             Var1, Var2, Var3, Var4, Var5, Var6, Var7, Var8, Var9, Var10)
            VALUES (1,2,2,5,3,0,0,0,0,0,0,0,5);

SELECT
    idEinzel_Ergebnis,
    Geraete_Wettkampf_idGeraete_Wettkampf,
    Personen_idPersonen,
    Versuch_Nr,
    Score,
    Var1, Var2, Var3, Var4, Var5,
    Var6, Var7, Var8, Var9, Var10
FROM Einzel_Ergebnis
WHERE Personen_idPersonen = 10 AND Geraete_Wettkampf_idGeraete_Wettkampf = 1
ORDER BY Personen_idPersonen, Versuch_Nr

SELECT g.idGeraete, g.Name, g.Anzahl_Var, g.Berechnung_Variante, ghw.idGeraete_Wettkampf, ghw.Anzahl_Durchfuehrungen
            FROM Geraete g
            JOIN Geraete_has_Wettkampf ghw ON g.idGeraete = ghw.Geraete_idGeraete
            WHERE ghw.Wettkampf_idWettkampf = 1
            ORDER BY g.Name
