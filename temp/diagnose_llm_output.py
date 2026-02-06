# -*- coding: utf-8 -*-
"""诊断 LLM 输出问题"""

# 读取原始 LLM 输出
with open(r'E:\Python\MathProject_AST_Research\skills_shadow\jh_數學1上_IntegerAdditionOperation_FAILED_20260128_130257.raw.txt', 'r', encoding='utf-8') as f:
    raw_output = f.read()

print("="*70)
print("原始 LLM 输出分析")
print("="*70)
print(f"\n总长度: {len(raw_output)} 字符")
print(f"是否包含 'def generate': {' def generate' in raw_output}")
print(f"是否包含 '```python': {'```python' in raw_output}")
print(f"是否包含 '```': {'```' in raw_output}")

print("\n前 500 字符:")
print(raw_output[:500])

print("\n后 500 字符:")
print(raw_output[-500:])
