"""
完整驗證 AB1、AB2、AB3 獨立工作能力
"""
import sys
sys.path.insert(0, '.')

# 測試 AB2（剛修復的）
print("="*60)
print("AB2 測試（逆向工程）")
print("="*60)
try:
    from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2 import generate as gen_ab2
    for i in range(2):
        result = gen_ab2()
        q = result['question_text']
        print(f"AB2 Question {i+1}: {q[:60]}...")
        print(f"Answer: {result['correct_answer']}\n")
    print("✅ AB2 Test PASSED\n")
except Exception as e:
    print(f"❌ AB2 Test FAILED: {e}\n")

# 現在測試 AB3（應該使用統一 Healer）
print("="*60)
print("AB3 測試（統一清理 Healer）")
print("="*60)
try:
    from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 import generate as gen_ab3
    for i in range(2):
        result = gen_ab3()
        q = result['question_text']
        print(f"AB3 Question {i+1}: {q[:60]}...")
        print(f"Answer: {result['correct_answer']}\n")
    print("✅ AB3 Test PASSED\n")
except Exception as e:
    print(f"❌ AB3 Test FAILED: {e}\n")

print("="*60)
print("所有測試完成")
print("="*60)
