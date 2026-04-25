#!/usr/bin/env python3
"""Pre-create per-worker CKAN test databases and ini files for pytest-xdist.

Called from bin/test-ckanext-artesp-theme before launching pytest with -n.
Each worker gets its own ckan_test_gw{N} database and a corresponding
/tmp/ckan_test_gw{N}.ini that overrides sqlalchemy.url.

Usage: python3 utils/xdist_worker_setup.py <n_workers|auto>
"""
import sys
import os
import configparser

raw_n = sys.argv[1] if len(sys.argv) > 1 else "auto"
n = os.cpu_count() or 1 if raw_n == "auto" else int(raw_n)

BASE_INI = "/srv/app/src_extensions/ckanext-artesp_theme/test.ini"
INI_DIR = os.environ.get(
    "CKAN_XDIST_INI_DIR", "/srv/app/src_extensions/ckanext-artesp_theme/.pytest-xdist"
)
DB_HOST = "db"
DB_USER = "ckandbuser"
DB_PASS = "ckandbpassword"

os.makedirs(INI_DIR, exist_ok=True)

try:
    import psycopg2
    conn = psycopg2.connect(
        host=DB_HOST, dbname="postgres", user=DB_USER, password=DB_PASS
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Drop stale worker DBs first (schema may be outdated between test sessions)
    for i in range(n):
        db_name = f"ckan_test_gw{i}"
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cur.fetchone():
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (db_name,),
            )
            cur.execute(f"DROP DATABASE {db_name}")

    # Terminate connections to the template DB before cloning
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = 'ckan_test' AND pid <> pg_backend_pid()"
    )

    for i in range(n):
        db_name = f"ckan_test_gw{i}"
        # Clone from ckan_test so the schema is already initialised.
        # clean_db() will only need to DELETE data, not DROP/CREATE tables.
        cur.execute(f"CREATE DATABASE {db_name} TEMPLATE ckan_test OWNER {DB_USER}")
        print(f"Created database: {db_name}")

    cur.close()
    conn.close()
except Exception as exc:
    print(f"Error creating worker databases: {exc}", file=sys.stderr)
    sys.exit(1)

for i in range(n):
    worker_id = f"gw{i}"
    cp = configparser.RawConfigParser()
    cp.read(BASE_INI)
    # Use absolute path because worker ini lives outside the test.ini directory.
    cp.set("app:main", "use", "config:/srv/app/src/ckan/test-core.ini")
    cp.set(
        "app:main",
        "sqlalchemy.url",
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/ckan_test_{worker_id}",
    )
    dest = os.path.join(INI_DIR, f"ckan_test_{worker_id}.ini")
    with open(dest, "w") as f:
        cp.write(f)
    print(f"Created worker ini: {dest}")
