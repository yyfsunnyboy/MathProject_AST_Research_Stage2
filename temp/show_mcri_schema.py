#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
詳細查看 kumon_math.db 中的三層 MCRI 評分表結構
"""
import sqlite3

db_path = r'E:\Python\MathProject_AST_Research\instance\kumon_math.db'

conn = sqlite3.connect(db_path)
c = conn.cursor()

tables_info = {
    'ablation_summary': '🌟 第一層：彙總統計表（統計推論層）',
    'experiment_runs': '📊 第二層：實驗主表（實驗控制層）',
    'evaluation_items': '📝 第三層：評估明細表（原始數據層）'
}

for table_name, description in tables_info.items():
    print(f'\n{"="*80}')
    print(f'{description}')
    print(f'表名: {table_name}')
    print(f'{"="*80}')
    
    # 查詢表結構
    c.execute(f"PRAGMA table_info({table_name})")
    columns = c.fetchall()
    
    print(f'\n欄位數: {len(columns)}\n')
    print(f'{"欄位名":<30} {"類型":<15} {"說明"}')
    print('-' * 80)
    
    for col_id, col_name, col_type, notnull, default_val, pk in columns:
        pk_marker = '🔑' if pk else '  '
        null_marker = 'NOT NULL' if notnull else 'NULLABLE'
        print(f'{pk_marker} {col_name:<28} {col_type:<15} {null_marker}')
    
    # 查詢數據統計
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = c.fetchone()[0]
    print(f'\n當前數據行數: {row_count}')

conn.close()

print(f'\n{"="*80}')
print('✅ 三層 MCRI 評分表結構查詢完成！')
print(f'{"="*80}')
