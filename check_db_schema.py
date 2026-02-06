#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""檢查資料庫 schema"""

import sqlite3
from pathlib import Path

db_path = Path('instance/kumon_math.db')

if not db_path.exists():
    print(f"[ERROR] Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 檢查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f'\n{"="*70}')
    print(f'TABLE: {table_name}')
    print("="*70)
    
    # 取得表結構
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    
    for col in columns:
        cid, name, type_, notnull, default_val, pk = col
        print(f'{cid+1:2d}. {name:35s} {type_:15s} PK={pk}')
    
    print(f'\nTotal columns: {len(columns)}')

conn.close()
