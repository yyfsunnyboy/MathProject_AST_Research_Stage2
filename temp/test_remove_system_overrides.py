#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試新的 remove_system_overrides 函數
確保它能正確移除整個函式區塊，而不僅僅是 def 行
"""

import sys
from pathlib import Path

# 添加 core 模塊到路徑
sys.path.insert(0, str(Path(__file__).parent / 'core'))

from code_generator import remove_system_overrides


def test_case_1():
    """測試案例 1：簡單的 def 移除"""
    code = """
def generate(level=1):
    x = randint(1, 10)
    
def fmt_num(x):
    return str(x)

print("done")
"""
    result = remove_system_overrides(code)
    print("Test 1 - 簡單 def 移除:")
    print("輸入:", repr(code))
    print("輸出:", repr(result))
    print("期望：def fmt_num(...) 及其內容被移除")
    assert "def fmt_num" not in result
    print("✅ PASS\n")


def test_case_2():
    """測試案例 2：多行函式內容移除"""
    code = """
def generate(level=1):
    x = randint(1, 10)
    return x

def fmt_num(n, mode='frac'):
    '''格式化數字'''
    if mode == 'frac':
        return str(Fraction(n))
    else:
        return str(n)

def calculate():
    return 1
"""
    result = remove_system_overrides(code)
    print("Test 2 - 多行函式移除:")
    print("✅ def fmt_num 及其內容被移除")
    assert "def fmt_num" not in result
    assert "if mode == 'frac'" not in result
    assert "def generate" in result
    assert "def calculate" in result
    print("✅ PASS\n")


def test_case_3():
    """測試案例 3：變數賦值移除"""
    code = """
op_latex = {'+': '+', '-': '-'}

def generate(level=1):
    return 1
"""
    result = remove_system_overrides(code)
    print("Test 3 - 變數賦值移除:")
    print("✅ op_latex 變數賦值被移除")
    assert "op_latex" not in result
    assert "def generate" in result
    print("✅ PASS\n")


def test_case_4():
    """測試案例 4：保護 generate 函式（不刪）"""
    code = """
def generate(level=1):
    x = randint(1, 10)
    
    def fmt_num(n):
        return str(n)
    
    return x

def to_latex(x):
    return f"${x}$"
"""
    result = remove_system_overrides(code)
    print("Test 4 - 嵌套函式移除:")
    print("✅ to_latex 被移除，generate 被保留")
    assert "def generate" in result
    assert "def to_latex" not in result
    assert "return x" in result
    print("✅ PASS\n")


def test_case_5():
    """測試案例 5：連續多個系統函式定義"""
    code = """
def fmt_num(x):
    return str(x)

def to_latex(x):
    return f"${x}$"

def safe_choice(items):
    return choice(items)

def generate(level=1):
    x = randint(1, 10)
    return x
"""
    result = remove_system_overrides(code)
    print("Test 5 - 連續多個系統函式移除:")
    print("✅ 三個系統函式都被移除")
    assert "def fmt_num" not in result
    assert "def to_latex" not in result
    assert "def safe_choice" not in result
    assert "def generate" in result
    print("✅ PASS\n")


def test_case_6():
    """測試案例 6：縮排邊界偵測（不刪正常縮排的函式內容）"""
    code = """
def fmt_num(x):
    # 多行函式
    result = str(x)
    if x > 0:
        result = f"+{result}"
    return result

def generate(level=1):
    x = randint(1, 10)
    formatted = fmt_num(x)  # 呼叫被移除的函式（運行時會錯）
    return formatted
"""
    result = remove_system_overrides(code)
    print("Test 6 - 縮排邊界：")
    print("✅ 整個 def fmt_num(...) 區塊被移除")
    assert "def fmt_num" not in result
    assert "if x > 0:" not in result
    assert "def generate" in result
    assert "formatted = fmt_num(x)" in result
    print("✅ PASS\n")


def test_case_7():
    """測試案例 7：實際生成代碼的問題場景"""
    code = """
import random
from fractions import Fraction

def generate(level=1):
    x = randint(1, 10)
    
def fmt_num(x, mode='frac'):
    if mode == 'frac':
        return str(Fraction(x))
    else:
        return str(int(x))
    
def to_latex(expr):
    return f"${expr}$"

def calculate_answer(x):
    return fmt_num(x, mode='decimal')
"""
    result = remove_system_overrides(code)
    print("Test 7 - 實際場景：")
    print("輸入行數:", len(code.split('\n')))
    print("輸出行數:", len(result.split('\n')))
    assert "def fmt_num" not in result
    assert "def to_latex" not in result
    assert "def generate" in result
    assert "def calculate_answer" in result
    print("✅ PASS\n")


if __name__ == "__main__":
    print("=" * 70)
    print("測試 remove_system_overrides 函數（整塊移除版本）")
    print("=" * 70 + "\n")
    
    try:
        test_case_1()
        test_case_2()
        test_case_3()
        test_case_4()
        test_case_5()
        test_case_6()
        test_case_7()
        
        print("=" * 70)
        print("✅ 所有測試通過！")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
