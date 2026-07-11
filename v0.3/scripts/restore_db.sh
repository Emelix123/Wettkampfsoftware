#!/usr/bin/env bash
# Stellt einen mit backup_db.sh erzeugten Dump wieder her.
#   ./scripts/restore_db.sh backups/wettkampfDB-20260711-101500.sql.gz
#
# ACHTUNG: ueberschreibt den aktuellen Stand der Datenbank!
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -ne 1 ] || [ ! -f "$1" ]; then
  echo "Aufruf: $0 <backup-datei.sql.gz>" >&2
  exit 1
fi

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
DB_USER="${DB_USER:-wettkampf}"
DB_PASSWORD="${DB_PASSWORD:-wettkampf}"
DB_NAME="${DB_NAME:-wettkampfDB}"

read -r -p "Datenbank '${DB_NAME}' mit '$1' UEBERSCHREIBEN? (ja/nein) " antwort
if [ "${antwort}" != "ja" ]; then
  echo "Abgebrochen."
  exit 1
fi

gunzip -c "$1" | docker compose exec -T db mysql \
  -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}"

echo "Restore fertig. App neu starten: docker compose restart app"
