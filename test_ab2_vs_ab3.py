#!/usr/bin/env python3
import sys
sys.path.append(r'e:\python\MathProject_AST_Research')

print("="*70)
print("AB2 vs AB3 对比诊断")
print("="*70)

# Test AB2
print("\n[AB2 Test]")
try:
    import skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2 as ab2
    print("✅ AB2 导入成功")
    
    result = ab2.generate(level=1)
    print(f"✅ AB2 generate() 执行成功")
    print(f"   问题文本长度: {len(result['question_text'])}")
    print(f"   答案: {result['correct_answer']}")
    
except Exception as e:
    print(f"❌ AB2 失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test AB3
print("\n[AB3 Test]")
try:
    # 需要重新导入，避免缓存
    import importlib
    if 'skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3' in sys.modules:
        del sys.modules['skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3']
    
    import skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 as ab3
    print("✅ AB3 导入成功")
    
    result = ab3.generate(level=1)
    print(f"✅ AB3 generate() 执行成功")
    print(f"   问题文本长度: {len(result['question_text'])}")
    print(f"   答案: {result['correct_answer']}")
    
except Exception as e:
    print(f"❌ AB3 失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
