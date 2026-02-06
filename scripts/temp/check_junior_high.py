#!/usr/bin/env python3
"""查看國中技能的情況"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查詢所有國中技能
cursor.execute("SELECT DISTINCT skill_id FROM textbook_examples WHERE skill_id LIKE 'jh_%' ORDER BY skill_id")
jh_skills = [s[0] for s in cursor.fetchall()]

print(f'資料庫中國中技能數: {len(jh_skills)}\n')

# 查看整數四則運算相關
print('【整數四則運算相關技能】')
print('=' * 80)
count_found = 0
for skill_id in jh_skills:
    if any(x in skill_id for x in ['Integer', 'integer', '整數']):
        cursor.execute('SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?', (skill_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f'{skill_id}: {count}個例題')
            count_found += 1

print(f"\n找到 {count_found} 個相關技能")

# 同時看看 backup_GenByGemini 中國中技能的複雜度
from pathlib import Path

jh_files = list(Path('skills/backup_GenByGemini').glob('jh_*.py'))
print(f'\n\nGemini 生成的國中技能數: {len(jh_files)}')

# 查看複雜度分佈
simple = 0
medium = 0
complex_count = 0

for filepath in jh_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = len(f.readlines())
    
    if lines > 300:
        complex_count += 1
    elif lines > 150:
        medium += 1
    else:
        simple += 1

print(f'複雜度分佈: 簡({simple}) 中({medium}) 複({complex_count})')
print(f'平均行數: {sum(len(open(f).readlines()) for f in jh_files) // len(jh_files)}')

conn.close()
