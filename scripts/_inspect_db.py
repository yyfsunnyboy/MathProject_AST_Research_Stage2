import sqlite3
import os

db_path = r'E:\Python\MathProject_AST_Research\instance\benchmark_20260219_142702.db'
if not os.path.exists(db_path):
    print(f"DB file not found at {db_path}")
else:
    print(f"Opening DB: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    conn.close()
