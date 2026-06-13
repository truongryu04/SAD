#!/bin/sh
set -e

PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-postgres}"
PGPASSWORD="${PGPASSWORD:-123456}"
export PGPASSWORD

wait_postgres() {
  echo "[postgres-seeder] Waiting for PostgreSQL at ${PGHOST}:${PGPORT}..."
  until psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "SELECT 1" >/dev/null 2>&1; do
    sleep 2
  done
  echo "[postgres-seeder] PostgreSQL is ready."
}

wait_table() {
  db="$1"
  table="$2"

  echo "[postgres-seeder] Waiting for ${db}.${table}..."
  while : ; do
    exists=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${db}" -tAc "SELECT to_regclass('${table}') IS NOT NULL;" 2>/dev/null || echo "f")
    if [ "${exists}" = "t" ]; then
      break
    fi
    sleep 2
  done
  echo "[postgres-seeder] Found ${db}.${table}."
}

wait_postgres
wait_table product_service_db app_product
wait_table product_service_db app_category
wait_table product_service_db app_book
wait_table product_service_db app_electronics
wait_table product_service_db app_fashion
wait_table ai_service_db app_airequest

echo "[postgres-seeder] Running PostgreSQL seed files..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d product_service_db -f /seeds/seed_category_service.sql
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d product_service_db -f /seeds/seed_product_service.sql
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d ai_service_db -f /seeds/seed_ai_service.sql

echo "[postgres-seeder] Seed completed successfully."
