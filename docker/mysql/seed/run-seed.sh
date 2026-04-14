#!/bin/sh
set -e

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_ROOT_PASSWORD:-123456}"

wait_mysql() {
  echo "[mysql-seeder] Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
  until mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -e "SELECT 1" >/dev/null 2>&1; do
    sleep 2
  done
  echo "[mysql-seeder] MySQL is ready."
}

wait_table() {
  db="$1"
  table="$2"

  echo "[mysql-seeder] Waiting for ${db}.${table}..."
  while : ; do
    exists=$(mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${db}' AND table_name='${table}';" 2>/dev/null || echo "0")
    if [ "${exists}" = "1" ]; then
      break
    fi
    sleep 2
  done
  echo "[mysql-seeder] Found ${db}.${table}."
}

wait_mysql
wait_table customer_service_db app_customeraccount
wait_table staff_service_db app_staffaccount
wait_table order_service_db app_order

echo "[mysql-seeder] Running MySQL seed files..."
mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" < /seeds/seed_customer_service.sql
mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" < /seeds/seed_staff_service.sql
mysql -h"${MYSQL_HOST}" -P"${MYSQL_PORT}" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" < /seeds/seed_order_service.sql

echo "[mysql-seeder] Seed completed successfully."
