#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check where MASTER_SPEC should come from"""

import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查看 SkillGenCodePrompt 表
print("【SkillGenCodePrompt 表信息】")
cursor.execute("PRAGMA table_info(SkillGenCodePrompt)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]:<30} {col[2]}")

print("\n" + "="*60)

# 查询 gh_ApplicationsOfDerivatives 的 SkillGenCodePrompt
cursor.execute("SELECT * FROM SkillGenCodePrompt WHERE skill_id = 'gh_ApplicationsOfDerivatives'")
row = cursor.fetchone()

if row:
    print("\n【SkillGenCodePrompt 中的数据】")
    cols = [desc[0] for desc in cursor.description]
    for col, val in zip(cols, row):
        if val and len(str(val)) > 100:
            print(f"{col}: {str(val)[:200]}...")
        else:
            print(f"{col}: {val}")
else:
    print("\n✗ gh_ApplicationsOfDerivatives 在 SkillGenCodePrompt 中未找到!")
    
    # 看看表里有什么
    print("\n【SkillGenCodePrompt 中存在的技能】")
    cursor.execute("SELECT DISTINCT skill_id FROM SkillGenCodePrompt LIMIT 10")
    for (skill_id,) in cursor.fetchall():
        print(f"  - {skill_id}")

conn.close()
