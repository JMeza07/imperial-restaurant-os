#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Uso: $0 <archivo_backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"

echo "[restore] Restaurando desde: ${BACKUP_FILE}"

gunzip -c "${BACKUP_FILE}" \
  | docker compose exec -T db psql \
      -U "${POSTGRES_USER:-imperial}" \
      -d "${POSTGRES_DB:-imperial}"

echo "[restore] Restauración completada"
