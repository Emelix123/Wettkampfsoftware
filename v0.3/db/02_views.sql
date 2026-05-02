USE wettkampfDB;

-- =====================================================
-- VIEWs ersetzen die Cache-Tabellen aus v6.
-- Sie aggregieren immer live aus Einzel_Ergebnis.
-- Für die kleine Datenmenge eines Wettkampftags ist das mehr als schnell genug.
-- =====================================================

-- Bester gültiger Score pro Person+Wettkampf+Gerät
CREATE OR REPLACE VIEW `vw_Person_Geraet_Best` AS
SELECT
    ee.Personen_id,
    ee.Wettkampf_id,
    ee.Geraete_id,
    MAX(ee.Score) AS BesterScore
FROM Einzel_Ergebnis ee
WHERE ee.Ist_Gueltig = 1
  AND ee.Status      = 'Freigegeben'
  AND ee.Score IS NOT NULL
GROUP BY ee.Personen_id, ee.Wettkampf_id, ee.Geraete_id;

-- Einzel-Gesamtwertung: Summe der besten Scores pro Gerät
CREATE OR REPLACE VIEW `vw_Gesamt_Ergebnisse` AS
SELECT
    phw.Wettkampf_id,
    phw.Personen_id,
    IFNULL(SUM(b.BesterScore), 0) AS GesamtScore,
    COUNT(b.Geraete_id)           AS Anzahl_Geraete_Gewertet
FROM Personen_has_Wettkampf phw
LEFT JOIN vw_Person_Geraet_Best b
       ON b.Personen_id   = phw.Personen_id
      AND b.Wettkampf_id  = phw.Wettkampf_id
WHERE phw.Start_Status IN ('Gemeldet','Gestartet')
GROUP BY phw.Wettkampf_id, phw.Personen_id;

-- Einzel-Rangliste mit Platz (Window-Function)
CREATE OR REPLACE VIEW `vw_Rangliste_Einzel` AS
SELECT
    g.Wettkampf_id,
    g.Personen_id,
    p.Vorname,
    p.Nachname,
    p.Geschlecht,
    v.Kuerzel  AS Verein_Kuerzel,
    v.Name     AS Verein_Name,
    g.GesamtScore,
    g.Anzahl_Geraete_Gewertet,
    RANK() OVER (PARTITION BY g.Wettkampf_id ORDER BY g.GesamtScore DESC) AS Platz
FROM vw_Gesamt_Ergebnisse g
JOIN Personen p ON p.idPersonen = g.Personen_id
LEFT JOIN Verein v ON v.idVerein = p.Verein_id;

-- Mannschaftswertung: Summe ALLER Mitglieder (Streichwerte: Backend macht's,
-- aber für die Standard-View nehmen wir alle, weil Mannschaft_Groesse NULL = unbegrenzt).
-- Wenn Mannschaft_Groesse gesetzt ist, summiert das Backend selbst die besten N.
CREATE OR REPLACE VIEW `vw_Mannschaft_Score_All` AS
SELECT
    m.idMannschaft,
    m.Wettkampf_id,
    m.Name AS Mannschaft_Name,
    SUM(g.GesamtScore) AS GesamtScore_Alle,
    COUNT(phw.Personen_id) AS Mitglieder_Gesamt
FROM Mannschaft m
LEFT JOIN Personen_has_Wettkampf phw
       ON phw.Mannschaft_id = m.idMannschaft
      AND phw.Wettkampf_id  = m.Wettkampf_id
LEFT JOIN vw_Gesamt_Ergebnisse g
       ON g.Personen_id  = phw.Personen_id
      AND g.Wettkampf_id = phw.Wettkampf_id
GROUP BY m.idMannschaft, m.Wettkampf_id, m.Name;
