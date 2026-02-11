"""
Ab3 Execution Test - 验证 generate() 是否能正确运行
"""

import sys
sys.path.insert(0, r'e:\\python\\MathProject_AST_Research')

# 导入 Ab3 模块
from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 import generate, check

print("="*80)
print("AB3 EXECUTION TEST")
print("="*80)

# 测试 1: 调用 generate()
print("\n[TEST 1] 调用 generate() 函数...")
try:
    result = generate(level=1)
    print("✅ PASS: generate() 成功执行")
    print(f"  返回类型: {type(result)}")
    print(f"  返回键: {list(result.keys())}")
    print(f"  题目: {result.get('question_text', 'N/A')[:60]}...")
    print(f"  正确答案: {result.get('correct_answer', 'N/A')}")
except Exception as e:
    print(f"❌ FAIL: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 2: 多次调用确保稳定性
print("\n[TEST 2] 多次调用检查稳定性...")
try:
    for i in range(5):
        result = generate(level=1)
        assert 'question_text' in result
        assert 'correct_answer' in result
        print(f"  ✅ 第 {i+1} 次调用成功")
    print("✅ PASS: 5 次调用全部成功")
except Exception as e:
    print(f"❌ FAIL: {type(e).__name__}: {e}")
    sys.exit(1)

# 测试 3: 验证返回的答案格式
print("\n[TEST 3] 验证答案格式...")
try:
    result = generate(level=1)
    answer = result.get('correct_answer')
    
    # 答案应该是数字或可转换为数字
    try:
        val = int(answer)
        print(f"✅ PASS: 答案是有效的整数: {val}")
    except ValueError:
        try:
            val = float(answer)
            print(f"✅ PASS: 答案是有效的浮点数: {val}")
        except ValueError:
            print(f"⚠️ WARNING: 答案格式不是标准数字: {answer}")
except Exception as e:
    print(f"❌ FAIL: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ AB3 所有测试通过！")
print("="*80)
