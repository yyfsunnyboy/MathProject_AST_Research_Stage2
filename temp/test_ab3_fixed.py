"""測試修復後的 Ab3 skill"""

import sys
sys.path.insert(0, r'E:\Python\MathProject_AST_Research\skills')

from gh_ApplicationsOfDerivatives_Cloud_Ab3 import generate, check

print("測試 Ab3 (Full Healing) 的 generate() 和 check() 函數")
print("=" * 60)

# 測試生成函數
try:
    result = generate(level=1)
    print("✅ 生成成功")
    print(f"題目: {result['question_text']}")
    print(f"答案: {result['correct_answer']}")
    print()
    
    # 測試檢查函數
    check_result = check(result['correct_answer'], result['correct_answer'])
    print(f"✅ 檢查函數運作正常: {check_result}")
    
except Exception as e:
    print(f"❌ 失敗: {e}")
    import traceback
    traceback.print_exc()
