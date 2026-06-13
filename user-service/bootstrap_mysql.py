import os
import sys
import time

import pymysql


def main() -> int:
    host = os.getenv("DB_MYSQL_HOST", "mysql")
    port = int(os.getenv("DB_MYSQL_PORT", "3306"))
    user = os.getenv("DB_MYSQL_USER", "root")
    password = os.getenv("DB_MYSQL_PASSWORD", "123456")
    db_name = os.getenv("DB_MYSQL_NAME", "user_service_db")
    timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))

    for i in range(timeout):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset="utf8mb4",
                autocommit=True,
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.close()
            print(f"MySQL ready and ensured database '{db_name}' exists.")
            return 0
        except Exception as exc:
            print(f"Waiting for MySQL/bootstrap ({i + 1}/{timeout}): {exc}")
            time.sleep(1)

    print("Timed out waiting for MySQL/bootstrap.")
    return 1


if __name__ == "__main__":
    sys.exit(main())