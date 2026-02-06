#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱：migrate_experiment_runs_v2.py
版本：V1.0
作者：Math AI Research Team
最後更新日期：2026-02-05
用途：將新欄位遷移到 experiment_runs 表（kumon_math.db）
=============================================================================

新增欄位分類：

1. 批次管理 (Batch Management)
   - batch_id: 批次 ID，用於一次撈出某次跑的 50 筆數據

2. Golden Prompt 變因控制 (Control Variables)
   - golden_prompt_path: Golden Prompt 文件路徑
   - prompt_hash: Prompt SHA256 雜湊值

3. 成本與效能指標 (Cost & Performance)
   - prompt_tokens: Prompt Token 數
   - completion_tokens: 完成 Token 數
   - total_tokens: 總 Token 數
   - latency_ms: 延遲（毫秒）

4. Healer 介入統計 (Healer Metrics)
   - healer_applied: 是否啟用 Healer (BOOLEAN)
   - healer_fix_count: Healer 修復次數 (INTEGER)

=============================================================================
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = r'E:\Python\MathProject_AST_Research\instance\kumon_math.db'

def migrate_experiment_runs_table():
    """遷移 experiment_runs 表，新增 8 個欄位"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 資料庫不存在: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        print('='*80)
        print('📊 開始遷移 experiment_runs 表')
        print('='*80)
        
        # 檢查表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiment_runs'")
        if not c.fetchone():
            print("❌ experiment_runs 表不存在！")
            return False
        
        # 取得現有欄位列表
        c.execute("PRAGMA table_info(experiment_runs)")
        existing_columns = {row[1] for row in c.fetchall()}
        
        # 定義要新增的欄位
        new_columns = {
            'batch_id': 'VARCHAR(50)',
            'golden_prompt_path': 'VARCHAR(255)',
            'prompt_hash': 'VARCHAR(64)',
            'prompt_tokens': 'INTEGER',
            'completion_tokens': 'INTEGER',
            'total_tokens': 'INTEGER',
            'latency_ms': 'INTEGER',
            'healer_applied': 'BOOLEAN DEFAULT 0',
            'healer_fix_count': 'INTEGER DEFAULT 0'
        }
        
        # 新增缺失的欄位
        added_count = 0
        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                print(f"  ⏳ 新增欄位: {col_name:<25} {col_def}")
                try:
                    c.execute(f"ALTER TABLE experiment_runs ADD COLUMN {col_name} {col_def}")
                    added_count += 1
                    print(f"  ✅ {col_name} 新增成功")
                except sqlite3.OperationalError as e:
                    print(f"  ⚠️  {col_name} 新增失敗: {str(e)}")
            else:
                print(f"  ℹ️  {col_name} 已存在（略過）")
        
        conn.commit()
        
        # 驗證遷移結果
        print('\n📋 驗證遷移結果...')
        print('='*80)
        c.execute("PRAGMA table_info(experiment_runs)")
        columns = c.fetchall()
        print(f"✅ experiment_runs 現有欄位數: {len(columns)}")
        
        # 列出所有新欄位
        print('\n🆕 新增的欄位：')
        for col_name in new_columns.keys():
            if col_name in {row[1] for row in columns}:
                print(f"  ✅ {col_name}")
        
        # 查詢數據行數
        c.execute("SELECT COUNT(*) FROM experiment_runs")
        row_count = c.fetchone()[0]
        print(f'\n📊 experiment_runs 表中的數據行數: {row_count}')
        
        conn.close()
        
        print('\n' + '='*80)
        print(f'✅ 遷移完成！新增了 {added_count} 個欄位')
        print('='*80)
        
        return True
        
    except Exception as e:
        print(f"❌ 遷移失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    migrate_experiment_runs_table()
