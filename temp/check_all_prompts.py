#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查詢 gh_ApplicationsOfDerivatives 的所有 prompt 記錄"""
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

rows = cur.execute('''
    SELECT id, model_tag, prompt_type, experiment_group, is_active, LENGTH(prompt_content) as len
    FROM skill_gencode_prompt 
    WHERE skill_id = "gh_ApplicationsOfDerivatives"
    ORDER BY id
''').fetchall()

print('ID  | model_tag  | prompt_type  | experiment_group | is_active | 長度')
print('='*85)
for r in rows:
    exp_group = str(r[3]) if r[3] else 'None'
    print(f'{r[0]:3d} | {r[1]:10s} | {r[2]:12s} | {exp_group:16s} | {r[4]:9d} | {r[5]:5d}')

print('\n如果你使用的是模式2或特定實驗組，應該找對應的 experiment_group')
conn.close()
