#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT
from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code, POLYNOMIAL_HELPERS
import sqlite3

skill_id = 'gh_ApplicationsOfDerivatives'
domains = get_required_domains(skill_id)
code = get_domain_helpers_code(domains)

# 新的精簡模板
template = f"""### 🔧 標準函數庫（{', '.join(domains)}）

{code}

⚠️ 規則：
1. 直接調用上述函數，禁止重新定義
2. 你只需實現 `def generate(level=1, **kwargs)`
3. 答案格式：純多項式逗號分隔，例 "6x-5, 6"（禁止包含 f'(x)= 或換行）
"""

# 獲取最新 MASTER_SPEC
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()
master = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
    (skill_id,)
).fetchone()[0]
conn.close()

print("=" * 70)
print("🎯 Prompt 優化結果")
print("=" * 70)

print("\n📊 組件大小對比:")
print(f"  UNIVERSAL_GEN_CODE_PROMPT: {len(UNIVERSAL_GEN_CODE_PROMPT):,} chars (不變)")
print(f"  POLYNOMIAL_HELPERS:        {len(POLYNOMIAL_HELPERS):,} chars (原 3,711)")
print(f"  Domain Injection 模板:      {len(template):,} chars (原 4,456)")
print(f"  MASTER_SPEC:               {len(master):,} chars (不變)")

old_domain = 4456
new_domain = len(template)
reduction = old_domain - new_domain

print(f"\n✅ Domain Injection 減少: {reduction:,} chars ({reduction/old_domain*100:.1f}%)")

# 計算總 prompt 大小
header = "\n\n### MASTER_SPEC:\n"
old_total = len(UNIVERSAL_GEN_CODE_PROMPT) + 4456 + len(header) + len(master)
new_total = len(UNIVERSAL_GEN_CODE_PROMPT) + new_domain + len(header) + len(master)

print(f"\n📉 總 Prompt 大小:")
print(f"  優化前: {old_total:,} chars")
print(f"  優化後: {new_total:,} chars")
print(f"  減少:   {old_total - new_total:,} chars ({(old_total-new_total)/old_total*100:.1f}%)")

print(f"\n🔢 Token 估算 (Qwen2.5-Coder 1:1 比例):")
print(f"  優化前: ~{old_total:,} tokens")
print(f"  優化後: ~{new_total:,} tokens")
print(f"  減少:   ~{old_total - new_total:,} tokens")

print(f"\n🔢 Token 估算 (Gemini 3:1 比例):")
print(f"  優化前: ~{old_total//3:,} tokens")
print(f"  優化後: ~{new_total//3:,} tokens")
print(f"  減少:   ~{(old_total - new_total)//3:,} tokens")

print("\n" + "=" * 70)
print("✅ 優化完成！")
print("=" * 70)
