"""顯示完整的 BARE_PROMPT_TEMPLATE"""

from core.prompts.prompt_builder import PromptBuilder

# 模擬 Ab1 生成時的 Prompt
prompt = PromptBuilder.build(
    master_spec="",
    ablation_id=1,
    textbook_example="""範例：已知 $f(x) = -3x^{4}-5x^{3}+3x^{2}+x+4$，求 $f'(x)$ 與 $f'''(x)$。
答案：$f'(x) = -12x^{3}-15x^{2}+6x+1$, $f'''(x) = -72x-30$
解法提示：利用冪次法則對每一項分別求導，注意常數項求導後為零...""",
    topic="導數的應用"
)

print("=" * 100)
print("【完整 BARE_PROMPT_TEMPLATE (Ab1)】")
print("=" * 100)
print(prompt)
print("=" * 100)
print(f"\nPrompt 總字數: {len(prompt)} 字元")
print(f"Prompt 總行數: {len(prompt.splitlines())} 行")
