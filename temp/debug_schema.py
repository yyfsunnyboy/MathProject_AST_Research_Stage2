#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to check database schema and data"""

import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查看 skills_info 表的所有列
cursor.execute("PRAGMA table_info(skills_info)")
columns = cursor.fetchall()
print("【skills_info 表结构】")
for col in columns:
    print(f"  {col[1]:<30} {col[2]}")

print("\n" + "="*60)

# 查询 gh_ApplicationsOfDerivatives
cursor.execute("SELECT * FROM skills_info WHERE skill_id = 'gh_ApplicationsOfDerivatives'")
row = cursor.fetchone()

if row:
    cols = [desc[0] for desc in cursor.description]
    skill_data = dict(zip(cols, row))
    print(f"\n【gh_ApplicationsOfDerivatives 详细信息】")
    for key, value in skill_data.items():
        if value:
            print(f"{key}: {value}")
        else:
            print(f"{key}: (NULL)")
else:
    print("技能未找到")

conn.close()
