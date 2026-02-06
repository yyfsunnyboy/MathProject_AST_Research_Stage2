#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
檢查 MCRI 評分表是否在資料庫中
"""
import sqlite3
import os

db_path = r'E:\Python\MathProject_AST_Research\textbook_data.db'

if not os.path.exists(db_path):
    print(f"❌ 資料庫不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 查詢所有表格
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = c.fetchall()

print('📊 資料庫中的所有表格：')
print('=' * 70)
for table in tables:
    print(f'  ✓ {table[0]}')

print(f'\n總共 {len(tables)} 個表格')

# 檢查關鍵的 MCRI 表
print('\n🔍 關鍵 MCRI 表檢查：')
print('=' * 70)
mcri_tables = ['ablation_summary', 'experiment_runs', 'evaluation_items']
for table_name in mcri_tables:
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = c.fetchone()
    status = '✅ 存在' if result else '❌ 不存在'
    print(f'  {table_name}: {status}')

conn.close()
