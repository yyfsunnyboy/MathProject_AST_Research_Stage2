"""
測試 Domain 函數自動注入機制
驗證修改後的 code_generator.py 能否正確注入 Domain 函數庫
"""
import sys
import os

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.code_generator import build_calculation_skeleton

def test_domain_injection():
    """測試 Domain 函數注入"""
    
    # 測試 1: 無 skill_id（向後兼容）
    print("=" * 70)
    print("測試 1: build_calculation_skeleton() - 無 skill_id")
    print("=" * 70)
    skeleton_no_skill = build_calculation_skeleton()
    print(f"長度: {len(skeleton_no_skill)} 字元")
    assert "[INJECTED UTILS]" in skeleton_no_skill
    assert "[AI GENERATED CODE]" in skeleton_no_skill
    print("✅ 測試通過：包含基礎工具注入\n")
    
    # 測試 2: ApplicationsOfDerivatives（應該注入多項式函數）
    print("=" * 70)
    print("測試 2: build_calculation_skeleton('gh_ApplicationsOfDerivatives')")
    print("=" * 70)
    skeleton_deriv = build_calculation_skeleton('gh_ApplicationsOfDerivatives')
    
    print(f"長度: {len(skeleton_deriv)} 字元")
    
    # 驗證包含 Domain 函數
    assert "[DOMAIN HELPERS" in skeleton_deriv, "❌ 缺少 Domain 函數標記"
    assert "def _poly_to_latex" in skeleton_deriv, "❌ 缺少 _poly_to_latex 函數"
    assert "def _differentiate_poly" in skeleton_deriv, "❌ 缺少 _differentiate_poly 函數"
    assert "def _deriv_symbol_latex" in skeleton_deriv, "❌ 缺少 _deriv_symbol_latex 函數"
    
    print("✅ 測試通過：正確注入多項式函數庫")
    
    # 顯示注入的函數列表
    domain_section = skeleton_deriv.split("[DOMAIN HELPERS")[1].split("[AI GENERATED CODE]")[0]
    functions = [line.strip() for line in domain_section.split('\n') if line.strip().startswith('def ')]
    print(f"\n注入的 Domain 函數（共 {len(functions)} 個）:")
    for func in functions:
        print(f"  - {func}")
    
    print("\n" + "=" * 70)
    print("🎉 所有測試通過！Domain 函數自動注入機制運作正常")
    print("=" * 70)

if __name__ == "__main__":
    test_domain_injection()
