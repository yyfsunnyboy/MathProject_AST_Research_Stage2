"""驗證方案 1 實施結果：場景區分法"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT

def verify_solution1():
    """驗證方案 1 的實施結果"""
    
    print("=" * 80)
    print("【方案 1 實施驗證】場景區分法")
    print("=" * 80)
    print()
    
    # 檢查點 1: 是否包含場景分類決策樹
    has_decision_tree = "場景分類決策樹" in UNIVERSAL_GEN_CODE_PROMPT
    has_scenario_a = "🟢 場景 A：Domain 函數題型" in UNIVERSAL_GEN_CODE_PROMPT
    has_scenario_b = "🟡 場景 B：簡單運算題型" in UNIVERSAL_GEN_CODE_PROMPT
    
    # 檢查點 2: 是否強調工程化 = 簡潔
    has_engineering_principle = "工程化 = 簡潔直接" in UNIVERSAL_GEN_CODE_PROMPT
    
    # 檢查點 3: 是否提供清晰的實作範例
    has_scenario_a_example = "標準實作流程（方案 1）" in UNIVERSAL_GEN_CODE_PROMPT
    has_scenario_b_example = "方式 A：手動添加 $（推薦" in UNIVERSAL_GEN_CODE_PROMPT
    
    # 檢查點 4: 是否明確禁止混合模式
    has_forbidden_pattern = "絕對禁止的混合模式" in UNIVERSAL_GEN_CODE_PROMPT
    
    # 檢查點 5: 是否包含記憶口訣
    has_mnemonic_a = "Domain 函數已完美 → 手動加 $ → 直接用，不 clean" in UNIVERSAL_GEN_CODE_PROMPT
    has_mnemonic_b = "簡單運算 → 優先手動 $ → 或最後 clean 一次" in UNIVERSAL_GEN_CODE_PROMPT
    
    print("✅ 檢查點 1: 場景分類")
    print(f"   - 決策樹: {has_decision_tree}")
    print(f"   - 場景 A (Domain 函數): {has_scenario_a}")
    print(f"   - 場景 B (簡單運算): {has_scenario_b}")
    print()
    
    print("✅ 檢查點 2: 核心原則")
    print(f"   - 工程化 = 簡潔直接: {has_engineering_principle}")
    print()
    
    print("✅ 檢查點 3: 實作範例")
    print(f"   - 場景 A 範例: {has_scenario_a_example}")
    print(f"   - 場景 B 範例: {has_scenario_b_example}")
    print()
    
    print("✅ 檢查點 4: 禁止模式")
    print(f"   - 混合模式警告: {has_forbidden_pattern}")
    print()
    
    print("✅ 檢查點 5: 記憶口訣")
    print(f"   - 場景 A 口訣: {has_mnemonic_a}")
    print(f"   - 場景 B 口訣: {has_mnemonic_b}")
    print()
    
    # 提取場景 A 的部分
    if "🟢 場景 A：Domain 函數題型" in UNIVERSAL_GEN_CODE_PROMPT:
        scenario_a_start = UNIVERSAL_GEN_CODE_PROMPT.index("🟢 場景 A：Domain 函數題型")
        scenario_a_end = UNIVERSAL_GEN_CODE_PROMPT.find("🟡 場景 B：", scenario_a_start)
        if scenario_a_end == -1:
            scenario_a_end = scenario_a_start + 1500
        
        print("=" * 80)
        print("【場景 A 摘錄】Domain 函數題型")
        print("=" * 80)
        print()
        print(UNIVERSAL_GEN_CODE_PROMPT[scenario_a_start:scenario_a_end].strip()[:800])
        print("...")
        print()
    
    # 提取場景 B 的部分
    if "🟡 場景 B：簡單運算題型" in UNIVERSAL_GEN_CODE_PROMPT:
        scenario_b_start = UNIVERSAL_GEN_CODE_PROMPT.index("🟡 場景 B：簡單運算題型")
        scenario_b_end = UNIVERSAL_GEN_CODE_PROMPT.find("🔴 絕對禁止的混合模式", scenario_b_start)
        if scenario_b_end == -1:
            scenario_b_end = scenario_b_start + 1200
        
        print("=" * 80)
        print("【場景 B 摘錄】簡單運算題型")
        print("=" * 80)
        print()
        print(UNIVERSAL_GEN_CODE_PROMPT[scenario_b_start:scenario_b_end].strip()[:600])
        print("...")
        print()
    
    # 最終判斷
    print("=" * 80)
    print("【實施驗證結果】")
    print("=" * 80)
    print()
    
    all_pass = (
        has_decision_tree and 
        has_scenario_a and 
        has_scenario_b and 
        has_engineering_principle and
        has_scenario_a_example and
        has_scenario_b_example and
        has_forbidden_pattern and
        has_mnemonic_a and
        has_mnemonic_b
    )
    
    if all_pass:
        print("✅ 方案 1 實施成功！")
        print()
        print("新的 UNIVERSAL Prompt 特點：")
        print("  🎯 清晰的場景分類決策樹")
        print("  🟢 場景 A：Domain 函數 → 手動 $ + 禁止 clean")
        print("  🟡 場景 B：簡單運算 → 優先手動 $ 或可選 clean")
        print("  🔴 明確禁止混合模式")
        print("  📌 易記的口訣幫助理解")
        print()
        print("優勢：")
        print("  ✅ 簡潔直接，符合工程化真義")
        print("  ✅ 消除字串處理複雜度")
        print("  ✅ 徹底解決 placeholder 外洩")
        print("  ✅ AI 更容易理解和遵循")
        print()
        print("下次生成代碼時，AI 將自動：")
        print("  1. 判斷題型場景（Domain 函數 vs 簡單運算）")
        print("  2. 選擇對應的實作方式")
        print("  3. 避免混合模式的致命錯誤")
        return True
    else:
        print("❌ 實施不完整，請檢查：")
        if not has_decision_tree:
            print("  - 缺少場景分類決策樹")
        if not has_scenario_a:
            print("  - 缺少場景 A 說明")
        if not has_scenario_b:
            print("  - 缺少場景 B 說明")
        if not has_engineering_principle:
            print("  - 缺少工程化原則說明")
        if not has_scenario_a_example:
            print("  - 缺少場景 A 範例")
        if not has_scenario_b_example:
            print("  - 缺少場景 B 範例")
        if not has_forbidden_pattern:
            print("  - 缺少混合模式警告")
        if not has_mnemonic_a or not has_mnemonic_b:
            print("  - 缺少記憶口訣")
        return False

if __name__ == "__main__":
    success = verify_solution1()
    sys.exit(0 if success else 1)
