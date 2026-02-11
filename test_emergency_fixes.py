"""
Emergency Fix Verification Test
驗證兩個紧急修復是否有效：
1. 禁止重複 Import (本地定義檢查)
2. 移除末尾垃圾 (remove_trailing_artifacts)
"""

import sys
import re
sys.path.insert(0, r'e:\\python\\MathProject_AST_Research')

from core.healers.regex_healer import RegexHealer

def test_no_duplicate_import():
    """Test: 本地已定義的 class 不會被重複 import"""
    print("\n" + "="*80)
    print("TEST 1: 禁止重複 Import (本地定義檢查)")
    print("="*80)
    
    healer = RegexHealer()
    
    # 模擬 Ab3 的情況: 已經有本地 IntegerOps 定義
    code_with_local_def = """
# 本地已定義 IntegerOps
class IntegerOps:
    def compute(self, a, b):
        return a + b

def generate():
    ops = IntegerOps()
    result = ops.compute(5, 3)
    return {'answer': str(result)}
"""
    
    print("输入代码（已有本地 IntegerOps 定義）:")
    print(code_with_local_def)
    print()
    
    fixed_code, stats = healer.heal(code_with_local_def)
    
    print("修復後代码:")
    print(fixed_code)
    print()
    
    # 檢查是否有重複 import
    has_domain_import = "from domain_function_library import IntegerOps" in fixed_code
    
    if has_domain_import:
        print("❌ FAIL: 仍然添加了 domain_function_library 的 import (重複定義風險)")
        return False
    else:
        print("✅ PASS: 本地已定義，無重複 import (正確)")
        return True

def test_trailing_artifacts_removal():
    """Test: 末尾垃圾被正確移除"""
    print("\n" + "="*80)
    print("TEST 2: 移除末尾垃圾 (remove_trailing_artifacts)")
    print("="*80)
    
    healer = RegexHealer()
    
    test_cases = [
        ("末尾 }", "def f():\n    return 1\n}", "def f():\n    return 1"),
        ("末尾 python", "def f():\n    return 1\npython", "def f():\n    return 1"),
        ("末尾 };", "def f():\n    return 1\n};", "def f():\n    return 1"),
        ("多層垃圾", "def f():\n    x=1\n};\npython", "def f():\n    x=1"),
    ]
    
    all_passed = True
    for name, input_code, expected in test_cases:
        result, _ = healer.heal(input_code)
        passed = result == expected
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if not passed:
            print(f"  Expected: {repr(expected)}")
            print(f"  Got:      {repr(result)}")
            all_passed = False
    
    return all_passed

def test_combined_fix():
    """Test: 兩個修復結合使用"""
    print("\n" + "="*80)
    print("TEST 3: 兩個修復結合 (實戰場景)")
    print("="*80)
    
    healer = RegexHealer()
    
    # 模擬 Ab3 的真實場景：本地定義 + 末尾垃圾
    # 關鍵：末尾垃圾 } 和 python 應該是在新行上（LLM 添加的，而不是代碼本身）
    realistic_ab3_code = """class IntegerOps:
    def __init__(self):
        self.name = "Integer Operations"
    
    def add(self, a, b):
        return a + b

def generate(level=1, **kwargs):
    ops = IntegerOps()
    a = 5
    b = 3
    result = ops.add(a, b)
    return {'question_text': f'{a}+{b}', 'correct_answer': str(result), 'answer': '', 'mode': 1}
}
python"""
    
    print("输入: Ab3 實戰代碼（本地定義 + 末尾垃圾）")
    print(f"代碼末尾: ...{repr(realistic_ab3_code[-30:])}")
    print()
    
    fixed_code, stats = healer.heal(realistic_ab3_code)
    
    print(f"修復後末尾: ...{repr(fixed_code[-30:])}")
    print(f"修復統計: {stats}")
    print()
    
    # 檢查：
    # 1. 沒有重複 import
    has_duplicate_import = "from domain_function_library import IntegerOps" in fixed_code
    
    # 2. 末尾垃圾被移除 - 檢查是否沒有「新行後跟 } 或 python」
    # 末尾不應該有孤立的新行 + 垃圾
    ends_with_isolated_garbage = bool(re.search(r'\n\s*[}a-z]', fixed_code[-20:]))
    
    # 3. 代碼能編譯
    try:
        compile(fixed_code, '<string>', 'exec')
        compiles = True
        compile_error = None
    except Exception as e:
        compiles = False
        compile_error = str(e)
    
    print("檢查結果:")
    print(f"  {'✅' if not has_duplicate_import else '❌'} 無重複 import")
    print(f"  {'✅' if not ends_with_isolated_garbage else '❌'} 末尾無孤立垃圾")
    if not compiles:
        print(f"  ❌ 代碼編譯失敗: {compile_error}")
    else:
        print(f"  ✅ 代碼能正確編譯")
    
    return (not has_duplicate_import) and (not ends_with_isolated_garbage) and compiles

if __name__ == "__main__":
    print("\n🚨 EMERGENCY FIX VERIFICATION")
    print("="*80)
    
    results = []
    results.append(("禁止重複 Import", test_no_duplicate_import()))
    results.append(("移除末尾垃圾", test_trailing_artifacts_removal()))
    results.append(("兩個修復結合", test_combined_fix()))
    
    print("\n" + "="*80)
    print("測試摘要")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
    
    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)
    
    print(f"\n📊 結果: {total_passed}/{total_tests} 通過")
    
    if total_passed == total_tests:
        print("🎉 Ab3 可以從庸醫變成神醫了！")
    else:
        print("⚠️ 仍有問題需要修復")
