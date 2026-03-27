import sqlite3
import json

def main():
    db = 'db.sqlite3'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(forms_netfamilyproperty13b)")
    rows = cur.fetchall()
    print(json.dumps(rows, indent=2))
    conn.close()

if __name__ == '__main__':
    main()
