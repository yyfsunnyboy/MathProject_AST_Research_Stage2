"""
測試 Ab2 實際收到的 Prompt 內容
"""
import sys
sys.path.insert(0, 'E:\\Python\\MathProject_AST_Research')

from core.prompts.prompt_builder import PromptBuilder

# 模擬 Ab2 的 prompt 構建
skill_id = "gh_ApplicationsOfDerivatives"
ablation_id = 2
master_spec = """[模擬的 MASTER_SPEC 內容]
生成導數題目...
"""

prompt = PromptBuilder.build(
    master_spec,
    ablation_id=ablation_id,
    skill_id=skill_id
)

print("=" * 80)
print("Ab2 實際收到的 Prompt 長度:", len(prompt))
print("=" * 80)

# 檢查是否包含關鍵警告
keywords_to_check = [
    ("V4.2.2 CRITICAL", "關鍵版本標記"),
    ("絕對禁止", "禁止警告"),
    ("clean_latex_output()", "函數名稱"),
    ("Ab2 爆炸的根本原因", "明確後果說明"),
    ("ApplicationsOfDerivatives 實戰案例", "具體範例"),
    ("derivative_symbols_latex", "變數名範例"),
]

print("\n檢查關鍵警告是否存在於 Prompt 中:\n")
for keyword, description in keywords_to_check:
    exists = keyword in prompt
    status = "✅ 存在" if exists else "❌ 缺失"
    print(f"{status} - {description}: '{keyword}'")

# 顯示包含 clean_latex_output 的部分
print("\n" + "=" * 80)
print("包含 'clean_latex_output' 的段落:")
print("=" * 80)

lines = prompt.split('\n')
for i, line in enumerate(lines):
    if 'clean_latex_output' in line.lower():
        # 顯示前後各2行
        start = max(0, i - 2)
        end = min(len(lines), i + 3)
        print(f"\n[Line {i}]")
        for j in range(start, end):
            prefix = ">>> " if j == i else "    "
            print(f"{prefix}{lines[j]}")

# 顯示 Domain 函數相關的警告
print("\n" + "=" * 80)
print("包含 'Domain 函數' 的段落:")
print("=" * 80)

for i, line in enumerate(lines):
    if 'Domain 函數' in line or 'domain 函數' in line:
        start = max(0, i - 1)
        end = min(len(lines), i + 10)
        print(f"\n[Line {i}]")
        for j in range(start, end):
            prefix = ">>> " if j == i else "    "
            print(f"{prefix}{lines[j]}")
