#!/usr/bin/env python3
import sys
sys.path.append(r'e:\python\MathProject_AST_Research')

# 清除缓存
for mod in list(sys.modules.keys()):
    if 'jh_數學1上_FourArithmeticOperationsOfIntegers' in mod:
        del sys.modules[mod]

import skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2 as ab2
import skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 as ab3

print("="*80)
print("AB2 vs AB3 詳細對比（5次執行）")
print("="*80)

for i in range(5):
    print(f"\n【第 {i+1} 次執行】")
    
    try:
        q2 = ab2.generate(level=1)
        print(f"✅ AB2: {q2['question_text'][:60]}...")
        print(f"   答案: {q2['correct_answer']}")
    except Exception as e:
        print(f"❌ AB2 失败: {e}")
    
    try:
        q3 = ab3.generate(level=1)
        print(f"✅ AB3: {q3['question_text'][:60]}...")
        print(f"   答案: {q3['correct_answer']}")
    except Exception as e:
        print(f"❌ AB3 失败: {e}")

print("\n" + "="*80)
