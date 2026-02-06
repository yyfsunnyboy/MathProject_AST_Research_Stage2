#!/usr/bin/env python3
"""查看之前 debug 過的技能"""
import sqlite3
from pathlib import Path

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查詢整數和分數四則運算技能
print('【實際 Debug 過的技能】')
print('=' * 80)

test_skills = [
    'jh_數學1上_FourArithmeticOperationsOfIntegers',
    'jh_數學1上_IntegerAdditionOperation',
    'jh_數學1上_FractionAdditionAndSubtraction',
    'jh_數學1上_FractionMultiplication',
    'jh_數學1上_FractionDivision'
]

for skill_id in test_skills:
    cursor.execute('SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?', (skill_id,))
    count = cursor.fetchone()[0]
    if count > 0:
        print(f'{skill_id}: {count}個例題')

# 查詢系統中是否有 golden skills 或測試記錄
print('\n\n【檢查系統中的測試記錄表】')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()
print(f'所有表格: {[t[0] for t in all_tables]}')

# 查詢 regression_test 或類似的測試結果
for table in all_tables:
    table_name = table[0]
    if 'test' in table_name.lower() or 'log' in table_name.lower() or 'experiment' in table_name.lower():
        print(f'\n發現相關表格: {table_name}')
        cursor.execute(f'PRAGMA table_info({table_name})')
        cols = cursor.fetchall()
        print(f'  列: {[c[1] for c in cols[:5]]}...')

conn.close()

# 查看系統中已有的技能文件
print('\n\n【系統中已有的技能文件（skills/）】')
print('=' * 80)

skills_dir = Path('skills')
if skills_dir.exists():
    py_files = list(skills_dir.glob('*.py'))
    print(f'總共: {len(py_files)} 個技能文件')
    
    # 找出整數、分數相關的
    related = [f for f in py_files if any(x in f.name for x in ['integer', '整數', 'fraction', '分數', '加', '減', '乘', '除'])]
    print(f'\n整數/分數四則運算相關: {len(related)} 個')
    for f in related[:10]:
        print(f'  - {f.name}')
