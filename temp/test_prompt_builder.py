"""測試修改後的 Prompt Builder"""

from core.prompts.prompt_builder import PromptBuilder

# 測試 Ab1
print("=" * 80)
print("【測試 Ab1 Prompt】")
print("=" * 80)
ab1_prompt = PromptBuilder.build(
    master_spec="",
    ablation_id=1,
    textbook_example="範例：已知 f(x) = 3x^2 - 5x + 2，求 f'(x)",
    topic="導數的應用"
)
# 檢查是否包含答案格式說明
if "答案應該直接顯示多項式結果" in ab1_prompt:
    print("✅ Ab1 Prompt 包含導數答案格式說明")
else:
    print("⚠️ Ab1 Prompt 缺少導數答案格式說明")

print("\n" + "=" * 80)
print("【測試 Ab2/Ab3 Prompt (Domain 注入)】")
print("=" * 80)
ab2_prompt = PromptBuilder.build(
    master_spec="[測試用 MASTER_SPEC]",
    ablation_id=2,
    skill_id="gh_ApplicationsOfDerivatives"
)
# 檢查是否包含答案格式說明
if "導數題型答案格式" in ab2_prompt:
    print("✅ Ab2/Ab3 Prompt 包含導數答案格式規範 (Domain 注入)")
else:
    print("⚠️ Ab2/Ab3 Prompt 缺少導數答案格式規範")

if "當題目要求多個導數時" in ab2_prompt:
    print("✅ Ab2/Ab3 Prompt 包含導數答案格式說明 (UNIVERSAL)")
else:
    print("⚠️ Ab2/Ab3 Prompt 缺少導數答案格式說明")

print("\n✅ Prompt 源頭修改完成！")
