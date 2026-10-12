#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="imperial_${TIMESTAMP}.sql.gz"

echo "[backup] Creando backup: ${FILENAME}"

docker compose exec -T db pg_dump \
  -U "${POSTGRES_USER:-imperial}" \
  -d "${POSTGRES_DB:-imperial}" \
  --no-owner \
  --no-privileges \
  --format=plain \
  | gzip > "${BACKUP_DIR}/${FILENAME}"

echo "[backup] Backup creado: ${BACKUP_DIR}/${FILENAME}"

# Retener solo los últimos 14 backups
ls -t "${BACKUP_DIR}"/imperial_*.sql.gz | tail -n +15 | xargs -r rm
echo "[backup] Limpieza de backups antiguos completada"
