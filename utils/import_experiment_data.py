# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): import_experiment_data.py
功能說明 (Description): 從 CSV 匯入 MCRI V4.2 實驗資料到資料庫
執行語法 (Usage): python utils/import_experiment_data.py --runs <主表.csv> --items <附表.csv>
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

from models import db, ExperimentRun, EvaluationItem


def import_from_csv(runs_csv, items_csv, db_path='instance/math_education.db', skip_duplicates=True):
    """
    從 CSV 匯入實驗資料
    
    Args:
        runs_csv: 主表 CSV 檔案路徑
        items_csv: 附表 CSV 檔案路徑
        db_path: 資料庫檔案路徑
        skip_duplicates: 是否跳過重複的 run_id（True）或覆蓋（False）
    
    Returns:
        tuple: (成功匯入主表數, 成功匯入附表數)
    """
    # 建立資料庫連線
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 確保資料表存在
    db.metadata.create_all(engine)
    
    runs_imported = 0
    items_imported = 0
    runs_skipped = 0
    items_skipped = 0
    
    # =================================================================
    # 匯入主表：experiment_runs
    # =================================================================
    print(f"📥 匯入主表: {runs_csv}")
    
    with open(runs_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            run_id = row['run_id']
            
            # 檢查是否已存在
            existing = session.query(ExperimentRun).filter_by(run_id=run_id).first()
            
            if existing and skip_duplicates:
                runs_skipped += 1
                continue
            elif existing:
                # 覆蓋模式：刪除舊記錄（會自動刪除關聯的 items）
                session.delete(existing)
            
            # 建立新記錄
            run = ExperimentRun(
                run_id=run_id,
                timestamp=datetime.fromisoformat(row['timestamp']) if row.get('timestamp') else None,
                model_name=row['model_name'],
                skill_name=row['skill_name'],
                ablation_id=int(row['ablation_id']),
                sample_index=int(row['sample_index']),
                code_commit_hash=row['code_commit_hash'],
                python_version=row['python_version'],
                mcri_version=row.get('mcri_version', 'V4.2'),
                model_temperature=float(row['model_temperature']) if row.get('model_temperature') else 0.7,
                repetitions_planned=int(row['repetitions_planned']) if row.get('repetitions_planned') else 20,
                repetitions_completed=int(row['repetitions_completed']) if row.get('repetitions_completed') else 0,
                fail_count=int(row['fail_count']) if row.get('fail_count') else 0,
                pass_rate=float(row['pass_rate']) if row.get('pass_rate') else None,
                avg_exec_time=float(row['avg_exec_time']) if row.get('avg_exec_time') else None,
                score_l1_total=int(row['score_l1_total']) if row.get('score_l1_total') else None,
                score_l1_1_syntax=int(row['score_l1_1_syntax']) if row.get('score_l1_1_syntax') else None,
                score_l1_2_runtime=int(row['score_l1_2_runtime']) if row.get('score_l1_2_runtime') else None,
                score_l2_total=int(row['score_l2_total']) if row.get('score_l2_total') else None,
                score_l2_1_contract=int(row['score_l2_1_contract']) if row.get('score_l2_1_contract') else None,
                score_l2_2_purity=int(row['score_l2_2_purity']) if row.get('score_l2_2_purity') else None,
                avg_l3_total=float(row['avg_l3_total']) if row.get('avg_l3_total') else None,
                avg_l3_1_internal=float(row['avg_l3_1_internal']) if row.get('avg_l3_1_internal') else None,
                avg_l3_2_external=float(row['avg_l3_2_external']) if row.get('avg_l3_2_external') else None,
                avg_l4_total=float(row['avg_l4_total']) if row.get('avg_l4_total') else None,
                avg_l4_1_numeric=float(row['avg_l4_1_numeric']) if row.get('avg_l4_1_numeric') else None,
                avg_l4_2_visual=float(row['avg_l4_2_visual']) if row.get('avg_l4_2_visual') else None,
                avg_mcri_total=float(row['avg_mcri_total']) if row.get('avg_mcri_total') else None,
                source_code_path=row['source_code_path'],
                notes=row.get('notes')
            )
            
            session.add(run)
            runs_imported += 1
    
    # 提交主表
    session.commit()
    print(f"✅ 匯入 {runs_imported} 筆主表記錄（跳過 {runs_skipped} 筆重複）")
    
    # =================================================================
    # 匯入附表：evaluation_items
    # =================================================================
    print(f"\n📥 匯入附表: {items_csv}")
    
    with open(items_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            item_id = row['item_id']
            run_id = row['run_id']
            
            # 檢查主表是否存在
            run_exists = session.query(ExperimentRun).filter_by(run_id=run_id).first()
            if not run_exists:
                print(f"⚠️ 跳過 item {item_id}：找不到對應的 run_id {run_id}")
                items_skipped += 1
                continue
            
            # 檢查是否已存在
            existing = session.query(EvaluationItem).filter_by(item_id=item_id).first()
            
            if existing and skip_duplicates:
                items_skipped += 1
                continue
            elif existing:
                session.delete(existing)
            
            # 建立新記錄
            item = EvaluationItem(
                item_id=item_id,
                run_id=run_id,
                repetition_index=int(row['repetition_index']),
                generated_question=row.get('generated_question'),
                generated_answer=row.get('generated_answer'),
                generated_correct_answer=row.get('generated_correct_answer'),
                status=row['status'],
                error_log=row.get('error_log'),
                exec_time_ms=float(row['exec_time_ms']) if row.get('exec_time_ms') else None,
                included_in_avg=row.get('included_in_avg', '1').lower() in ('1', 'true', 'yes'),  # 支援多種格式
                score_l3_total=int(row['score_l3_total']) if row.get('score_l3_total') else None,
                score_l3_1_internal=int(row['score_l3_1_internal']) if row.get('score_l3_1_internal') else None,
                score_l3_2_external=int(row['score_l3_2_external']) if row.get('score_l3_2_external') else None,
                score_l4_total=int(row['score_l4_total']) if row.get('score_l4_total') else None,
                score_l4_1_numeric=int(row['score_l4_1_numeric']) if row.get('score_l4_1_numeric') else None,
                score_l4_2_visual=int(row['score_l4_2_visual']) if row.get('score_l4_2_visual') else None,
                student_input_test=row.get('student_input_test'),
                student_input_result=row.get('student_input_result')
            )
            
            session.add(item)
            items_imported += 1
    
    # 提交附表
    session.commit()
    print(f"✅ 匯入 {items_imported} 筆附表記錄（跳過 {items_skipped} 筆）")
    
    # =================================================================
    # 驗證資料完整性
    # =================================================================
    print("\n" + "="*70)
    print("🔍 驗證資料完整性")
    print("="*70)
    
    total_runs = session.query(ExperimentRun).count()
    total_items = session.query(EvaluationItem).count()
    
    print(f"✅ 主表總筆數: {total_runs}")
    print(f"✅ 附表總筆數: {total_items}")
    
    # 檢查孤立的 items（沒有對應 run）
    orphan_items = session.query(EvaluationItem).outerjoin(ExperimentRun).filter(
        ExperimentRun.run_id == None
    ).count()
    
    if orphan_items > 0:
        print(f"⚠️ 發現 {orphan_items} 筆孤立的附表記錄（沒有對應的主表）")
    
    session.close()
    
    print("\n✅ 匯入完成！")
    
    return runs_imported, items_imported


def main():
    parser = argparse.ArgumentParser(description='從 CSV 匯入 MCRI V4.2 實驗資料')
    parser.add_argument('--runs', required=True, help='主表 CSV 檔案路徑')
    parser.add_argument('--items', required=True, help='附表 CSV 檔案路徑')
    parser.add_argument('--db-path', default='instance/math_education.db', help='資料庫檔案路徑')
    parser.add_argument('--overwrite', action='store_true', help='覆蓋重複記錄（預設跳過）')
    
    args = parser.parse_args()
    
    import_from_csv(
        runs_csv=args.runs,
        items_csv=args.items,
        db_path=args.db_path,
        skip_duplicates=not args.overwrite
    )


if __name__ == '__main__':
    main()
