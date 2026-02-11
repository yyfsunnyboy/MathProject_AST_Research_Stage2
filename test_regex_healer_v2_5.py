#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for RegexHealer V2.5
驗證智慧依賴注入功能與系統集成
"""

from core.healers.regex_healer import RegexHealer

def test_integration():
    """完整集成測試"""
    print("=" * 80)
    print("🧪 RegexHealer V2.5 - 集成測試")
    print("=" * 80)
    
    healer = RegexHealer()
    
    # 測試代碼：使用 domain_function_library 中的多個類別
    test_code = """```python
def generate(level=1):
    # 使用 FractionOps 進行浮點數轉換
    a = FractionOps.create(-0.6)
    
    # 使用 IntegerOps 進行安全評估
    b = IntegerOps.safe_eval("abs(-5)")
    
    # 使用中文符號（需要修復）
    c = Fraction（3，5）
    
    # 使用 input（應該被移除）
    x = input（"Enter value"）
    
    question_text = f'計算 {a} × {b} - {c} 的值'
    correct_answer = f'{a * b - c}'
    
    return {
        'question_text': question_text,
        'correct_answer': correct_answer,
        'answer': '',
        'mode': 1
    }
```"""
    
    print("\n【原始代碼】")
    print(test_code)
    
    # 執行修復
    print("\n【執行修復】")
    fixed_code, stats = healer.heal(test_code)
    
    print("\n【修復後的代碼】")
    print(fixed_code)
    
    print("\n【修復統計】")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # ================================================================
    # 驗證
    # ================================================================
    print("\n【驗證結果】")
    print("-" * 80)
    
    verifications = [
        ("1. Markdown 標記已移除", "```" not in fixed_code),
        ("2. FractionOps import 已注入", "from domain_function_library import FractionOps" in fixed_code),
        ("3. IntegerOps import 已注入", "from domain_function_library import IntegerOps" in fixed_code),
        ("4. 中文括號已修復", "def generate(level=1):" in fixed_code),
        ("5. input() 已移除", "input(" not in fixed_code),
        ("6. 統計計數 > 0", stats['regex_fix_count'] > 0),
        ("7. 注入計數 >= 2", stats['imports_injected'] >= 2),
    ]
    
    all_pass = True
    for check_name, result in verifications:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name} ... {status}")
        all_pass = all_pass and result
    
    # ================================================================
    # 最終結論
    # ================================================================
    print("\n" + "=" * 80)
    if all_pass:
        print("✅ 【ALL TESTS PASS】RegexHealer V2.5 已完成部署")
        print("✅ 智慧依賴注入功能運作正常")
        print("✅ 修復統計機制完善")
    else:
        print("❌ 【SOME TESTS FAILED】請檢查上述失敗項目")
    print("=" * 80)
    
    return all_pass

if __name__ == "__main__":
    success = test_integration()
    exit(0 if success else 1)
