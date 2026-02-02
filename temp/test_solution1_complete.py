"""快速測試：驗證方案 1 實施後的完整系統"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prompts.prompt_builder import UNIVERSAL_GEN_CODE_PROMPT, PromptBuilder
from core.prompt_architect import ARCHITECT_SYSTEM_PROMPT
from models import db, SkillGenCodePrompt
from app import app

def test_complete_system():
    """測試完整的 Prompt 系統"""
    
    print("=" * 80)
    print("【方案 1 完整系統測試】")
    print("=" * 80)
    print()
    
    # 測試 1: Architect Prompt
    print("✅ 測試 1: Architect System Prompt")
    print("-" * 80)
    
    has_architect_mode_a = "模式 A：使用 Domain 標準函數" in ARCHITECT_SYSTEM_PROMPT
    has_architect_mode_b = "模式 B：簡單運算式" in ARCHITECT_SYSTEM_PROMPT
    has_architect_warning = "絕對禁止**對 Domain 函數結果調用 clean_latex_output()" in ARCHITECT_SYSTEM_PROMPT
    
    print(f"   - Domain 模式說明: {has_architect_mode_a}")
    print(f"   - 簡單運算模式說明: {has_architect_mode_b}")
    print(f"   - 禁止 clean 警告: {has_architect_warning}")
    
    architect_ok = has_architect_mode_a and has_architect_mode_b and has_architect_warning
    print(f"   → Architect Prompt: {'✅ 通過' if architect_ok else '❌ 失敗'}")
    print()
    
    # 測試 2: UNIVERSAL Prompt
    print("✅ 測試 2: UNIVERSAL Prompt")
    print("-" * 80)
    
    has_decision_tree = "場景分類決策樹" in UNIVERSAL_GEN_CODE_PROMPT
    has_scenario_a = "🟢 場景 A：Domain 函數題型" in UNIVERSAL_GEN_CODE_PROMPT
    has_scenario_b = "🟡 場景 B：簡單運算題型" in UNIVERSAL_GEN_CODE_PROMPT
    has_mnemonic = "Domain 函數已完美 → 手動加 $ → 直接用，不 clean" in UNIVERSAL_GEN_CODE_PROMPT
    
    print(f"   - 決策樹: {has_decision_tree}")
    print(f"   - 場景 A: {has_scenario_a}")
    print(f"   - 場景 B: {has_scenario_b}")
    print(f"   - 記憶口訣: {has_mnemonic}")
    
    universal_ok = has_decision_tree and has_scenario_a and has_scenario_b and has_mnemonic
    print(f"   → UNIVERSAL Prompt: {'✅ 通過' if universal_ok else '❌ 失敗'}")
    print()
    
    # 測試 3: MASTER_SPEC (Database)
    print("✅ 測試 3: 資料庫 MASTER_SPEC")
    print("-" * 80)
    
    try:
        app.app_context().push()
        
        latest_spec = SkillGenCodePrompt.query.filter_by(
            skill_id='gh_ApplicationsOfDerivatives',
            prompt_type='MASTER_SPEC'
        ).order_by(SkillGenCodePrompt.id.desc()).first()
        
        if latest_spec:
            spec_content = latest_spec.prompt_content
            
            # 檢查是否已修復（不包含強制 clean 指令）
            has_old_bug = "最後呼叫 `q = clean_latex_output(q)`" in spec_content and \
                         "組合：將式子插入敘述，最後呼叫 clean_latex_output(q)" in spec_content
            
            has_format_conversion = "_coeffs_to_terms" in spec_content
            has_correct_answer_format = "純多項式，逗號分隔" in spec_content or "polynomial1, polynomial2" in spec_content
            
            print(f"   - 最新 MASTER_SPEC ID: {latest_spec.id}")
            print(f"   - 創建時間: {latest_spec.created_at}")
            print(f"   - 包含格式轉換: {has_format_conversion}")
            print(f"   - 包含答案格式規範: {has_correct_answer_format}")
            print(f"   - 包含舊的 clean bug: {has_old_bug}")
            
            spec_ok = has_format_conversion and has_correct_answer_format and not has_old_bug
            print(f"   → MASTER_SPEC: {'✅ 通過' if spec_ok else '⚠️ 建議重新生成'}")
        else:
            print("   - 未找到 MASTER_SPEC")
            spec_ok = False
            print(f"   → MASTER_SPEC: ⚠️ 未找到")
    except Exception as e:
        print(f"   - 資料庫錯誤: {e}")
        spec_ok = False
        print(f"   → MASTER_SPEC: ❌ 失敗")
    
    print()
    
    # 測試 4: Prompt Builder
    print("✅ 測試 4: Prompt Builder 整合")
    print("-" * 80)
    
    try:
        # 測試組裝 Ab2/Ab3 Prompt
        if latest_spec:
            full_prompt = PromptBuilder.build(
                master_spec=latest_spec.prompt_content,
                ablation_id=2,
                skill_id='gh_ApplicationsOfDerivatives'
            )
            
            # 檢查完整 Prompt
            has_universal = "場景分類決策樹" in full_prompt
            has_domain = "### 🔧 標準函數庫" in full_prompt or "POLYNOMIAL_HELPERS" in full_prompt
            has_master = "### MASTER_SPEC:" in full_prompt
            
            print(f"   - Prompt 總長度: {len(full_prompt)} 字元")
            print(f"   - 包含 UNIVERSAL: {has_universal}")
            print(f"   - 包含 Domain 函數: {has_domain}")
            print(f"   - 包含 MASTER_SPEC: {has_master}")
            
            builder_ok = has_universal and has_domain and has_master
            print(f"   → Prompt Builder: {'✅ 通過' if builder_ok else '❌ 失敗'}")
        else:
            builder_ok = False
            print(f"   → Prompt Builder: ⚠️ 無法測試（缺少 MASTER_SPEC）")
    except Exception as e:
        print(f"   - 組裝錯誤: {e}")
        builder_ok = False
        print(f"   → Prompt Builder: ❌ 失敗")
    
    print()
    
    # 最終報告
    print("=" * 80)
    print("【完整系統測試結果】")
    print("=" * 80)
    print()
    
    all_ok = architect_ok and universal_ok and spec_ok and builder_ok
    
    if all_ok:
        print("✅ 所有測試通過！系統已完整實施方案 1")
        print()
        print("修復總結：")
        print("  🎯 Architect：生成正確的 MASTER_SPEC（雙模式）")
        print("  🎯 UNIVERSAL：提供清晰的場景判斷指引")
        print("  🎯 Database：存儲修復後的 MASTER_SPEC")
        print("  🎯 Builder：正確組裝完整 Prompt")
        print()
        print("下一步：")
        print("  1. 運行 scripts/sync_skills_files.py 模式[2] 或 [3]")
        print("  2. 測試生成的代碼是否遵循場景 A 標準流程")
        print("  3. 驗證不再有 placeholder 外洩")
        return True
    else:
        print("⚠️ 部分測試未通過")
        print()
        print("狀態檢查：")
        print(f"  - Architect Prompt: {'✅' if architect_ok else '❌'}")
        print(f"  - UNIVERSAL Prompt: {'✅' if universal_ok else '❌'}")
        print(f"  - MASTER_SPEC: {'✅' if spec_ok else '⚠️'}")
        print(f"  - Prompt Builder: {'✅' if builder_ok else '⚠️'}")
        print()
        
        if not spec_ok:
            print("建議：重新生成 MASTER_SPEC")
            print("  python scripts/sync_skills_files.py")
            print("  選擇模式[4] - Architect")
        
        return False

if __name__ == "__main__":
    success = test_complete_system()
    sys.exit(0 if success else 1)
