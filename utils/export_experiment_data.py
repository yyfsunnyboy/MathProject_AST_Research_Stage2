# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): export_experiment_data.py
功能說明 (Description): 匯出 MCRI V4.2 實驗資料到 CSV 格式
執行語法 (Usage): python utils/export_experiment_data.py [--output-dir reports/]
版本資訊 (Version): V1.0
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import os
import csv
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加父目錄到路徑
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ExperimentRun, EvaluationItem


def export_to_csv(db_path='instance/math_education.db', output_dir='reports'):
    """
    匯出實驗資料到 CSV
    
    Args:
        db_path: 資料庫檔案路徑
        output_dir: 輸出目錄
    
    Returns:
        tuple: (主表檔名, 附表檔名)
    """
    # 建立資料庫連線
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 建立輸出目錄
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 產生時間戳記檔名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    runs_filename = f'experiment_runs_{timestamp}.csv'
    items_filename = f'evaluation_items_{timestamp}.csv'
    
    runs_path = output_path / runs_filename
    items_path = output_path / items_filename
    
    # =================================================================
    # 匯出主表：experiment_runs
    # =================================================================
    print(f"📊 匯出主表到: {runs_path}")
    
    runs = session.query(ExperimentRun).order_by(ExperimentRun.timestamp.desc()).all()
    
    if not runs:
        print("⚠️ 資料庫中沒有實驗記錄！")
        session.close()
        return None, None
    
    # 定義欄位順序（與資料表設計對應）
    runs_fieldnames = [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'code_commit_hash', 'python_version', 'model_temperature',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual',
        'avg_mcri_total', 'source_code_path', 'mcri_version', 'notes'
    ]
    
    with open(runs_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=runs_fieldnames)
        writer.writeheader()
        
        for run in runs:
            row = run.to_dict()
            writer.writerow(row)
    
    print(f"✅ 匯出 {len(runs)} 筆主表記錄")
    
    # =================================================================
    # 匯出附表：evaluation_items
    # =================================================================
    print(f"\n📊 匯出附表到: {items_path}")
    
    items = session.query(EvaluationItem).join(ExperimentRun).order_by(
        ExperimentRun.timestamp.desc(),
        EvaluationItem.repetition_index
    ).all()
    
    # 定義欄位順序
    items_fieldnames = [
        'item_id', 'run_id', 'repetition_index',
        'generated_question', 'generated_answer', 'generated_correct_answer',
        'status', 'error_log', 'exec_time_ms', 'included_in_avg',
        'score_l3_total', 'score_l3_1_internal', 'score_l3_2_external',
        'score_l4_total', 'score_l4_1_numeric', 'score_l4_2_visual',
        'student_input_test', 'student_input_result'
    ]
    
    with open(items_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=items_fieldnames)
        writer.writeheader()
        
        for item in items:
            row = item.to_dict()
            writer.writerow(row)
    
    print(f"✅ 匯出 {len(items)} 筆附表記錄")
    
    # =================================================================
    # 統計摘要
    # =================================================================
    print("\n" + "="*70)
    print("📈 資料摘要")
    print("="*70)
    
    # 按配置統計
    from sqlalchemy import func
    stats = session.query(
        ExperimentRun.ablation_id,
        func.count(ExperimentRun.run_id).label('count'),
        func.avg(ExperimentRun.avg_mcri_total).label('avg_mcri'),
        func.avg(ExperimentRun.pass_rate).label('avg_pass_rate')
    ).group_by(ExperimentRun.ablation_id).all()
    
    ablation_names = {1: 'Ab1 (Bare)', 2: 'Ab2 (Eng)', 3: 'Ab3 (Healer)'}
    
    print(f"\n{'配置':<20} {'實驗次數':<10} {'平均MCRI':<12} {'平均通過率':<12}")
    print("-" * 70)
    for stat in stats:
        ab_name = ablation_names.get(stat.ablation_id, f'Ab{stat.ablation_id}')
        avg_mcri = stat.avg_mcri if stat.avg_mcri else 0
        avg_pass = stat.avg_pass_rate if stat.avg_pass_rate else 0
        print(f"{ab_name:<20} {stat.count:<10} {avg_mcri:<12.1f} {avg_pass*100:<11.1f}%")
    
    session.close()
    
    print("\n✅ 匯出完成！")
    print(f"📁 主表: {runs_path}")
    print(f"📁 附表: {items_path}")
    
    return runs_filename, items_filename


def main():
    parser = argparse.ArgumentParser(description='匯出 MCRI V4.2 實驗資料到 CSV')
    parser.add_argument('--db-path', default='instance/math_education.db', help='資料庫檔案路徑')
    parser.add_argument('--output-dir', default='reports', help='輸出目錄')
    
    args = parser.parse_args()
    
    export_to_csv(db_path=args.db_path, output_dir=args.output_dir)


if __name__ == '__main__':
    main()
