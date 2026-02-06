# -*- coding: utf-8 -*-
"""
===============================================================================
程式名稱: regression_test.py - AI 代碼生成器回歸測試系統
===============================================================================

【程式用途】
    防止 Healer 修改導致已成功技能失效（Regression Bug）
    確保 code_generator.py 的任何修改不會破壞已驗證的技能生成

【研究背景】
    專案：旺宏科學獎 - 複合式 AI 架構降低數學題庫生成成本之研究
    核心問題：
        - 修復技能 A 成功 → 修改 Healer 修復技能 B → 技能 A 又失敗了！
        - 原因：Healer 的 Regex 過度匹配或破壞代碼結構
        - 影響：無法建立穩定的技能生成流水線
    
    解決方案：
        - 建立「Golden Skills」基準集（已驗證成功的技能）
        - 每次修改 Healer 後自動執行回歸測試
        - 100% 通過才允許提交修改

【主要功能】
    1. Golden Skills 管理
       - 維護已驗證成功的技能列表（GOLDEN_SKILLS）
       - 支援逐步擴充測試集
    
    2. 自動化測試流程
       - 重新生成每個 Golden Skill 的代碼
       - 驗證生成的檔案存在
       - 動態載入並執行 generate() 函數
       - 執行 3 次採樣測試，確保穩定性
    
    3. 詳細測試報告
       - 即時顯示每個技能的測試進度
       - 統計通過率（X/Y 通過）
       - 標示失敗的具體步驟

【使用場景】
    ✅ 必須使用的時機：
       - 修改 core/code_generator.py 的 Healer 邏輯後
       - 新增或修改任何 Regex 修復規則
       - 調整 AST Healer 的邏輯
       - 修改 Dynamic Sampling 機制
    
    ⚠️  建議使用的時機：
       - 每日開發結束前（建立檢查點）
       - 準備執行正式實驗前
       - 提交重要程式碼變更前
    
    🚫 不需要使用的時機：
       - 僅修改 UI 或資料庫 Schema
       - 僅修改文件或註解
       - 調整實驗參數（不涉及代碼生成）

【技術說明】
    測試方法：
        1. 呼叫 auto_generate_skill_code() 重新生成代碼
        2. 使用 importlib 動態載入生成的 .py 檔案
        3. 執行 generate() 函數 3 次
        4. 驗證返回值格式：{'question_text': ..., 'answer': ...}
    
    測試配置：
        - Ablation ID: 3 (Full-Healing 完整修復模式)
        - Model Size: 14B (Qwen 2.5-Coder 14B)
        - Prompt Level: Full-Healing
    
    成功標準：
        - 代碼生成成功（is_ok = True）
        - 檔案成功寫入 skills/ 目錄
        - generate() 函數可執行
        - 返回值包含必要欄位
        - 3 次採樣全部通過

【開發流程（黃金法則）】
    1. 修改前：確認當前回歸測試 100% 通過
    2. 修改 Healer：在 code_generator.py 中實作新邏輯
    3. 立即測試：執行 python scripts/regression_test.py
    4. 驗證結果：
       ✅ 100% 通過 → 可以繼續開發新技能
       ❌ 有失敗 → 回滾修改或修正問題
    5. 新技能成功後：加入 GOLDEN_SKILLS 列表

【Golden Skills 擴充原則】
    - 只加入已通過至少 10 次生成測試的技能
    - 優先選擇不同類型的技能（整數、分數、小數、混合）
    - 確保 MASTER_SPEC 質量穩定
    - 定期清理不再需要的測試項目

【版本資訊】
    版本：v1.0
    建立日期：2026-01-28
    作者：MathProject_AST_Research Team
    相關文件：
        - scripts/safe_healer_development.md（安全開發流程）
        - docs/競賽文件/專案速查.md（專案概覽）
        - core/code_generator.py（被測試的核心模組）
    
    變更記錄：
        v1.0 (2026-01-28): 初始版本
            - 建立基本回歸測試框架
            - 支援單一技能測試和批量測試
            - 實作詳細的測試報告輸出

【執行範例】
    # 執行所有 Golden Skills 的回歸測試
    python scripts/regression_test.py
    
    # 預期輸出
    ======================================================================
    🚀 開始回歸測試 - 驗證 Healer 修改是否影響已成功技能
    ======================================================================
    
    ============================================================
    🧪 測試技能: jh_數學1上_FourArithmeticOperationsOfIntegers
    ============================================================
    ✅ 測試 1/3 通過
    ✅ 測試 2/3 通過
    ✅ 測試 3/3 通過
    ✅ jh_數學1上_FourArithmeticOperationsOfIntegers - 全部測試通過
    
    ======================================================================
    📊 測試總結
    ======================================================================
    ✅ PASS - jh_數學1上_FourArithmeticOperationsOfIntegers
    
    總計: 1/1 通過
    🎉 所有回歸測試通過！可以安全提交修改。

【重要提醒】
    ⚠️  回歸測試失敗表示：
        1. 您的修改可能過度匹配（Regex 太寬鬆）
        2. 新的 Healer 與舊的 Healer 產生衝突
        3. 使用了危險的字串插入操作
    
    🔧 失敗後的處理流程：
        1. 檢查最近修改的 Healer 代碼
        2. 使用 git diff 比對變更
        3. 回滾到上一個穩定版本
        4. 重新設計更精確的修復邏輯
        5. 再次執行回歸測試
    
    🎯 目標：維持 100% 回歸測試通過率
         這是確保實驗數據公信力的關鍵！

===============================================================================
"""

