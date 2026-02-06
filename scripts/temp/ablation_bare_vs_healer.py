# -*- coding: utf-8 -*-
"""
===============================================================================
程式名稱: ablation_bare_vs_healer.py - Healer 價值驗證實驗
===============================================================================

【程式用途】
    驗證 Healer 的真實價值：對比 Bare Prompt vs Full-Healing
    回答核心問題：Qwen 14B 裸跑能輕易生成簡單技能嗎？

【研究背景】
    專案：旺宏科學獎 - 複合式 AI 架構降低數學題庫生成成本之研究
    
    關鍵質疑：
        - 簡單技能（整數加減乘除）可能不需要 Healer 就能成功
        - 如果 Healer 只做微弱修復，說服力不足
        - 需要用對照實驗證明 Healer 的必要性
    
    解決方案：
        - Ablation Study: 對比 Bare (ablation_id=1) vs Full-Healing (ablation_id=3)
        - 統計修復次數和成功率差異
        - 證明 Healer 的實際貢獻

【主要功能】
    1. 使用 Bare Prompt（無 Healer）生成技能
    2. 使用 Full-Healing（有 Healer）生成同一技能
    3. 對比兩者的成功率和修復統計
    4. 生成詳細的對比報告

【執行範例】
    python scripts/ablation_bare_vs_healer.py
    
    預期輸出：
    ======================================================================
    🔬 Ablation Study: Bare vs Full-Healing
    ======================================================================
    
    技能: jh_數學1上_IntegerAdditionOperation
    
    📊 Bare Prompt (無 Healer):
      ❌ 生成失敗: SyntaxError
      修復次數: 0
    
    📊 Full-Healing (有 Healer):
      ✅ 生成成功
      修復次數: 3 (Regex: 2, AST: 1)
    
    💡 結論: Healer 修復了 3 個錯誤，成功率從 0% 提升到 100%

【版本資訊】
    版本：v1.0
    建立日期：2026-01-28
    作者：MathProject_AST_Research Team

===============================================================================
"""

import sys
import os
from datetime import datetime

# [Env Fix] 確保載入環境變數
from dotenv import load_dotenv
load_dotenv()  # 從 .env 載入環境變數

# 路徑設定
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db, SkillGenCodePrompt
from core.code_generator import auto_generate_skill_code
from core.prompt_architect import generate_v15_spec
import importlib.util

# 測試技能列表
TEST_SKILLS = [
    ('jh_數學1上_IntegerAdditionOperation', '整數的加法運算'),
    ('jh_數學1上_IntegerSubtractionOperation', '整數的減法運算'),
    ('jh_數學1上_IntegerMultiplication', '整數的乘法運算'),
    ('jh_數學1上_IntegerDivision', '整數的除法運算'),
]

# Ablation 配置
ABLATION_CONFIGS = [
    (1, 'Bare', 'Bare Prompt (270 chars) + MASTER_SPEC, 無 Healer'),
    (2, 'MASTER_SPEC_Only', 'Pure Database MASTER_SPEC, 無 Healer'),
    (3, 'Full_Healing', 'Database MASTER_SPEC + Full Healer (Regex+AST)'),
]

