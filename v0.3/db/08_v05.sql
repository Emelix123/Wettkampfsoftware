-- =====================================================
-- Migration v0.5 (idempotent):
--   * Neue Berechnungs-Arten: Turnen mit 1 Kampfrichter
--     - TURNEN_DE_PENALTY:     D + E - Penalty
--     - TURNEN_DE_PENALTY_B10: D + (10 - E-Abzug) - Penalty
--
-- Fuer bestehende DB-Volumes laeuft dieselbe Logik auch beim App-Start
-- (app/migrations.py) — dieses Script ist fuer frische Installationen
-- bzw. manuelles Einspielen:
--   docker compose exec -T db mysql -uwettkampf -p wettkampfDB < db/08_v05.sql
-- =====================================================
USE wettkampfDB;

INSERT IGNORE INTO `Berechnungs_Art` (`Regel_Kuerzel`, `Bezeichnung`, `Beschreibung`) VALUES
('TURNEN_DE_PENALTY',     'Turnen: D + E - Penalty (1 KR)',
 'D-Note + E-Note - Penalty (optional). Fuer 1 Kampfrichter; bei mehreren wird gemittelt.'),
('TURNEN_DE_PENALTY_B10', 'Turnen: D + (10 - E-Abzug) - Penalty (1 KR)',
 'Kampfrichter traegt nur den E-Abzug ein, System rechnet E = 10 - Abzug. Score = D + E - Penalty.');
