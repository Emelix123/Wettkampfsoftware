#!/usr/bin/env bash
# Vollstaendiger MySQL-Dump der Wettkampf-DB in ./backups/.
# Am Wettkampftag am besten regelmaessig laufen lassen, z.B. alle 10 Minuten:
#   watch -n 600 ./scripts/backup_db.sh
# oder per cron:
#   */10 * * * * cd /pfad/zu/v0.3 && ./scripts/backup_db.sh
#
# Zugangsdaten kommen aus .env (gleiche Werte wie docker-compose).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
DB_USER="${DB_USER:-wettkampf}"
DB_PASSWORD="${DB_PASSWORD:-wettkampf}"
DB_NAME="${DB_NAME:-wettkampfDB}"

mkdir -p backups
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="backups/${DB_NAME}-${STAMP}.sql.gz"

docker compose exec -T db mysqldump \
  -u"${DB_USER}" -p"${DB_PASSWORD}" \
  --single-transaction --routines --triggers "${DB_NAME}" \
  | gzip > "${OUT}"

echo "Backup geschrieben: ${OUT} ($(du -h "${OUT}" | cut -f1))"

# Alte Backups aufraeumen: die letzten 100 behalten
ls -1t backups/${DB_NAME}-*.sql.gz 2>/dev/null | tail -n +101 | xargs -r rm --
