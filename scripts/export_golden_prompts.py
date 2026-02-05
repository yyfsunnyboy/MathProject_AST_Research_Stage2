# -*- coding: utf-8 -*-
"""
Golden Prompts 匯出工具
將當前的 Prompt 模板匯出為靜態檔案，供實驗使用

使用方式:
    python scripts/export_golden_prompts.py --skill gh_ApplicationsOfDerivatives
    python scripts/export_golden_prompts.py --all  # 匯出所有技能
"""

import sys
import os
import argparse
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.abspath('.'))

from core.prompts.prompt_builder import PromptBuilder
from utils.init_db import get_all_master_specs

def export_prompt_to_file(skill_id, ablation_id, output_dir):
    """
    匯出指定技能和 Ablation 的 Prompt 到檔案
    
    Args:
        skill_id: 技能 ID
        ablation_id: Ablation ID (1, 2, 3)
        output_dir: 輸出目錄
    """
    # 從資料庫取得 MASTER_SPEC
    master_specs = get_all_master_specs()
    
    if skill_id not in master_specs:
        print(f"❌ 找不到技能: {skill_id}")
        return False
    
    master_spec = master_specs[skill_id]['spec_text']
    topic = master_specs[skill_id].get('topic', '數學題目')
    
    # 準備課本範例（Ab1 需要）
    textbook_example = f"""範例：已知 f(x) = 3x³ - 5x² + 2，求 f'(x) 與 f''(x) 的值。
答案：9x² - 10x, 18x - 10"""
    
    # 生成 Prompt
    try:
        prompt = PromptBuilder.build(
            master_spec=master_spec,
            ablation_id=ablation_id,
            textbook_example=textbook_example,
            topic=topic,
            skill_id=skill_id
        )
    except Exception as e:
        print(f"❌ 生成 Prompt 失敗: {e}")
        return False
    
    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 儲存到檔案
    filename = f"{skill_id}_Ab{ablation_id}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        # 寫入標頭資訊
        f.write(f"# ============================================================================\n")
        f.write(f"# Golden Prompt - {skill_id} (Ablation {ablation_id})\n")
        f.write(f"# 匯出時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# ============================================================================\n")
        f.write(f"\n")
        f.write(prompt)
    
    # 顯示統計資訊
    char_count = len(prompt)
    line_count = prompt.count('\n') + 1
    
    print(f"✅ 已匯出: {filepath}")
    print(f"   - 字符數: {char_count:,}")
    print(f"   - 行數: {line_count:,}")
    
    return True

def export_all_ablations(skill_id, output_dir):
    """匯出指定技能的所有 Ablation Prompts"""
    print(f"\n{'='*80}")
    print(f"匯出技能: {skill_id}")
    print(f"{'='*80}\n")
    
    success_count = 0
    
    for ablation_id in [1, 2, 3]:
        ablation_name = {1: "Ab1 (Bare)", 2: "Ab2 (Engineered)", 3: "Ab3 (Healer)"}[ablation_id]
        print(f"\n📝 {ablation_name}")
        print("-" * 40)
        
        if export_prompt_to_file(skill_id, ablation_id, output_dir):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ 成功匯出: {success_count}/3 個 Prompts")
    print(f"{'='*80}\n")
    
    return success_count == 3

def main():
    parser = argparse.ArgumentParser(description='匯出 Golden Prompts 到靜態檔案')
    parser.add_argument('--skill', type=str, help='技能 ID (例: gh_ApplicationsOfDerivatives)')
    parser.add_argument('--all', action='store_true', help='匯出所有技能')
    parser.add_argument('--output', type=str, default='experiments/golden_prompts',
                       help='輸出目錄 (預設: experiments/golden_prompts)')
    
    args = parser.parse_args()
    
    if not args.skill and not args.all:
        parser.error("請指定 --skill 或 --all")
    
    output_dir = args.output
    
    if args.all:
        # 取得所有技能
        master_specs = get_all_master_specs()
        skills = list(master_specs.keys())
        
        print(f"\n🔍 找到 {len(skills)} 個技能")
        print(f"輸出目錄: {output_dir}\n")
        
        total_success = 0
        for skill_id in skills:
            if export_all_ablations(skill_id, output_dir):
                total_success += 1
        
        print(f"\n{'='*80}")
        print(f"🎉 完成！成功匯出 {total_success}/{len(skills)} 個技能")
        print(f"{'='*80}\n")
    else:
        # 匯出單一技能
        export_all_ablations(args.skill, output_dir)

if __name__ == '__main__':
    main()
