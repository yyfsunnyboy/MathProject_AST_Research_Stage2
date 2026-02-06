#!/usr/bin/env python3
"""檢查資料庫結構"""
import sqlite3
from pathlib import Path

DB_PATH = Path("instance/kumon_math.db")

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# 列出所有表格
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("資料庫表格清單:")
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*80)

# 檢查 textbook_example 表的列
cursor.execute("PRAGMA table_info(textbook_example)")
columns = cursor.fetchall()
print("\ntextbook_example 表的列:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# 隨機查看一些例題
print("\n" + "="*80)
print("隨機樣本 - textbook_example:")
cursor.execute("SELECT * FROM textbook_example LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"列數: {len(row)}")
    cursor.execute("PRAGMA table_info(textbook_example)")
    cols = cursor.fetchall()
    for i, col in enumerate(cols):
        if row[i]:
            val = str(row[i])[:100]
            print(f"  {col[1]}: {val}...")

conn.close()
