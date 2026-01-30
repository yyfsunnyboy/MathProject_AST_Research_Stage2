# -*- coding: utf-8 -*-
# ⚠️⚠️⚠️ 暫時檔案 可刪除! ⚠️⚠️⚠️
# 本檔案僅供重構期間測試使用，完成後可安全刪除
# 創建時間: 2026-01-30
# 用途: 驗證重構後的向後相容性
"""
=============================================================================
模組名稱 (Module Name): temp/test_backward_compatibility.py
功能說明 (Description): 測試 code_generator 重構後的向後相容性
執行語法 (Usage): python temp/test_backward_compatibility.py
版本資訊 (Version): 1.0 (Temporary Test)
更新日期 (Date): 2026-01-30
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_import():
    """測試導入是否正常"""
    try:
        from core.code_generator import auto_generate_skill_code
        print("✅ Import 成功")
        return True
    except Exception as e:
        print(f"❌ Import 失敗: {e}")
        return False

def test_function_signature():
    """測試函數簽名是否正確"""
    try:
        from core.code_generator import auto_generate_skill_code
        import inspect
        sig = inspect.signature(auto_generate_skill_code)
        params = list(sig.parameters.keys())
        
        assert 'skill_id' in params, "缺少 skill_id 參數"
        assert 'queue' in params, "缺少 queue 參數"
        print("✅ 函數簽名正確")
        print(f"   參數列表: {params}")
        return True
    except Exception as e:
        print(f"❌ 函數簽名測試失敗: {e}")
        return False

def test_utils_import():
    """測試工具函數導入"""
    try:
        from core.utils import safe_choice, to_latex, fmt_num
        print("✅ Utils 模組導入成功")
        return True
    except Exception as e:
        print(f"⚠️ Utils 模組導入失敗（預期，尚未建立）: {e}")
        return False

def test_healers_import():
    """測試 Healers 模組導入"""
    try:
        from core.healers import RegexHealer, ASTHealer
        print("✅ Healers 模組導入成功")
        return True
    except Exception as e:
        print(f"⚠️ Healers 模組導入失敗（預期，尚未建立）: {e}")
        return False

def test_validators_import():
    """測試 Validators 模組導入"""
    try:
        from core.validators import SyntaxValidator, DynamicSampler
        print("✅ Validators 模組導入成功")
        return True
    except Exception as e:
        print(f"⚠️ Validators 模組導入失敗: {e}")
        return False

def test_prompts_import():
    """測試 Prompts 模組導入"""
    try:
        from core.prompts import PromptBuilder
        print("✅ Prompts 模組導入成功")
        return True
    except Exception as e:
        print(f"⚠️ Prompts 模組導入失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Code Generator 重構 - 向後相容性測試")
    print("=" * 60)
    
    tests = [
        ("基礎導入測試", test_import),
        ("函數簽名測試", test_function_signature),
        ("Utils 模組測試", test_utils_import),
        ("Healers 模組測試", test_healers_import),
        ("Validators 模組測試", test_validators_import),
        ("Prompts 模組測試", test_prompts_import),
    ]
    
    results = []
    for name, test in tests:
        print(f"\n📋 {name}")
        print("-" * 60)
        results.append(test())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！")
    elif passed >= 2:
        print("⚠️ 部分測試通過（重構進行中）")
    else:
        print("❌ 多數測試失敗，請檢查！")
    print("=" * 60)
