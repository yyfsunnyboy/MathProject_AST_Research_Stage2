# -*- coding: utf-8 -*-
"""
批次實驗執行器
為指定技能執行多次生成實驗，並儲存結果到 experiments/results/

使用方式:
    # 為單一技能執行 100 次實驗（所有 Ablation）
    python scripts/run_batch_experiment.py --skill gh_ApplicationsOfDerivatives --samples 100
    
    # 只執行特定 Ablation
    python scripts/run_batch_experiment.py --skill gh_ApplicationsOfDerivatives --samples 100 --ablations 2,3
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, os.path.abspath('.'))

from core.code_generator import CodeGenerator
from core.prompts.prompt_builder import PromptBuilder
from utils.init_db import get_all_master_specs

def ensure_experiment_dirs(skill_id, ablation_id):
    """確保實驗目錄存在"""
    base_dir = Path(f"experiments/results/{skill_id}/Ab{ablation_id}")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def save_sample(skill_id, ablation_id, sample_num, code, metadata, validation):
    """
    儲存單一樣本的程式碼和評測報告
    
    Args:
        skill_id: 技能 ID
        ablation_id: Ablation ID
        sample_num: 樣本編號
        code: 生成的程式碼
        metadata: 生成 metadata
        validation: 驗證結果
    """
    output_dir = ensure_experiment_dirs(skill_id, ablation_id)
    
    # 儲存程式碼
    code_file = output_dir / f"sample_{sample_num}.py"
    with open(code_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    # 建立評測報告
    report = {
        "sample_id": sample_num,
        "skill_id": skill_id,
        "ablation_id": ablation_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata,
        "validation": validation,
        "file_path": str(code_file.relative_to("experiments/results"))
    }
    
    # 儲存報告
    json_file = output_dir / f"sample_{sample_num}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return code_file, json_file

def run_single_experiment(skill_id, ablation_id, sample_num, master_spec, topic):
    """
    執行單次實驗
    
    Returns:
        dict: {
            'success': bool,
            'code_file': Path or None,
            'json_file': Path or None,
            'metadata': dict,
            'validation': dict
        }
    """
    try:
        # 準備 Prompt
        textbook_example = f"""範例：已知 f(x) = 3x³ - 5x² + 2，求 f'(x) 與 f''(x) 的值。
答案：9x² - 10x, 18x - 10"""
        
        prompt = PromptBuilder.build(
            master_spec=master_spec,
            ablation_id=ablation_id,
            textbook_example=textbook_example,
            topic=topic,
            skill_id=skill_id
        )
        
        # 生成代碼
        generator = CodeGenerator(model_name="qwen2.5-coder:14b")
        
        result = generator.generate_skill_file(
            skill_id=skill_id,
            prompt=prompt,
            ablation_id=ablation_id,
            enable_basic_cleanup=(ablation_id >= 2),
            enable_advanced_healer=(ablation_id >= 3)
        )
        
        # 提取 metadata 和驗證結果
        metadata = {
            "model": result.get('model', 'qwen2.5-coder:14b'),
            "tokens_in": result.get('tokens_in', 0),
            "tokens_out": result.get('tokens_out', 0),
            "generation_time": result.get('generation_time', 0),
            "strategy": result.get('strategy', 'Unknown')
        }
        
        validation = {
            "syntax_valid": result.get('syntax_valid', False),
            "has_while_true": result.get('has_while_true', False),
            "has_generate_function": result.get('has_generate_function', False),
            "verification_status": result.get('verification_status', 'UNKNOWN')
        }
        
        # 儲存結果
        code_file, json_file = save_sample(
            skill_id, ablation_id, sample_num,
            result['code'], metadata, validation
        )
        
        return {
            'success': True,
            'code_file': code_file,
            'json_file': json_file,
            'metadata': metadata,
            'validation': validation
        }
        
    except Exception as e:
        print(f"   ❌ 生成失敗: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_batch_for_ablation(skill_id, ablation_id, num_samples, master_spec, topic):
    """為單一 Ablation 執行批次實驗"""
    ablation_name = {1: "Ab1 (Bare)", 2: "Ab2 (Engineered)", 3: "Ab3 (Healer)"}[ablation_id]
    
    print(f"\n{'='*80}")
    print(f"📊 {ablation_name} - 開始批次生成")
    print(f"{'='*80}\n")
    
    success_count = 0
    failed_count = 0
    
    for i in range(1, num_samples + 1):
        print(f"🔄 樣本 {i}/{num_samples}...", end=' ', flush=True)
        
        result = run_single_experiment(skill_id, ablation_id, i, master_spec, topic)
        
        if result['success']:
            success_count += 1
            print(f"✅ 成功")
        else:
            failed_count += 1
            print(f"❌ 失敗")
    
    print(f"\n{'='*80}")
    print(f"✅ 成功: {success_count}/{num_samples}")
    print(f"❌ 失敗: {failed_count}/{num_samples}")
    print(f"成功率: {success_count/num_samples*100:.1f}%")
    print(f"{'='*80}\n")
    
    return success_count, failed_count

def main():
    parser = argparse.ArgumentParser(description='執行批次實驗')
    parser.add_argument('--skill', type=str, required=True, help='技能 ID')
    parser.add_argument('--samples', type=int, default=100, help='每個 Ablation 的樣本數量 (預設: 100)')
    parser.add_argument('--ablations', type=str, default='1,2,3', help='要執行的 Ablation IDs (預設: 1,2,3)')
    
    args = parser.parse_args()
    
    # 解析 Ablation IDs
    ablation_ids = [int(x.strip()) for x in args.ablations.split(',')]
    
    # 取得 MASTER_SPEC
    master_specs = get_all_master_specs()
    
    if args.skill not in master_specs:
        print(f"❌ 找不到技能: {args.skill}")
        return
    
    master_spec = master_specs[args.skill]['spec_text']
    topic = master_specs[args.skill].get('topic', '數學題目')
    
    print(f"\n{'='*80}")
    print(f"🚀 批次實驗開始")
    print(f"{'='*80}")
    print(f"技能: {args.skill}")
    print(f"樣本數量: {args.samples} 每個 Ablation")
    print(f"Ablation 組別: {ablation_ids}")
    print(f"{'='*80}\n")
    
    total_success = 0
    total_failed = 0
    
    for ablation_id in ablation_ids:
        success, failed = run_batch_for_ablation(
            args.skill, ablation_id, args.samples, master_spec, topic
        )
        total_success += success
        total_failed += failed
    
    print(f"\n{'='*80}")
    print(f"🎉 所有實驗完成！")
    print(f"{'='*80}")
    print(f"總成功: {total_success}/{args.samples * len(ablation_ids)}")
    print(f"總失敗: {total_failed}/{args.samples * len(ablation_ids)}")
    print(f"整體成功率: {total_success/(args.samples * len(ablation_ids))*100:.1f}%")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
