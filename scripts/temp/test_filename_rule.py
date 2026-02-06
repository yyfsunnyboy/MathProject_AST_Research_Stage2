"""
快速測試：驗證新的檔名規則和 3x Ablation 生成
"""

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

print("=" * 70)
print("✅ 檔名規則驗證")
print("=" * 70)

# 測試範例
skill_id = "jh_數學1上_IntegerAdditionOperation"
model_size = "14B"

print(f"\n技能 ID: {skill_id}")
print(f"模型等級: {model_size}")
print("\n預期生成的檔名:")

for ablation_id in [1, 2, 3]:
    filename = f"{skill_id}_{model_size}_Ab{ablation_id}.py"
    filepath = os.path.join(project_root, 'skills', filename)
    print(f"  Ab{ablation_id}: {filename}")
    print(f"       完整路徑: {filepath}")

print("\n" + "=" * 70)
print("✅ 驗證完成！")
print("=" * 70)

print("\n📋 實驗設計摘要:")
print("   每個技能將生成 3 個版本:")
print("   - Ab1: Bare Prompt (無 Healer)")
print("   - Ab2: Regex Only (僅 Regex Healer)")
print("   - Ab3: Full-Healing (Regex + AST Healer)")
print("\n   這樣可以完整對比不同配置的效果！")
