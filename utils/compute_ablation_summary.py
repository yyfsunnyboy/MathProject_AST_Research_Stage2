# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): compute_ablation_summary.py
功能說明 (Description): 計算 MCRI V4.2 實驗的統計彙總（信賴區間、顯著性檢定）
執行語法 (Usage): python utils/compute_ablation_summary.py [--skill <skill_name>]
版本資訊 (Version): V1.0
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import sys
import os
import uuid
import argparse
import numpy as np
from scipy import stats
from datetime import datetime

# 確保可以導入專案模組
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, ExperimentRun, AblationSummary
from app import create_app

def compute_summary_for_config(skill_name, ablation_id, model_name='qwen2.5-coder:14b'):
    """
    計算特定技能 × 配置的統計彙總
    
    Args:
        skill_name: 技能名稱
        ablation_id: 配置 ID (1=Bare, 2=Eng, 3=Healer)
        model_name: 模型名稱
    
    Returns:
        dict: 統計彙總數據
    """
    # 1. 查詢同一技能、同一配置的所有 sample（預期 5 筆）
    runs = ExperimentRun.query.filter_by(
        skill_name=skill_name,
        ablation_id=ablation_id,
        model_name=model_name
    ).all()
    
    if not runs:
        print(f"⚠️  警告：未找到 {skill_name} Ab{ablation_id} 的實驗數據")
        return None
    
    if len(runs) < 5:
        print(f"⚠️  警告：{skill_name} Ab{ablation_id} 只有 {len(runs)} 筆樣本（少於預期的 5 筆）")
    
    # 2. 提取 avg_mcri_total（5 個值）
    mcri_scores = [run.avg_mcri_total for run in runs if run.avg_mcri_total is not None]
    l3_external_scores = [run.avg_l3_2_external for run in runs if run.avg_l3_2_external is not None]
    l4_numeric_scores = [run.avg_l4_1_numeric for run in runs if run.avg_l4_1_numeric is not None]
    
    if not mcri_scores:
        print(f"⚠️  警告：{skill_name} Ab{ablation_id} 沒有有效的 MCRI 分數")
        return None
    
    # 3. 計算統計量
    mean_mcri = float(np.mean(mcri_scores))
    std_mcri = float(np.std(mcri_scores, ddof=1)) if len(mcri_scores) > 1 else 0.0
    
    # 4. 計算 95% 信賴區間（t 分布）
    if len(mcri_scores) > 1:
        confidence = 0.95
        df = len(mcri_scores) - 1  # 自由度
        sem = stats.sem(mcri_scores)  # 標準誤
        ci = stats.t.interval(confidence, df, loc=mean_mcri, scale=sem)
        ci95_lower = float(ci[0])
        ci95_upper = float(ci[1])
    else:
        ci95_lower = mean_mcri
        ci95_upper = mean_mcri
    
    # 5. 計算關鍵維度統計
    mean_l3_external = float(np.mean(l3_external_scores)) if l3_external_scores else None
    mean_l4_numeric = float(np.mean(l4_numeric_scores)) if l4_numeric_scores else None
    
    # 6. 顯著性檢定（vs Ab1）
    p_value = None
    notes = "-"
    
    if ablation_id > 1:
        # 查詢 Ab1 的數據
        ab1_runs = ExperimentRun.query.filter_by(
            skill_name=skill_name,
            ablation_id=1,
            model_name=model_name
        ).all()
        
        ab1_scores = [run.avg_mcri_total for run in ab1_runs if run.avg_mcri_total is not None]
        
        if ab1_scores and len(ab1_scores) > 1 and len(mcri_scores) > 1:
            # 執行獨立樣本 t-test（雙尾檢定）
            t_stat, p_val = stats.ttest_ind(mcri_scores, ab1_scores)
            p_value = float(p_val)
            
            # 生成備註
            if p_value < 0.001:
                sig = "p<0.001 (高度顯著)"
            elif p_value < 0.01:
                sig = "p<0.01 (顯著)"
            elif p_value < 0.05:
                sig = "p<0.05 (邊緣顯著)"
            else:
                sig = f"p={p_value:.3f} (無顯著差異)"
            
            diff = mean_mcri - np.mean(ab1_scores)
            notes = f"Ab{ablation_id} vs Ab1: {sig}, Δ={diff:+.1f}"
    
    # 7. 返回統計彙總
    return {
        'summary_id': str(uuid.uuid4()),
        'skill_name': skill_name,
        'ablation_id': ablation_id,
        'model_name': model_name,
        'sample_count': len(mcri_scores),
        'total_runs': len(mcri_scores) * 20,  # 假設每個 sample 有 20 次重複
        'mean_mcri_total': mean_mcri,
        'std_mcri_total': std_mcri,
        'ci95_lower': ci95_lower,
        'ci95_upper': ci95_upper,
        'mean_l3_external': mean_l3_external,
        'mean_l4_numeric': mean_l4_numeric,
        'p_value_vs_ab1': p_value,
        'notes': notes
    }


