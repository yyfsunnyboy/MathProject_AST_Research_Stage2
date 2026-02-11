# -*- coding: utf-8 -*-
"""測試 AB2 LaTeX 修復"""

import sys
sys.path.insert(0, r'e:\python\MathProject_AST_Research')

# 重新加載模塊
if 'jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2' in sys.modules:
    del sys.modules['jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2']

from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2 import generate

print("=" * 70)
print("AB2 LaTeX 修復驗證")
print("=" * 70)

# 測試多次
for i in range(3):
    result = generate()
    question = result['question_text']
    answer = result['answer']
    
    print(f"\n【題目 {i+1}】")
    print(f"  問題: {question}")
    print(f"  答案: {answer}")
    
    # 驗證括號成對
    left_bracket = question.count(r'\left[')
    right_bracket = question.count(r'\right]')
    left_pipe = question.count(r'\left|')
    right_pipe = question.count(r'\right|')
    
    if left_bracket == right_bracket and left_pipe == right_pipe:
        print(f"  ✅ LaTeX 括號配對正確")
    else:
        print(f"  ❌ LaTeX 括號配對有誤 ([ {left_bracket}~{right_bracket}, | {left_pipe}~{right_pipe})")
    
    # 檢查 $ 符號成對
    dollar_count = question.count('$')
    if dollar_count % 2 == 0:
        print(f"  ✅ $ 符號成對正確 ({dollar_count} 個)")
    else:
        print(f"  ❌ $ 符號不成對 ({dollar_count} 個)")

print("\n" + "=" * 70)
print("驗證完成")
print("=" * 70)
