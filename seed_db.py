import sqlite3, os, sys

db_path = 'mvp_data.db'
if not os.path.exists(db_path):
    db_path = 'client_data.db'
print(f"Using DB: {db_path}")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

# Check tenants if it exists
if 'tenants' in tables:
    cur.execute('SELECT id, name, api_key, plan FROM tenants LIMIT 10')
    rows = cur.fetchall()
    print('Tenants:', rows)
    
    # Check if our test key exists
    cur.execute("SELECT id FROM tenants WHERE api_key = 'sk-test-key-123'")
    exists = cur.fetchone()
    if not exists:
        print("Test key NOT found — inserting...")
        cur.execute("""
            INSERT OR IGNORE INTO tenants (id, name, api_key, plan, created_at)
            VALUES ('tenant-local', 'Xenia Local', 'sk-test-key-123', 'enterprise', datetime('now'))
        """)
        conn.commit()
        print("Inserted tenant with api_key = sk-test-key-123")
    else:
        print(f"Test key found for tenant: {exists[0]}")
else:
    print("No tenants table! Creating it...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT,
            api_key TEXT UNIQUE,
            plan TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO tenants (id, name, api_key, plan, created_at)
        VALUES ('tenant-local', 'Xenia Local', 'sk-test-key-123', 'enterprise', datetime('now'))
    """)
    conn.commit()
    print("Created tenants table and inserted test tenant")

# Verify
cur.execute("SELECT id, api_key FROM tenants WHERE api_key = 'sk-test-key-123'")
row = cur.fetchone()
print(f"Verified: {row}")

conn.close()
