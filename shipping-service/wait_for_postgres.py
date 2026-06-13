import os
import socket
import sys
import time


host = os.getenv("DB_POSTGRES_HOST", "postgres")
port = int(os.getenv("DB_POSTGRES_PORT", "5432"))
timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))

for i in range(timeout):
    try:
        with socket.create_connection((host, port), 2):
            print(f"Postgres reachable at {host}:{port}")
            sys.exit(0)
    except Exception:
        print(f"Waiting for Postgres {host}:{port} ({i+1}/{timeout})")
        time.sleep(1)

print(f"Timed out waiting for Postgres at {host}:{port}")
sys.exit(1)
