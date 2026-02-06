# -*- coding: utf-8 -*-
"""
===============================================================================
程式名稱: build_golden_skills.py - Golden Skills 快速建立工具
===============================================================================

【程式用途】
    自動測試簡單技能，快速建立 Golden Skills 基準集
    避免手動逐個測試的繁瑣流程

【研究背景】
    專案：旺宏科學獎 - 複合式 AI 架構降低數學題庫生成成本之研究
    
    問題：
        - 分數四則運算太複雜，不適合作為早期 Golden Skill
        - 需要從簡單技能開始建立穩定基準
        - 手動測試效率低
    
    解決方案：
        - 按難度排序測試候選技能
        - 自動生成並驗證
        - 成功後立即加入 regression_test.py

【主要功能】
    1. 候選技能清單（按難度排序）
    2. 自動批次生成測試
    3. 成功技能自動加入 GOLDEN_SKILLS
    4. 詳細成功/失敗報告

【使用場景】
    ✅ 必須使用：
       - 第一次建立 Golden Skills 集合
       - 擴充 Golden Skills 到 5-10 個
    
    ⚠️ 建議使用：
       - 定期補充新的穩定技能
    
    🚫 不需要：
       - Golden Skills 已足夠（5+ 個）
       - 只測試單一技能

【技術說明】
    測試配置：
        - Ablation ID: 3 (Full-Healing)
        - Model: Qwen 2.5-Coder 14B
        - 每個技能測試 3 次
    
    候選技能（按難度）：
        1. IntegerAdditionOperation (⭐)
        2. IntegerSubtractionOperation (⭐)
        3. PositiveAndNegativeNumbers (⭐)
        4. IntegerMultiplication (⭐⭐)
        5. IntegerDivision (⭐⭐)

【版本資訊】
    版本：v1.0
    建立日期：2026-01-28
    作者：MathProject_AST_Research Team

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

# 候選技能列表（按難度排序，從簡單到複雜）
CANDIDATE_SKILLS = [
    ('jh_數學1上_IntegerAdditionOperation', '整數的加法運算', '⭐'),
    ('jh_數學1上_IntegerSubtractionOperation', '整數的減法運算', '⭐'),
    ('jh_數學1上_PositiveAndNegativeNumbers', '正數與負數', '⭐'),
    ('jh_數學1上_IntegerMultiplication', '整數的乘法運算', '⭐⭐'),
    ('jh_數學1上_IntegerDivision', '整數的除法運算', '⭐⭐'),
    # 添加更多候選技能...
]

def test_skill(skill_id, skill_name):
    """測試單個技能的生成和執行"""
    print(f"\n{'='*70}")
    print(f"🧪 測試技能: {skill_name} ({skill_id})")
    print(f"{'='*70}")
    
    try:
        # 1. 生成代碼
        print("  [1/4] 正在生成代碼...")
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id,
            queue=None,
            ablation_id=3,
            model_size_class='14B',
            prompt_level='Full-Healing'
        )
        
        if not is_ok:
            print(f"  ❌ 生成失敗: {msg}")
            return False, msg
        
        print(f"  ✅ 代碼生成成功")
        
        # 2. 檢查檔案
        print("  [2/4] 檢查檔案是否存在...")
        skill_file = os.path.join(project_root, 'skills', f'{skill_id}.py')
        if not os.path.exists(skill_file):
            print(f"  ❌ 檔案未生成")
            return False, "File not created"
        
        print(f"  ✅ 檔案已創建: {skill_file}")
        
        # 3. 動態載入
        print("  [3/4] 動態載入模組...")
        spec = importlib.util.spec_from_file_location("temp_skill", skill_file)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)
        print(f"  ✅ 模組載入成功")
        
        # 4. 執行測試（3 次）
        print("  [4/4] 執行 3 次採樣測試...")
        for i in range(3):
            try:
                item = temp_module.generate()
                assert isinstance(item, dict), f"返回類型錯誤: {type(item)}"
                assert 'question_text' in item, "缺少 question_text"
                assert 'answer' in item, "缺少 answer"
                print(f"    ✅ 測試 {i+1}/3 通過")
            except Exception as e:
                print(f"    ❌ 測試 {i+1}/3 失敗: {str(e)}")
                return False, f"Runtime test failed: {str(e)}"
        
        print(f"\n🎉 {skill_name} - 全部測試通過！")
        return True, "Success"
        
    except Exception as e:
        print(f"  ❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def build_golden_skills(max_skills=5):
    """自動建立 Golden Skills"""
    print("\n" + "="*70)
    print("🚀 Golden Skills 自動建立工具")
    print(f"📊 目標: 建立 {max_skills} 個穩定的 Golden Skills")
    print("="*70)
    
    successful_skills = []
    failed_skills = []
    
    for skill_id, skill_name, difficulty in CANDIDATE_SKILLS:
        if len(successful_skills) >= max_skills:
            print(f"\n✅ 已達成目標：{len(successful_skills)} 個 Golden Skills")
            break
        
        print(f"\n{'→'*35}")
        print(f"📌 候選技能 {len(successful_skills)+1}/{max_skills}")
        print(f"   難度: {difficulty}")
        print(f"{'→'*35}")
        
        success, message = test_skill(skill_id, skill_name)
        
        if success:
            successful_skills.append((skill_id, skill_name))
            print(f"\n✅ 成功！已加入 Golden Skills 清單")
        else:
            failed_skills.append((skill_id, skill_name, message))
            print(f"\n❌ 失敗，跳過此技能")
            print(f"   原因: {message}")
            print(f"   策略: 繼續測試下一個候選技能")
    
    # 總結
    print("\n" + "="*70)
    print("📊 建立結果總結")
    print("="*70)
    
    print(f"\n✅ 成功技能 ({len(successful_skills)} 個):")
    for i, (skill_id, skill_name) in enumerate(successful_skills, 1):
        print(f"  {i}. {skill_name}")
        print(f"     ID: {skill_id}")
    
    if failed_skills:
        print(f"\n❌ 失敗技能 ({len(failed_skills)} 個):")
        for i, (skill_id, skill_name, message) in enumerate(failed_skills, 1):
            print(f"  {i}. {skill_name}")
            print(f"     ID: {skill_id}")
            print(f"     原因: {message[:50]}...")
    
    # 生成 regression_test.py 的更新代碼
    if successful_skills:
        print("\n" + "="*70)
        print("📝 請將以下技能加入 regression_test.py 的 GOLDEN_SKILLS:")
        print("="*70)
        print("\nGOLDEN_SKILLS = [")
        for skill_id, skill_name in successful_skills:
            print(f"    '{skill_id}',  # {skill_name}")
        print("]")
        
        print("\n💡 提示：複製上面的代碼，替換 regression_test.py 中的 GOLDEN_SKILLS 列表")
    
    return successful_skills, failed_skills

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # 預設建立 5 個 Golden Skills
        target = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        successful, failed = build_golden_skills(max_skills=target)
        
        print(f"\n🏆 最終結果: {len(successful)}/{target} 個 Golden Skills 建立成功")
        sys.exit(0 if len(successful) >= 3 else 1)  # 至少需要 3 個才算成功
