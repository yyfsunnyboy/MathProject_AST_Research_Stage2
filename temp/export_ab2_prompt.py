#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成完整的 Ab2/Ab3 Prompt 並輸出到文件"""
import sys
import sqlite3
sys.path.insert(0, '.')

from core.prompts.prompt_builder import PromptBuilder

# 獲取最新的 MASTER_SPEC
skill_id = 'gh_ApplicationsOfDerivatives'
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

master_spec = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
    (skill_id,)
).fetchone()[0]

conn.close()

# 生成 Ab2/Ab3 的完整 prompt
full_prompt = PromptBuilder.build(
    master_spec=master_spec,
    ablation_id=2,  # Ab2 和 Ab3 使用相同的 prompt
    skill_id=skill_id
)

# 輸出到文件
output_file = 'temp/ab2_full_prompt.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_prompt)

print(f"✅ 完整 Prompt 已輸出到: {output_file}")
print(f"📊 統計:")
print(f"   總長度: {len(full_prompt):,} chars")
print(f"   總行數: {len(full_prompt.splitlines()):,} 行")
print(f"   估算 Tokens (Qwen 1:1): ~{len(full_prompt):,} tokens")
print(f"   估算 Tokens (Gemini 3:1): ~{len(full_prompt)//3:,} tokens")
