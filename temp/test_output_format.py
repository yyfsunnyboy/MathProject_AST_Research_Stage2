# -*- coding: utf-8 -*-
import sys
import importlib.util

# 測試生成的題目格式
spec = importlib.util.spec_from_file_location('test', r'E:\Python\MathProject_AST_Research\skills\jh_數學1上_IntegerAdditionOperation.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("=" * 70)
print("驗證題目格式 - IntegerAdditionOperation")
print("=" * 70)

for i in range(3):
    item = mod.generate()
    print(f"\n範例 {i+1}:")
    print(f"  題目: {item['question_text']}")
    print(f"  答案: {item['answer']}")
    
    # 驗證格式
    q = item['question_text']
    a = item['answer']
    
    # 檢查題目是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in q)
    # 檢查題目是否包含 $
    has_dollar = '$' in q
    # 檢查答案是否純數字或LaTeX
    answer_ok = a.lstrip('-').replace('.', '').isdigit() or '\\' in a
    
    print(f"  ✓ 包含中文: {'✅' if has_chinese else '❌'}")
    print(f"  ✓ 包含數學式: {'✅' if has_dollar else '❌'}")  
    print(f"  ✓ 答案格式: {'✅' if answer_ok else '❌'}")

print("\n" + "=" * 70)
print("測試其他技能")
print("=" * 70)

skills = [
    'jh_數學1上_IntegerMultiplication',
    'jh_數學1上_IntegerDivision',
    'jh_數學1上_FourArithmeticOperationsOfIntegers'
]

for skill_id in skills:
    spec = importlib.util.spec_from_file_location('test', f'E:\\Python\\MathProject_AST_Research\\skills\\{skill_id}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    item = mod.generate()
    print(f"\n{skill_id}:")
    print(f"  題目: {item['question_text'][:80]}...")
    print(f"  答案: {item['answer']}")
