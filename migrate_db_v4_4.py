#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫 Migration: 添加 V4.4 新增的欄位
安全地添加缺失的欄位而不刪除現有資料
"""

import sqlite3
from pathlib import Path

db_path = Path('instance/kumon_math.db')

if not db_path.exists():
    print(f"[ERROR] Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("[INFO] Starting database migration for V4.4...")
print("="*70)

# Step 1: 檢查 experiment_runs 缺失的欄位
print("\n[STEP 1] Checking experiment_runs table...")
cursor.execute('PRAGMA table_info(experiment_runs)')
existing_cols = {col[1] for col in cursor.fetchall()}

missing_in_runs = [
    ('avg_l4_3_artifacts', 'FLOAT'),
    ('avg_complexity_math_ops', 'FLOAT'),
    ('avg_complexity_ast_nodes', 'FLOAT'),
    ('avg_complexity_loop_depth', 'FLOAT'),
]

for col_name, col_type in missing_in_runs:
    if col_name not in existing_cols:
        try:
            cursor.execute(f'ALTER TABLE experiment_runs ADD COLUMN {col_name} {col_type}')
            print(f"  ✓ Added column: {col_name} ({col_type})")
        except Exception as e:
            print(f"  ✗ Error adding {col_name}: {e}")
    else:
        print(f"  ~ Column already exists: {col_name}")

# Step 2: 檢查 evaluation_items 缺失的欄位
print("\n[STEP 2] Checking evaluation_items table...")
cursor.execute('PRAGMA table_info(evaluation_items)')
existing_cols = {col[1] for col in cursor.fetchall()}

missing_in_items = [
    ('complexity_math_ops', 'INTEGER'),
    ('complexity_ast_nodes', 'INTEGER'),
    ('complexity_loop_depth', 'INTEGER'),
]

for col_name, col_type in missing_in_items:
    if col_name not in existing_cols:
        try:
            cursor.execute(f'ALTER TABLE evaluation_items ADD COLUMN {col_name} {col_type}')
            print(f"  ✓ Added column: {col_name} ({col_type})")
        except Exception as e:
            print(f"  ✗ Error adding {col_name}: {e}")
    else:
        print(f"  ~ Column already exists: {col_name}")

# Step 3: 提交變更
print("\n[STEP 3] Committing changes...")
conn.commit()

# Step 4: 驗證
print("\n[STEP 4] Verifying schema...")
cursor.execute('PRAGMA table_info(experiment_runs)')
runs_cols = {col[1] for col in cursor.fetchall()}
print(f"  experiment_runs: {len(runs_cols)} columns")

cursor.execute('PRAGMA table_info(evaluation_items)')
items_cols = {col[1] for col in cursor.fetchall()}
print(f"  evaluation_items: {len(items_cols)} columns")

cursor.execute('PRAGMA table_info(ablation_summary)')
summary_cols = {col[1] for col in cursor.fetchall()}
print(f"  ablation_summary: {len(summary_cols)} columns")

conn.close()

print("\n" + "="*70)
print("[OK] Database migration completed successfully!")
print("     No existing data was deleted.")
print("     New columns initialized with NULL/0 values.")