def compute_all_summaries(skill_names=None, model_name='qwen2.5-coder:14b'):
    """
    計算所有技能 × 配置的統計彙總
    
    Args:
        skill_names: 技能名稱列表（None = 計算所有技能）
        model_name: 模型名稱
    """
    app = create_app()
    
    with app.app_context():
        # 如果未指定技能，則查詢資料庫中所有技能
        if skill_names is None:
            distinct_skills = db.session.query(ExperimentRun.skill_name).distinct().all()
            skill_names = [skill[0] for skill in distinct_skills]
        
        print(f"🔄 開始計算統計彙總...")
        print(f"📊 技能數量: {len(skill_names)}")
        print(f"⚙️  配置數量: 3 (Ab1, Ab2, Ab3)")
        print(f"📈 預期生成: {len(skill_names) * 3} 筆彙總記錄\n")
        
        created_count = 0
        updated_count = 0
        
        for skill_name in skill_names:
            print(f"\n處理技能: {skill_name}")
            print("=" * 60)
            
            for ablation_id in [1, 2, 3]:
                # 計算統計數據
                summary_data = compute_summary_for_config(skill_name, ablation_id, model_name)
                
                if summary_data is None:
                    continue
                
                # 檢查是否已存在
                existing = AblationSummary.query.filter_by(
                    skill_name=skill_name,
                    ablation_id=ablation_id,
                    model_name=model_name
                ).first()
                
                if existing:
                    # 更新現有記錄
                    for key, value in summary_data.items():
                        if key != 'summary_id':  # 不更新 ID
                            setattr(existing, key, value)
                    updated_count += 1
                    print(f"  ✅ Ab{ablation_id}: 更新 | μ={summary_data['mean_mcri_total']:.1f}±{summary_data['std_mcri_total']:.1f}, "
                          f"CI=[{summary_data['ci95_lower']:.1f}, {summary_data['ci95_upper']:.1f}]")
                else:
                    # 建立新記錄
                    summary = AblationSummary(**summary_data)
                    db.session.add(summary)
                    created_count += 1
                    print(f"  ✅ Ab{ablation_id}: 新增 | μ={summary_data['mean_mcri_total']:.1f}±{summary_data['std_mcri_total']:.1f}, "
                          f"CI=[{summary_data['ci95_lower']:.1f}, {summary_data['ci95_upper']:.1f}]")
                
                # 顯示備註
                if summary_data['notes'] != "-":
                    print(f"     📝 {summary_data['notes']}")
        
        # 提交所有變更
        try:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"✅ 統計彙總完成！")
            print(f"📊 新增記錄: {created_count} 筆")
            print(f"🔄 更新記錄: {updated_count} 筆")
            print(f"📈 總計: {created_count + updated_count} 筆")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 錯誤：提交資料庫失敗 - {e}")
            raise


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='計算 MCRI V4.2 實驗統計彙總')
    parser.add_argument('--skill', type=str, help='指定技能名稱（不指定則計算所有技能）')
    parser.add_argument('--model', type=str, default='qwen2.5-coder:14b', help='模型名稱')
    
    args = parser.parse_args()
    
    skill_names = [args.skill] if args.skill else None
    
    compute_all_summaries(skill_names, args.model)


if __name__ == '__main__':
    main()