import sys
import os

# 路徑設定
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db
from core.code_generator import auto_generate_skill_code
import importlib.util

# 已知成功的技能列表（Golden Set）
GOLDEN_SKILLS = [
    'jh_數學1上_FourArithmeticOperationsOfIntegers',  # 整數四則運算（已成功）
    'jh_數學1上_IntegerAdditionOperation',  # 整數的加法運算
    'jh_數學1上_IntegerSubtractionOperation',  # 整數的減法運算
    'jh_數學1上_IntegerMultiplication',  # 整數的乘法運算
    'jh_數學1上_IntegerDivision',  # 整數的除法運算
]

def test_skill_generation(skill_id):
    """測試單個技能的生成"""
    print(f"\n{'='*60}")
    print(f"🧪 測試技能: {skill_id}")
    print(f"{'='*60}")
    
    try:
        # 1. 生成代碼
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id, 
            queue=None, 
            ablation_id=3, 
            model_size_class='14B',
            prompt_level='Full-Healing'
        )
        
        if not is_ok:
            print(f"❌ 生成失敗: {msg}")
            return False
        
        # 2. 檢查檔案是否存在
        skill_file = os.path.join(project_root, 'skills', f'{skill_id}.py')
        if not os.path.exists(skill_file):
            print(f"❌ 檔案未生成: {skill_file}")
            return False
        
        # 3. 動態載入並測試 generate() 函數
        spec = importlib.util.spec_from_file_location("temp_skill", skill_file)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)
        
        # 4. 執行 3 次測試
        for i in range(3):
            try:
                item = temp_module.generate()
                assert isinstance(item, dict), f"返回類型錯誤: {type(item)}"
                assert 'question_text' in item, "缺少 question_text"
                assert 'answer' in item, "缺少 answer"
                print(f"  ✅ 測試 {i+1}/3 通過")
            except Exception as e:
                print(f"  ❌ 測試 {i+1}/3 失敗: {str(e)}")
                return False
        
        print(f"✅ {skill_id} - 全部測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_regression_tests():
    """執行所有回歸測試"""
    print("\n" + "="*70)
    print("🚀 開始回歸測試 - 驗證 Healer 修改是否影響已成功技能")
    print("="*70)
    
    results = {}
    for skill_id in GOLDEN_SKILLS:
        results[skill_id] = test_skill_generation(skill_id)
    
    # 總結
    print("\n" + "="*70)
    print("📊 測試總結")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for skill_id, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {skill_id}")
    
    print(f"\n總計: {passed}/{total} 通過")
    
    if passed == total:
        print("\n🎉 所有回歸測試通過！可以安全提交修改。")
        return True
    else:
        print("\n⚠️  發現回歸錯誤！請檢查 Healer 修改。")
        return False

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        success = run_regression_tests()
        sys.exit(0 if success else 1)
