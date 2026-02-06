#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Active Healer 的新修復功能
驗證 Garbage Cleaner 和 Eval Eliminator 是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_generator import refine_ai_code

def test_garbage_cleaner():
    """測試孤立字元清理器"""
    print("=" * 60)
    print("Test 1: Garbage Cleaner (孤立字元清理)")
    print("=" * 60)
    
    buggy_code = """
def to_latex(num):
    if isinstance(num, Fraction):
        is_neg = num < 0
        sign_str = "-" if is_neg else ""
        abs_num = abs(num)
        `1
        # Comment here
        if abs_num.numerator > abs_num.denominator:
            return "result"
    return str(num)
"""
    
    print("原始代碼 (包含 `1):")
    print(buggy_code)
    
    fixed_code, fixes_count = refine_ai_code(buggy_code)
    
    print(f"\n修復後的代碼 (應用了 {fixes_count} 個修復):")
    print(fixed_code)
    
    # 驗證
    if '`1' in fixed_code:
        print("\n❌ FAILED: 孤立字元未被移除")
        return False
    else:
        print("\n✅ PASSED: 孤立字元已成功移除")
        return True

def test_eval_eliminator():
    """測試 safe_eval 替換器"""
    print("\n" + "=" * 60)
    print("Test 2: Eval Eliminator (safe_eval 替換)")
    print("=" * 60)
    
    buggy_code = """
def generate():
    for _safety_loop_var in range(1000):
        n1 = random.randint(-30, 30)
        n2 = random.randint(-30, 30)
        op1 = safe_choice(['+', '-'])
        intermediate_A = safe_eval(f'{n1} {op1} {n2}')
        
        n3 = random.randint(-30, 30)
        op2 = safe_choice(['+', '-', '*'])
        intermediate_B = safe_eval(f'{intermediate_A} {op2} {n3}')
        
        if abs(intermediate_B) < 100:
            break
    return {'question_text': q, 'answer': a}
"""
    
    print("原始代碼 (使用 safe_eval):")
    print(buggy_code)
    
    fixed_code, fixes_count = refine_ai_code(buggy_code)
    
    print(f"\n修復後的代碼 (應用了 {fixes_count} 個修復):")
    print(fixed_code)
    
    # 驗證
    if 'safe_eval(' in fixed_code:
        print("\n❌ FAILED: safe_eval 未被替換")
        return False
    elif '(n1 op1 n2)' in fixed_code and '(intermediate_A op2 n3)' in fixed_code:
        print("\n✅ PASSED: safe_eval 已成功替換為直接計算")
        return True
    else:
        print("\n⚠️  WARNING: safe_eval 被替換，但格式可能不正確")
        return False

def test_combined():
    """測試組合修復"""
    print("\n" + "=" * 60)
    print("Test 3: Combined Fixes (組合修復)")
    print("=" * 60)
    
    buggy_code = """
def generate():
    op_latex = {'+': '+', '-': '-'}
    for _safety_loop_var in range(1000):
        n1 = random.randint(-30, 30)
        `1
        n2 = random.randint(-30, 30)
        op1 = safe_choice(['+', '-'])
        result = safe_eval(f'{n1} {op1} {n2}')
        
        if abs(result) < 100:
            break
    
    q = f'{n1} {op_latex[op1]} {n2}'
    a = str(result)
    return {'question_text': q, 'answer': a}
"""
    
    print("原始代碼 (包含 `1 和 safe_eval):")
    print(buggy_code)
    
    fixed_code, fixes_count = refine_ai_code(buggy_code)
    
    print(f"\n修復後的代碼 (應用了 {fixes_count} 個修復):")
    print(fixed_code)
    
    # 驗證
    garbage_removed = '`1' not in fixed_code
    eval_replaced = 'safe_eval(' not in fixed_code
    
    if garbage_removed and eval_replaced:
        print("\n✅ PASSED: 所有修復都成功應用")
        return True
    else:
        print(f"\n❌ FAILED: garbage_removed={garbage_removed}, eval_replaced={eval_replaced}")
        return False

if __name__ == '__main__':
    results = []
    
    print("\n🔧 Active Healer 新功能測試")
    print("測試兩個新增的修復邏輯:")
    print("1. Garbage Cleaner - 移除孤立字元 (如 `1)")
    print("2. Eval Eliminator - 替換 safe_eval 為直接計算")
    print()
    
    results.append(test_garbage_cleaner())
    results.append(test_eval_eliminator())
    results.append(test_combined())
    
    print("\n" + "=" * 60)
    print(f"測試結果: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✅ 所有測試通過！Active Healer 新功能正常運作。")
        sys.exit(0)
    else:
        print("❌ 部分測試失敗，請檢查修復邏輯。")
        sys.exit(1)
