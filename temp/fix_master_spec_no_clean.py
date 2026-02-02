#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复 MASTER_SPEC - 移除 clean_latex_output 调用"""
import sqlite3

skill_id = 'gh_ApplicationsOfDerivatives'

# 读取当前的 MASTER_SPEC
conn = sqlite3.connect('instance/kumon_math.db')
cur = conn.cursor()

current_spec = cur.execute(
    'SELECT prompt_content FROM skill_gencode_prompt WHERE id=202'
).fetchone()[0]

# 替换所有 clean_latex_output 调用为不调用
updated_spec = current_spec.replace(
    '4. 最後呼叫 `q = clean_latex_output(q)`。',
    '4. ⚠️ **不要**呼叫 `clean_latex_output(q)`（已手動添加 $ 符號）'
)

updated_spec = updated_spec.replace(
    '- 使用 clean_latex_output() 自動包裝**最後一次**（僅呼叫一次）',
    '- ⚠️ **不要使用** clean_latex_output()（已使用 Domain 函數，已手動添加 $ 符號）'
)

# 插入新的修正版本
cur.execute('''
    INSERT INTO skill_gencode_prompt (skill_id, prompt_content, created_at)
    VALUES (?, ?, datetime('now'))
''', (skill_id, updated_spec))

new_id = cur.lastrowid
conn.commit()

print(f"✅ 修正後的 MASTER_SPEC 已插入")
print(f"   新 ID: {new_id}")
print(f"   舊 ID: 202")
print(f"   修改: 移除 clean_latex_output() 調用指示")

# 验证变更
changes = []
if 'clean_latex_output(q)' in current_spec and 'clean_latex_output(q)' not in updated_spec:
    changes.append("✅ 移除了 clean_latex_output 调用")
if '不要呼叫 clean_latex_output' in updated_spec:
    changes.append("✅ 添加了禁止调用的警告")

print(f"\n变更内容:")
for c in changes:
    print(f"  {c}")

conn.close()