def ask_regenerate_prompts():
    """詢問是否重新生成 MASTER_SPEC (Prompt Architect)"""
    print("\n" + "="*70)
    print("🔍 實驗準備：檢查 MASTER_SPEC (Coding Prompt)")
    print("="*70)
    
    # 檢查每個技能的 MASTER_SPEC 狀態
    missing_specs = []
    for skill_id, skill_name in TEST_SKILLS:
        spec = SkillGenCodePrompt.query.filter_by(
            skill_id=skill_id, 
            prompt_type="MASTER_SPEC"
        ).order_by(SkillGenCodePrompt.created_at.desc()).first()
        
        if spec:
            spec_age = (datetime.now() - spec.created_at).days
            print(f"  ✅ {skill_name}")
            print(f"     已有 MASTER_SPEC ({len(spec.prompt_content)} chars, {spec_age} 天前建立)")
        else:
            print(f"  ❌ {skill_name}")
            print(f"     缺少 MASTER_SPEC")
            missing_specs.append((skill_id, skill_name))
    
    if missing_specs:
        print(f"\n⚠️  警告: {len(missing_specs)} 個技能缺少 MASTER_SPEC，實驗將無法進行！")
        print("\n是否立即生成缺少的 MASTER_SPEC? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == 'y':
            print("\n🔧 生成缺少的 MASTER_SPEC...")
            for skill_id, skill_name in missing_specs:
                print(f"\n  生成 {skill_name}...")
                try:
                    generate_v15_spec(skill_id)
                    print(f"  ✅ 完成")
                except Exception as e:
                    print(f"  ❌ 失敗: {str(e)}")
            return True
        else:
            print("\n❌ 取消實驗執行")
            return False
    
    print("\n💡 是否重新生成所有技能的 MASTER_SPEC (Prompt Architect)?")
    print("   注意：重新生成將覆蓋現有的 MASTER_SPEC")
    print("\n選項:")
    print("  y - 是，重新生成所有 MASTER_SPEC")
    print("  n - 否，使用現有的 MASTER_SPEC")
    print("\n請選擇 (y/n): ", end="")
    
    choice = input().strip().lower()
    
    if choice == 'y':
        print("\n🔧 重新生成所有技能的 MASTER_SPEC...")
        for skill_id, skill_name in TEST_SKILLS:
            print(f"\n  生成 {skill_name}...")
            try:
                generate_v15_spec(skill_id)
                print(f"  ✅ 完成")
            except Exception as e:
                print(f"  ❌ 失敗: {str(e)}")
        print("\n✅ MASTER_SPEC 重新生成完成！")
        return True
    else:
        print("\n✅ 使用現有的 MASTER_SPEC 繼續實驗")
        return True

def test_with_ablation(skill_id, skill_name, ablation_id, ablation_name, model_size='14B'):
    """使用指定的 ablation 配置測試技能"""
    print(f"\n{'─'*70}")
    print(f"📊 測試組 Ab{ablation_id}: {ablation_name}")
    print(f"{'─'*70}")
    
    # 構建自定義檔案名稱：skill_id_模型等級_AbX.py
    custom_filename = f"{skill_id}_{model_size}_Ab{ablation_id}.py"
    custom_filepath = os.path.join(project_root, 'skills', custom_filename)
    
    print(f"  📝 輸出檔案: {custom_filename}")
    
    try:
        # 生成代碼
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id,
            queue=None,
            ablation_id=ablation_id,
            model_size_class=model_size,
            prompt_level=ablation_name,
            custom_output_path=custom_filepath  # 傳入自定義路徑
        )
        
        if not is_ok:
            print(f"  ❌ 生成失敗")
            print(f"     原因: {msg}")
            return {
                'success': False,
                'filename': custom_filename,
                'message': msg,
                'total_fixes': 0,
                'regex_fixes': 0,
                'ast_fixes': 0,
            }
        
        # 檢查檔案（使用自定義路徑）
        if not os.path.exists(custom_filepath):
            print(f"  ❌ 檔案未生成: {custom_filename}")
            return {
                'success': False,
                'filename': custom_filename,
                'message': 'File not created',
                'total_fixes': 0,
                'regex_fixes': 0,
                'ast_fixes': 0,
            }
        
        # 動態載入並測試
        spec = importlib.util.spec_from_file_location("temp_skill", custom_filepath)
        temp_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(temp_module)
        
        # 執行 3 次測試
        for i in range(3):
            try:
                item = temp_module.generate()
                assert isinstance(item, dict)
                assert 'question_text' in item
                assert 'answer' in item
            except Exception as e:
                print(f"  ❌ 執行測試 {i+1}/3 失敗: {str(e)}")
                return {
                    'success': False,
                    'filename': custom_filename,
                    'message': f'Runtime error: {str(e)}',
                    'total_fixes': metrics.get('total_fixes', 0),
                    'regex_fixes': metrics.get('regex_fixes', 0),
                    'ast_fixes': metrics.get('ast_fixes', 0),
                }
        
        print(f"  ✅ 生成成功")
        total_fixes = metrics.get('total_fixes', 0)
        print(f"     Healer 修復: {total_fixes} 次")
        if total_fixes > 0:
            print(f"       - Regex: {metrics.get('regex_fixes', 0)}")
            print(f"       - AST: {metrics.get('ast_fixes', 0)}")
        
        return {
            'success': True,
            'filename': custom_filename,
            'message': 'Success',
            'total_fixes': total_fixes,
            'regex_fixes': metrics.get('regex_fixes', 0),
            'ast_fixes': metrics.get('ast_fixes', 0),
        }
        
    except Exception as e:
        print(f"  ❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'filename': custom_filename,
            'message': str(e),
            'total_fixes': 0,
            'regex_fixes': 0,
            'ast_fixes': 0,
        }

