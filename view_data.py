import sqlite3
import json

conn = sqlite3.connect('./data/database.sqlite')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

data = {}
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    data[table_name] = [dict(zip(columns, row)) for row in rows]

conn.close()

print(json.dumps(data, indent=2))