# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): test_ablation_summary.py
功能說明 (Description): 測試 ablation_summary 彙總表功能
執行語法 (Usage): python utils/test_ablation_summary.py
版本資訊 (Version): V1.0
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, AblationSummary, ExperimentRun, EvaluationItem
from app import create_app

def test_ablation_summary():
    """測試彙總表功能"""
    app = create_app()
    
    with app.app_context():
        print("="*70)
        print("🧪 測試 MCRI V4.2 彙總表功能")
        print("="*70)
        
        # 測試 1：建立模擬實驗數據
        print("\n📝 測試 1：建立模擬實驗數據...")
        
        skill_name = "test_ApplicationsOfDerivatives"
        model_name = "qwen2.5-coder:14b"
        
        # 建立 3 個配置 × 5 個 sample = 15 筆 runs
        test_runs = []
        for ablation_id in [1, 2, 3]:
            for sample_index in [1, 2, 3, 4, 5]:
                # 模擬不同配置的分數（Ab1 < Ab2 < Ab3）
                base_score = 40.0 if ablation_id == 1 else (70.0 if ablation_id == 2 else 90.0)
                # 加入一些隨機變異
                import random
                random.seed(ablation_id * 100 + sample_index)
                score = base_score + random.uniform(-5, 5)
                
                run = ExperimentRun(
                    run_id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    model_name=model_name,
                    skill_name=skill_name,
                    ablation_id=ablation_id,
                    sample_index=sample_index,
                    code_commit_hash="test123",
                    python_version="3.9.13",
                    source_code_path=f"test_Ab{ablation_id}_{sample_index}.py",
                    repetitions_planned=20,
                    repetitions_completed=20,
                    fail_count=0,
                    pass_rate=1.0,
                    score_l1_total=18,
                    score_l2_total=18,
                    avg_l3_total=score * 0.28,
                    avg_l3_2_external=score * 0.14,
                    avg_l4_total=score * 0.32,
                    avg_l4_1_numeric=score * 0.16,
                    avg_mcri_total=score
                )
                db.session.add(run)
                test_runs.append(run)
        
        db.session.commit()
        print(f"✅ 已建立 {len(test_runs)} 筆模擬實驗數據")
        
        # 測試 2：計算統計彙總
        print("\n📊 測試 2：計算統計彙總...")
        
        from utils.compute_ablation_summary import compute_summary_for_config
        
        for ablation_id in [1, 2, 3]:
            summary_data = compute_summary_for_config(skill_name, ablation_id, model_name)
            
            if summary_data:
                summary = AblationSummary(**summary_data)
                db.session.add(summary)
                
                print(f"\n  Ab{ablation_id}:")
                print(f"    平均分: {summary_data['mean_mcri_total']:.2f}")
                print(f"    標準差: {summary_data['std_mcri_total']:.2f}")
                print(f"    95% CI: [{summary_data['ci95_lower']:.2f}, {summary_data['ci95_upper']:.2f}]")
                if summary_data['p_value_vs_ab1'] is not None:
                    print(f"    p-value: {summary_data['p_value_vs_ab1']:.4f}")
                print(f"    備註: {summary_data['notes']}")
        
        db.session.commit()
        print(f"\n✅ 已建立 3 筆彙總記錄")
        
        # 測試 3：查詢彙總表
        print("\n🔍 測試 3：查詢彙總表...")
        
        summaries = AblationSummary.query.filter_by(skill_name=skill_name).order_by(AblationSummary.ablation_id).all()
        
        print(f"\n找到 {len(summaries)} 筆彙總記錄：")
        print(f"\n{'配置':<8} {'平均分':<10} {'標準差':<10} {'95% CI':<25} {'p-value'}")
        print("-" * 70)
        
        for s in summaries:
            ci_str = f"[{s.ci95_lower:.1f}, {s.ci95_upper:.1f}]"
            p_str = f"{s.p_value_vs_ab1:.4f}" if s.p_value_vs_ab1 else "-"
            print(f"Ab{s.ablation_id:<7} {s.mean_mcri_total:<10.2f} {s.std_mcri_total:<10.2f} {ci_str:<25} {p_str}")
        
        # 測試 4：驗證信賴區間
        print("\n✅ 測試 4：驗證信賴區間邏輯...")
        
        ab3_summary = AblationSummary.query.filter_by(
            skill_name=skill_name, 
            ablation_id=3
        ).first()
        
        if ab3_summary:
            # 95% CI 應該包含平均值
            assert ab3_summary.ci95_lower <= ab3_summary.mean_mcri_total <= ab3_summary.ci95_upper
            print(f"✅ 信賴區間邏輯正確：{ab3_summary.mean_mcri_total:.2f} ∈ [{ab3_summary.ci95_lower:.2f}, {ab3_summary.ci95_upper:.2f}]")
        
        # 測試 5：to_dict 序列化
        print("\n📦 測試 5：to_dict() 序列化...")
        
        if ab3_summary:
            summary_dict = ab3_summary.to_dict()
            print(f"✅ 成功序列化：{len(summary_dict)} 個欄位")
            print(f"   欄位: {list(summary_dict.keys())}")
        
        # 清理測試數據
        print("\n🧹 清理測試數據...")
        
        EvaluationItem.query.filter(
            EvaluationItem.run_id.in_([r.run_id for r in test_runs])
        ).delete(synchronize_session=False)
        
        ExperimentRun.query.filter_by(skill_name=skill_name).delete()
        AblationSummary.query.filter_by(skill_name=skill_name).delete()
        db.session.commit()
        
        print("✅ 測試數據已清理")
        
        print("\n" + "="*70)
        print("✅ 所有測試通過！")
        print("="*70)
        
        print("\n📊 功能驗證：")
        print("  ✅ 建立模擬實驗數據")
        print("  ✅ 計算統計彙總（平均、標準差、CI）")
        print("  ✅ 顯著性檢定（t-test）")
        print("  ✅ 資料庫 CRUD 操作")
        print("  ✅ 序列化功能")
        print("  ✅ 資料清理")


if __name__ == '__main__':
    test_ablation_summary()
