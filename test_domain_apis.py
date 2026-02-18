"""
測試 domain_libs.py 中的 IntegerOps 和 FractionOps API
"""
import sys
import os
from fractions import Fraction

# Add core path to system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core', 'scaffold'))
from domain_libs import IntegerOps, FractionOps, RadicalOps


def test_integer_ops():
    """測試 IntegerOps API"""
    print("=" * 60)
    print("測試 IntegerOps")
    print("=" * 60)
    
    # Test fmt_num
    print("\n1. 測試 fmt_num（數字格式化）")
    print(f"   fmt_num(5) = {IntegerOps.fmt_num(5)}")
    print(f"   fmt_num(-5) = {IntegerOps.fmt_num(-5)}")
    print(f"   fmt_num(0) = {IntegerOps.fmt_num(0)}")
    assert IntegerOps.fmt_num(5) == "5"
    assert IntegerOps.fmt_num(-5) == "(-5)"
    assert IntegerOps.fmt_num(0) == "0"
    print("   ✅ fmt_num 測試通過")
    
    # Test random_nonzero
    print("\n2. 測試 random_nonzero（產生非零隨機數）")
    for _ in range(5):
        num = IntegerOps.random_nonzero(-10, 10)
        print(f"   產生: {num}")
        assert num != 0
        assert -10 <= num <= 10
    print("   ✅ random_nonzero 測試通過")
    
    # Test safe_eval
    print("\n3. 測試 safe_eval（安全計算表達式）")
    test_cases = [
        ("5 + 3", 8),
        ("10 - 4 * 2", 2),
        ("(5 + 3) * 2", 16),
        ("abs(-5)", 5),
        ("abs(10 - 20)", 10),
    ]
    for expr, expected in test_cases:
        result = IntegerOps.safe_eval(expr)
        print(f"   safe_eval('{expr}') = {result} (期望: {expected})")
        assert result == expected
    print("   ✅ safe_eval 測試通過")


def test_fraction_ops():
    """測試 FractionOps API"""
    print("\n" + "=" * 60)
    print("測試 FractionOps")
    print("=" * 60)
    
    # Test create
    print("\n1. 測試 create（建立分數）")
    f1 = FractionOps.create("1/2")
    f2 = FractionOps.create(0.5)
    f3 = FractionOps.create(Fraction(1, 2))
    f4 = FractionOps.create(3)
    print(f"   create('1/2') = {f1}")
    print(f"   create(0.5) = {f2}")
    print(f"   create(Fraction(1, 2)) = {f3}")
    print(f"   create(3) = {f4}")
    assert f1 == f2 == f3 == Fraction(1, 2)
    assert f4 == Fraction(3, 1)
    print("   ✅ create 測試通過")
    
    # Test to_latex
    print("\n2. 測試 to_latex（轉成 LaTeX）")
    test_cases = [
        (Fraction(1, 2), False, "\\frac{1}{2}"),
        (Fraction(-3, 4), False, "-\\frac{3}{4}"),
        (Fraction(5, 1), False, "5"),
        (Fraction(7, 3), True, "2\\frac{1}{3}"),
        (Fraction(-10, 3), True, "-3\\frac{1}{3}"),
    ]
    for frac, mixed, expected in test_cases:
        result = FractionOps.to_latex(frac, mixed=mixed)
        print(f"   to_latex({frac}, mixed={mixed}) = {result} (期望: {expected})")
        assert result == expected
    print("   ✅ to_latex 測試通過")
    
    # Test arithmetic operations
    print("\n3. 測試四則運算")
    a = Fraction(1, 2)
    b = Fraction(1, 3)
    
    add_result = FractionOps.add(a, b)
    print(f"   add(1/2, 1/3) = {add_result} (期望: 5/6)")
    assert add_result == Fraction(5, 6)
    
    sub_result = FractionOps.sub(a, b)
    print(f"   sub(1/2, 1/3) = {sub_result} (期望: 1/6)")
    assert sub_result == Fraction(1, 6)
    
    mul_result = FractionOps.mul(a, b)
    print(f"   mul(1/2, 1/3) = {mul_result} (期望: 1/6)")
    assert mul_result == Fraction(1, 6)
    
    div_result = FractionOps.div(a, b)
    print(f"   div(1/2, 1/3) = {div_result} (期望: 3/2)")
    assert div_result == Fraction(3, 2)
    
    # Test division by zero
    try:
        FractionOps.div(a, 0)
        assert False, "應該拋出異常"
    except ValueError as e:
        print(f"   div(1/2, 0) 正確拋出異常: {e}")
    
    print("   ✅ 四則運算測試通過")


def test_radical_ops():
    """測試 RadicalOps API（確認之前的實現仍正常）"""
    print("\n" + "=" * 60)
    print("測試 RadicalOps（已有實現）")
    print("=" * 60)
    
    # Test simplify_term
    print("\n1. 測試 simplify_term（簡化根式）")
    test_cases = [
        ((2, 12), (4, 3)),
        ((1, 18), (3, 2)),
        ((3, 8), (6, 2)),
    ]
    for (coeff, rad), (exp_coeff, exp_rad) in test_cases:
        result = RadicalOps.simplify_term(coeff, rad)
        print(f"   simplify_term({coeff}, {rad}) = {result} (期望: ({exp_coeff}, {exp_rad}))")
        assert result == (exp_coeff, exp_rad)
    print("   ✅ simplify_term 測試通過")
    
    # Test format_term
    print("\n2. 測試 format_term（格式化為 LaTeX）")
    test_cases = [
        ((2, 3, True), "2\\sqrt{3}"),
        ((1, 5, True), "\\sqrt{5}"),
        ((-2, 7, True), "-2\\sqrt{7}"),
        ((3, 2, False), "+3\\sqrt{2}"),  # 修正期望值：無空格
    ]
    for (coeff, rad, is_first), expected in test_cases:
        result = RadicalOps.format_term(coeff, rad, is_first)
        print(f"   format_term({coeff}, {rad}, {is_first}) = {result}")
        assert result == expected
    print("   ✅ format_term 測試通過")
    
    print("\n✅ RadicalOps 確認正常工作")


if __name__ == "__main__":
    try:
        test_integer_ops()
        test_fraction_ops()
        test_radical_ops()
        
        print("\n" + "=" * 60)
        print("🎉 所有 API 測試通過！")
        print("=" * 60)
        print("\n✅ IntegerOps 實現完成並測試通過")
        print("✅ FractionOps 實現完成並測試通過")
        print("✅ RadicalOps 確認正常工作")
        print("\n下一步：")
        print("  1. 執行 benchmark.py 測試整合效果")
        print("  2. 檢查 AI 生成的程式碼是否正確使用 API")
        print("  3. 驗證 MCRI 分數是否提升")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
