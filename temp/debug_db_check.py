#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to check database content"""

import sqlite3
import json

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查询 gh_ApplicationsOfDerivatives 的信息
cursor.execute("SELECT * FROM skills_info WHERE skill_id = 'gh_ApplicationsOfDerivatives'")
row = cursor.fetchone()

if row:
    cols = [desc[0] for desc in cursor.description]
    skill_data = dict(zip(cols, row))
    
    print("【技能数据库信息】")
    print(f"Skill ID: {skill_data.get('skill_id')}")
    print(f"Name: {skill_data.get('name')}")
    print(f"\n【Master Spec】")
    master_spec = skill_data.get('master_spec')
    if master_spec:
        try:
            spec = json.loads(master_spec)
            print(json.dumps(spec, ensure_ascii=False, indent=2)[:1000])
        except:
            print(master_spec[:500])
    else:
        print("(空)")
        
    print(f"\n【Coding Prompt】")
    coding_prompt = skill_data.get('coding_prompt')
    if coding_prompt:
        print(coding_prompt[:500])
    else:
        print("(空) - 这就是问题!")
else:
    print("技能未找到")

conn.close()
