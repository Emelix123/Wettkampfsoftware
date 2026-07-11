-- =====================================================
-- NUR FUER ENTWICKLUNG: loescht die komplette Datenbank!
-- Dieses Script wird bewusst NICHT im Docker-Init gemountet.
-- Danach 01_schema.sql bis 07_v04.sql manuell einspielen
-- oder das DB-Volume loeschen (docker compose down -v).
-- =====================================================
DROP DATABASE IF EXISTS wettkampfDB;
