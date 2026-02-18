"""
驗證 code_generator.py 能否正確注入 IntegerOps 和 FractionOps API
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from code_generator import _inject_domain_libs


def test_injection():
    """測試 API 注入功能"""
    print("=" * 70)
    print("測試 domain_libs API 注入")
    print("=" * 70)
    
    # Test case 1: Code with no imports (should inject all APIs)
    print("\n1. 測試注入到空代碼")
    code_no_import = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = IntegerOps.random_nonzero(-10, 10)
    return {'question_text': f'計算 {IntegerOps.fmt_num(a)}', 'answer': '', 'correct_answer': str(a), 'mode': 1}
"""
    result_code, injected = _inject_domain_libs(code_no_import)
    print(f"   注入的類別: {injected}")
    print(f"   代碼包含 IntegerOps 定義: {'class IntegerOps:' in result_code}")
    assert 'class IntegerOps:' in result_code
    assert 'IntegerOps' in injected
    print("   ✅ IntegerOps 注入成功")
    
    # Test case 2: Code using FractionOps
    print("\n2. 測試 FractionOps 注入")
    code_fraction = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    f = FractionOps.create('1/2')
    latex = FractionOps.to_latex(f)
    return {'question_text': f'計算 $$ {latex} $$', 'answer': '', 'correct_answer': '1/2', 'mode': 1}
"""
    result_code, injected = _inject_domain_libs(code_fraction)
    print(f"   注入的類別: {injected}")
    print(f"   代碼包含 FractionOps 定義: {'class FractionOps:' in result_code}")
    assert 'class FractionOps:' in result_code
    assert 'FractionOps' in injected
    print("   ✅ FractionOps 注入成功")
    
    # Test case 3: Code using RadicalOps
    print("\n3. 測試 RadicalOps 注入")
    code_radical = """
import random

def generate(level=1, **kwargs):
    coeff, rad = RadicalOps.simplify_term(2, 12)
    latex = RadicalOps.format_term(coeff, rad)
    return {'question_text': f'簡化 $$ {latex} $$', 'answer': '', 'correct_answer': latex, 'mode': 1}
"""
    result_code, injected = _inject_domain_libs(code_radical)
    print(f"   注入的類別: {injected}")
    print(f"   代碼包含 RadicalOps 定義: {'class RadicalOps:' in result_code}")
    assert 'class RadicalOps:' in result_code
    assert 'RadicalOps' in injected
    print("   ✅ RadicalOps 注入成功")
    
    # Test case 4: Code using multiple APIs
    print("\n4. 測試多個 API 同時注入")
    code_multi = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = IntegerOps.random_nonzero(-10, 10)
    f = FractionOps.create('1/2')
    coeff, rad = RadicalOps.simplify_term(2, 12)
    return {'question_text': 'Mixed', 'answer': '', 'correct_answer': '0', 'mode': 1}
"""
    result_code, injected = _inject_domain_libs(code_multi)
    print(f"   注入的類別: {injected}")
    assert 'IntegerOps' in injected
    assert 'FractionOps' in injected
    assert 'RadicalOps' in injected
    assert 'class IntegerOps:' in result_code
    assert 'class FractionOps:' in result_code
    assert 'class RadicalOps:' in result_code
    print("   ✅ 多個 API 同時注入成功")
    
    # Test case 5: Verify executable code
    print("\n5. 測試注入後的代碼可執行")
    test_code = """
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    a = IntegerOps.random_nonzero(-5, 5)
    return {
        'question_text': f'計算 {IntegerOps.fmt_num(a)}',
        'answer': '',
        'correct_answer': str(a),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {'correct': str(user_answer) == str(correct_answer), 'result': '正確'}
"""
    result_code, injected = _inject_domain_libs(test_code)
    
    # Try to execute the injected code
    exec_globals = {}
    try:
        exec(result_code, exec_globals)
        result = exec_globals['generate'](level=1)
        print(f"   生成題目: {result['question_text']}")
        print(f"   正確答案: {result['correct_answer']}")
        assert 'question_text' in result
        assert 'correct_answer' in result
        print("   ✅ 注入後的代碼成功執行")
    except Exception as e:
        print(f"   ❌ 執行失敗: {e}")
        raise


if __name__ == "__main__":
    try:
        test_injection()
        
        print("\n" + "=" * 70)
        print("🎉 所有注入測試通過！")
        print("=" * 70)
        print("\n✅ IntegerOps 可正確注入")
        print("✅ FractionOps 可正確注入")
        print("✅ RadicalOps 可正確注入")
        print("✅ 多個 API 可同時注入")
        print("✅ 注入後的代碼可正常執行")
        print("\n系統已準備好進行 benchmark 測試！")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