def run_ablation_study():
    """執行完整的 Ablation Study - 為每個技能生成 3 個版本（Ab1/Ab2/Ab3）"""
    
    # 先詢問是否重新生成 MASTER_SPEC
    if not ask_regenerate_prompts():
        print("\n❌ 實驗已取消")
        return None
    
    print("\n" + "="*70)
    print("🔬 Healer 價值驗證實驗: 3x Ablation Study")
    print("="*70)
    print("\n📋 實驗設計:")
    for ablation_id, short_name, full_name in ABLATION_CONFIGS:
        print(f"   Ab{ablation_id} ({short_name}): {full_name}")
    print("")
    
    all_results = []
    
    for skill_id, skill_name in TEST_SKILLS:
        print(f"\n" + "="*70)
        print(f"🧪 技能: {skill_name}")
        print(f"   ID: {skill_id}")
        print("="*70)
        
        skill_results = {
            'skill_id': skill_id,
            'skill_name': skill_name,
            'ablations': {}
        }
        
        # 測試所有三個 Ablation 配置
        for ablation_id, short_name, full_name in ABLATION_CONFIGS:
            result = test_with_ablation(
                skill_id, 
                skill_name, 
                ablation_id=ablation_id,
                ablation_name=full_name,
                model_size='14B'
            )
            skill_results['ablations'][ablation_id] = result
        
        # 三方對比分析
        print(f"\n💡 三方對比分析:")
        ab1 = skill_results['ablations'][1]
        ab2 = skill_results['ablations'][2]
        ab3 = skill_results['ablations'][3]
        
        print(f"   Ab1 (Bare):        {'✅ 成功' if ab1['success'] else '❌ 失敗'} - Healer 修復: {ab1['total_fixes']} 次")
        print(f"   Ab2 (MASTER_SPEC): {'✅ 成功' if ab2['success'] else '❌ 失敗'} - Healer 修復: {ab2['total_fixes']} 次")
        print(f"   Ab3 (Full):        {'✅ 成功' if ab3['success'] else '❌ 失敗'} - Healer 修復: {ab3['total_fixes']} 次 (Regex:{ab3['regex_fixes']}, AST:{ab3['ast_fixes']})")
        
        # 分析模式
        success_count = sum(1 for r in [ab1, ab2, ab3] if r['success'])
        healer_fixes_ab3 = ab3['total_fixes']
        
        if success_count == 3:
            if healer_fixes_ab3 > 0:
                print(f"\n   📊 模式: 全部成功，Healer 修復了 {healer_fixes_ab3} 個錯誤")
                print(f"        說明: MASTER_SPEC 可能有隱藏錯誤，Healer 成功修復")
            else:
                print(f"\n   ⚠️  模式: 全部成功且無需 Healer 修復")
                print(f"        說明: 此技能過於簡單，MASTER_SPEC 已足夠")
        elif success_count == 2:
            if ab1['success']:
                print(f"\n   ⚠️  模式: Bare 成功但某些 Healer 配置失敗")
                print(f"        說明: 可能 Healer 有 Bug 導致誤傷")
            else:
                print(f"\n   ✅ 模式: Healer 部分有效")
                print(f"        說明: 需要完整 Healer 才能成功")
        elif success_count == 1:
            if ab3['success']:
                print(f"\n   ✅ 模式: 僅 Full-Healing 成功")
                print(f"        說明: Healer 關鍵且有效！")
            else:
                print(f"\n   ⚠️  模式: 僅部分配置成功")
                print(f"        說明: 技能複雜度適中")
        else:
            print(f"\n   ❌ 模式: 全部失敗")
            print(f"        說明: 技能過於複雜，需要更強的修復機制")
        
        all_results.append(skill_results)
    
    # 總結報告
    print("\n" + "="*70)
    print("📊 總結報告")
    print("="*70)
    
    # 統計各配置的成功率
    total_skills = len(all_results)
    ab1_success = sum(1 for r in all_results if r['ablations'][1]['success'])
    ab2_success = sum(1 for r in all_results if r['ablations'][2]['success'])
    ab3_success = sum(1 for r in all_results if r['ablations'][3]['success'])
    
    print(f"\n成功率對比 (共 {total_skills} 個技能):")
    print(f"  Ab1 (Bare):       {ab1_success}/{total_skills} ({ab1_success/total_skills*100:.0f}%)")
    print(f"  Ab2 (Regex Only): {ab2_success}/{total_skills} ({ab2_success/total_skills*100:.0f}%)")
    print(f"  Ab3 (Full):       {ab3_success}/{total_skills} ({ab3_success/total_skills*100:.0f}%)")
    
    # Healer 修復統計
    total_fixes_ab3 = sum(r['ablations'][3]['total_fixes'] for r in all_results)
    
    print(f"\nHealer 修復統計:")
    print(f"  Ab1 (無 Healer):  總修復 0 次")
    print(f"  Ab2 (無 Healer):  總修復 0 次")
    print(f"  Ab3 (完整 Healer): 總修復 {total_fixes_ab3} 次 (平均 {total_fixes_ab3/total_skills:.1f}/技能)")
    if total_fixes_ab3 > 0:
        avg_regex = sum(r['ablations'][3]['regex_fixes'] for r in all_results) / total_skills
        avg_ast = sum(r['ablations'][3]['ast_fixes'] for r in all_results) / total_skills
        print(f"    - Regex 修復: 平均 {avg_regex:.1f}/技能")
        print(f"    - AST 修復:   平均 {avg_ast:.1f}/技能")
    
    # 生成的檔案清單
    print(f"\n📁 生成的檔案清單:")
    for result in all_results:
        print(f"\n  {result['skill_name']}:")
        for ablation_id in [1, 2, 3]:
            r = result['ablations'][ablation_id]
            status = "✅" if r['success'] else "❌"
            print(f"    {status} {r['filename']}")
    
    # 核心結論
    print(f"\n💡 核心結論:")
    
    improvement_ab2 = ab2_success - ab1_success
    improvement_ab3 = ab3_success - ab1_success
    healer_contribution = ab3_success - ab2_success
    
    if improvement_ab3 > 0:
        print(f"  ✅ Healer 顯著提升成功率:")
        print(f"     Bare → MASTER_SPEC:   +{improvement_ab2} 個技能 ({improvement_ab2/total_skills*100:+.0f}%) - Prompt 工程化貢獻")
        print(f"     MASTER_SPEC → Full:    +{healer_contribution} 個技能 ({healer_contribution/total_skills*100:+.0f}%) - Healer 獨立貢獻 ⭐")
        print(f"     Bare → Full:          +{improvement_ab3} 個技能 ({improvement_ab3/total_skills*100:+.0f}%) - 完整系統貢獻")
        print(f"     Healer 修復總數:     {total_fixes_ab3} 次")
        print(f"     ✨ 實驗設計有效！Healer 的價值得到證明！")
    elif ab1_success == ab3_success == total_skills:
        if total_fixes_ab3 > 0:
            print(f"  ⚠️  成功率相同但 Healer 有修復:")
            print(f"     說明: MASTER_SPEC 可能生成有隱藏錯誤的代碼")
            print(f"     Healer 修復了 {total_fixes_ab3} 個潛在問題")
            print(f"     🔍 建議: 深入分析修復的具體內容")
        else:
            print(f"  ⚠️  警告: 這些技能過於簡單，不需要 Healer")
            print(f"     建議: 測試更複雜的技能（如分數四則運算、方程式）")
    else:
        print(f"  ❌ 異常: Full-Healing 成功率未提升或下降")
        print(f"     可能原因: Healer 有 Bug，導致誤傷正常代碼")
        print(f"     🐛 需要檢查 Healer 的實作")
    
    return all_results

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        results = run_ablation_study()
        sys.exit(0)
