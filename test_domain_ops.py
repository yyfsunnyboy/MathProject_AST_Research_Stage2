# -*- coding: utf-8 -*-
import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.insert(0, basedir)

from core.prompts.domain_function_library import FractionOps, PolynomialOps, RadicalOps, IntegerOps

def test_fraction_ops():
    f1 = FractionOps.create(1, 2)
    f2 = FractionOps.create(1, 3)
    res = FractionOps.add(f1, f2)
    assert FractionOps.format_plain(res) == "5/6"
    assert FractionOps.to_latex(res) == r"\frac{5}{6}"
    print("✅ FractionOps 驗證通過")

def test_poly_ops():
    # p1 = 2x^2 + 3x + 1
    # p2 = x^2 - x
    res = PolynomialOps.add([2, 3, 1], [1, -1, 0])
    # Expected: 3x^2 + 2x + 1
    assert res == [3, 2, 1]
    latex = PolynomialOps.format_latex(res)
    assert latex == "3x^{2} + 2x + 1"
    print("✅ PolynomialOps (PolyOps) 驗證通過")

def test_radical_ops():
    res = RadicalOps.create(8)
    assert res == "2√2"
    term = RadicalOps.format_term(3, 8, True)
    # 3 * 2√2 = 6√2
    assert term == "6\\sqrt{2}"
    print("✅ RadicalOps 驗證通過")

def test_integer_ops():
    assert IntegerOps.fmt_num(-5) == "(-5)"
    assert IntegerOps.fmt_num(5) == "5"
    print("✅ IntegerOps 驗證通過")

if __name__ == "__main__":
    print("=== [單元測試] Python 領域工具庫 (domain_function_library.py) ===")
    test_fraction_ops()
    test_poly_ops()
    test_radical_ops()
    test_integer_ops()
    print("✅ 所有 Ops 工具測試完成且功能正常！")
