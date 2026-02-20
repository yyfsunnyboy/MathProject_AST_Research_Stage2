# -*- coding: utf-8 -*-
from core.engine.classifier import SkillClassifier

def test_classifier():
    classifier = SkillClassifier()
    test_cases = [
        ("計算根號 12 乘以根號 3。", "jh_數學2上_FourOperationsOfRadicals"),
        ("若 (-2x^2 + 5x - 1) + P = 3x^2 - 2x + 4，求 P。", "jh_數學2上_FourArithmeticOperationsOfPolynomial"),
        ("計算 (-15) + (-20) - 5 的值。", "jh_數學1上_FourArithmeticOperationsOfIntegers"),
        ("計算 1/2 + 3/4 - 1/8。", "jh_數學1上_FourArithmeticOperationsOfNumbers"),
        ("find the derivative of f(x) = x^2 + 3x", "gh_ApplicationsOfDerivatives"),
        ("今天天氣很好", "Unknown")
    ]
    
    print(f"--- 綜合分類測試 (共 {len(test_cases)} 題) ---")
    passed = 0
    for q, expected in test_cases:
        result = classifier.classify(input_text=q)
        is_pass = (result == expected)
        status = "✅ PASS" if is_pass else f"❌ FAIL (Got: {result})"
        print(f"Q: {q}")
        print(f"   Expected: {expected}")
        print(f"   Result:   {status}")
        if is_pass: passed += 1
    
    print(f"\n測試結論: {passed}/{len(test_cases)} 通過")

if __name__ == "__main__":
    test_classifier()
