"""測試修改後的精簡版 BARE_PROMPT_TEMPLATE"""

from core.prompts.prompt_builder import PromptBuilder

# 生成 Ab1 Prompt
prompt = PromptBuilder.build(
    master_spec="",
    ablation_id=1,
    textbook_example="""範例：已知 $f(x) = -3x^{4}-5x^{3}+3x^{2}+x+4$，求 $f'(x)$ 與 $f'''(x)$。
答案：$f'(x) = -12x^{3}-15x^{2}+6x+1$, $f'''(x) = -72x-30$""",
    topic="導數的應用"
)

print("=" * 80)
print("【精簡版 BARE_PROMPT_TEMPLATE (Ab1)】")
print("=" * 80)
print(prompt)
print("=" * 80)
print(f"\nPrompt 統計:")
print(f"  總字數: {len(prompt)} 字元")
print(f"  總行數: {len(prompt.splitlines())} 行")

print("\n【與舊版比較】")
print(f"  舊版 Ab1: ~1,242 字元, 47 行")
print(f"  新版 Ab1: {len(prompt)} 字元, {len(prompt.splitlines())} 行")
print(f"  縮減: {1242 - len(prompt)} 字元 ({((1242 - len(prompt)) / 1242 * 100):.1f}%)")

print("\n【檢查清單】")
checks = {
    "不含 LaTeX 格式要求": "LaTeX 語法格式" not in prompt,
    "不含答案格式範例": "正確範例" not in prompt and "錯誤範例" not in prompt,
    "不含詳細回傳格式代碼": "```python" not in prompt,
    "保留兩個函式要求": "def generate" in prompt and "def check" in prompt,
    "保留基本回傳格式": "'question_text'" in prompt and "'answer'" in prompt,
    "簡化模組建議": "standard library" in prompt,
}

for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")

print("\n✅ 精簡版 BARE_PROMPT 修改完成！")
print("   更接近真實用戶的 Prompt，適合作為 Baseline 對照組")
