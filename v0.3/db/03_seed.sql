USE wettkampfDB;

-- =====================================================
-- Seed: Stammdaten + Default-Admin
-- Default-Admin Login:  admin / admin123
--   bcrypt-Hash erzeugt mit:
--   python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
-- BITTE NACH DEM ERSTEN LOGIN ÄNDERN.
-- =====================================================

-- Berechnungs-Arten (Schlüssel auf Python-Strategy)
INSERT INTO `Berechnungs_Art` (`Regel_Kuerzel`, `Bezeichnung`, `Beschreibung`) VALUES
('TURNEN_OLYMPIC_TRIM', 'Turnen Olympisch (E-Note Trim)', 'D-Note + Schnitt der E-Noten ohne hoechste/niedrigste Wertung - Abzug.'),
('TURNEN_AVG',          'Turnen Schnitt aller Wertungen', 'D-Note + Schnitt aller E-Noten - Abzug.'),
('LA_DIRECT',           'Leichtathletik Direkt',          'Score = Wert * Faktor + Offset (Weite/Hoehe).'),
('LA_SPRINT',           'Leichtathletik Sprint/Zeit',     'Score = Offset - Wert * Faktor (kleiner Wert = besser).'),
('MANUELL',             'Manuell',                        'Wert wird direkt als Score uebernommen.');

-- Altersklassen (Beispiele)
INSERT INTO `Altersklasse` (`Kuerzel`, `Bezeichnung`, `Alter_Von`, `Alter_Bis`, `Geschlecht`) VALUES
('Offen', 'Offen fuer alle',  NULL, NULL, 'alle'),
('U18M',  'Under 18 Maennlich',14, 17, 'm'),
('U18W',  'Under 18 Weiblich', 14, 17, 'w');

-- Geraete (Turnen-Beispiel)
INSERT INTO `Geraete` (`Name`, `Einheit`, `Beschreibung`) VALUES
('Boden',     'Pkt', 'Bodenturnen'),
('Reck',      'Pkt', 'Reck'),
('Barren',    'Pkt', 'Barren'),
('Sprung',    'Pkt', 'Sprung ueber Pferd / Tisch'),
('Pauschenpferd','Pkt', 'Pauschenpferd'),
('Ringe',     'Pkt', 'Ringe'),
('Schwebebalken','Pkt', 'Schwebebalken'),
('Stufenbarren','Pkt', 'Stufenbarren');

-- Hinweis: Default-Admin wird beim ersten App-Start in Python angelegt
--          (siehe app/auth.py: ensure_default_admin), damit der bcrypt-Hash
--          immer mit der eingesetzten bcrypt-Version uebereinstimmt.
