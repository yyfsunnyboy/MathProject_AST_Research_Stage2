#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import sqlite3

sys.path.insert(0, '.')

conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

rows = cur.execute('''
    SELECT id, created_at, LENGTH(prompt_content) 
    FROM skill_gencode_prompt 
    WHERE skill_id=? 
    ORDER BY id
''', ('gh_ApplicationsOfDerivatives',)).fetchall()

print("ID  建立時間              長度")
print("="*40)
for r in rows:
    id_num = r[0]
    created = r[1][:19] if r[1] else "N/A"
    length = r[2]
    print(f"{id_num:3} {created:19} {length:6,} chars")

conn.close()

# 檢查 V47.5 時期的 prompt 組成
print("\n" + "="*40)
print("檢查 Gemini V47.5 時期 (5454 tokens) 的 prompt")
print("="*40)

from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT

print(f"UNIVERSAL_GEN_CODE_PROMPT: {len(UNIVERSAL_GEN_CODE_PROMPT):,} chars")
print(f"估算 tokens (÷3): {len(UNIVERSAL_GEN_CODE_PROMPT)//3:,}")

# 檢查是否有 Domain Injection
try:
    from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
    domains = get_required_domains('gh_ApplicationsOfDerivatives')
    if domains:
        code = get_domain_helpers_code(domains)
        print(f"\n🔧 Domain Injection 存在:")
        print(f"   Domains: {domains}")
        print(f"   Code length: {len(code):,} chars")
        print(f"   估算 tokens (÷3): {len(code)//3:,}")
    else:
        print("\n❌ 沒有 Domain Injection")
except:
    print("\n❌ Domain 功能不存在")

# 計算舊版 prompt 總長度
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
old_master = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE id=169'
).fetchone()

if old_master:
    print(f"\nID 169 (舊版): {len(old_master[0]):,} chars")
    
    # 假設舊版沒有 Domain Injection
    old_total_no_domain = len(UNIVERSAL_GEN_CODE_PROMPT) + len(old_master[0]) + 20
    print(f"舊版估算 (UNIVERSAL + MASTER): {old_total_no_domain:,} chars ≈ {old_total_no_domain//3:,} tokens")
    
conn.close()
