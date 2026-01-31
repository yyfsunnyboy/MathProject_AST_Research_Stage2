"""
驗證修復後的 Ab2/Ab3 邏輯
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ab2_logic():
    """測試 Ab2 是否還有無限迴圈問題"""
    print("=" * 70)
    print("測試 Ab2: 驗證導數生成邏輯（10 次採樣）")
    print("=" * 70)
    
    from skills.gh_ApplicationsOfDerivatives_14B_Ab2 import generate
    
    for i in range(10):
        try:
            result = generate()
            print(f"  ✅ 第 {i+1} 題: {result['question_text'][:60]}...")
        except Exception as e:
            print(f"  ❌ 第 {i+1} 題失敗: {e}")
            return False
    
    print("\n✅ Ab2 測試通過：無無限迴圈問題\n")
    return True

def test_ab3_coefficient_limit():
    """測試 Ab3 係數限制是否放寬"""
    print("=" * 70)
    print("測試 Ab3: 驗證係數限制放寬（20 次採樣）")
    print("=" * 70)
    
    from skills.gh_ApplicationsOfDerivatives_14B_Ab3 import generate
    
    success_count = 0
    for i in range(20):
        try:
            result = generate()
            success_count += 1
            print(f"  ✅ 第 {i+1} 題成功")
        except ValueError as e:
            if "exceeds limit" in str(e):
                print(f"  ❌ 第 {i+1} 題: 係數超限 {e}")
            else:
                raise
        except Exception as e:
            print(f"  ❌ 第 {i+1} 題失敗: {e}")
    
    success_rate = success_count / 20 * 100
    print(f"\n✅ Ab3 測試結果：{success_count}/20 成功 ({success_rate:.0f}%)")
    print(f"   預期：係數限制放寬後，成功率應接近 100%\n")
    return success_rate >= 95

if __name__ == "__main__":
    print("🔧 驗證修復：Ab2 無限迴圈 + Ab3 係數限制\n")
    
    test1 = test_ab2_logic()
    test2 = test_ab3_coefficient_limit()
    
    if test1 and test2:
        print("=" * 70)
        print("🎉 所有測試通過！可以開始 20 samples 統計測試")
        print("=" * 70)
    else:
        print("❌ 仍有問題需要修復")
