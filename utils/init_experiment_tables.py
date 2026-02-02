# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): init_experiment_tables.py
功能說明 (Description): 初始化 MCRI V4.2 實驗資料表（含彙總表）
執行語法 (Usage): python utils/init_experiment_tables.py
版本資訊 (Version): V1.1
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
更新內容: 新增 ablation_summary 彙總表初始化
=============================================================================
"""

import os
import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from models import db, AblationSummary, ExperimentRun, EvaluationItem


def init_experiment_tables(db_path='instance/math_education.db'):
    """
    初始化 MCRI V4.2 實驗資料表（含彙總表）
    
    Args:
        db_path: 資料庫檔案路徑
    """
    print("="*70)
    print("🔧 初始化 MCRI V4.2 實驗資料表（三層架構）")
    print("="*70)
    
    # 確保目錄存在
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # 建立資料庫連線
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    
    # 建立資料表
    print(f"\n📊 資料庫路徑: {db_path}")
    print("\n建立資料表...")
    
    # 建立三層資料表
    AblationSummary.__table__.create(engine, checkfirst=True)
    ExperimentRun.__table__.create(engine, checkfirst=True)
    EvaluationItem.__table__.create(engine, checkfirst=True)
    
    print("✅ ablation_summary - 🌟 彙總表（統計推論層）")
    print("✅ experiment_runs - 主表（實驗控制層）")
    print("✅ evaluation_items - 附表（原始數據層）")
    
    # 建立索引（已在 SQL 定義中，這裡確認）
    print("\n建立索引...")
    from sqlalchemy import Index
    
    # 彙總表索引
    idx_summary_1 = Index('idx_summary_skill', AblationSummary.skill_name)
    idx_summary_2 = Index('idx_summary_ablation', AblationSummary.ablation_id)
    idx_summary_3 = Index('idx_summary_mean_mcri', AblationSummary.mean_mcri_total.desc())
    
    # 主表索引
    idx1 = Index('idx_runs_model_skill_ab', 
                 ExperimentRun.model_name, 
                 ExperimentRun.skill_name, 
                 ExperimentRun.ablation_id)
    idx2 = Index('idx_runs_timestamp', ExperimentRun.timestamp.desc())
    idx3 = Index('idx_runs_mcri_total', ExperimentRun.avg_mcri_total.desc())
    
    # 附表索引
    idx4 = Index('idx_items_run_id', EvaluationItem.run_id)
    idx5 = Index('idx_items_status', EvaluationItem.status)
    idx6 = Index('idx_items_included', EvaluationItem.included_in_avg)
    
    for idx in [idx_summary_1, idx_summary_2, idx_summary_3, 
                idx1, idx2, idx3, idx4, idx5, idx6]:
        idx.create(engine, checkfirst=True)
    
    print("✅ 索引建立完成（9 個）")
    
    # 驗證資料表
    print("\n🔍 驗證資料表結構...")
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'ablation_summary' in tables:
        columns = inspector.get_columns('ablation_summary')
        print(f"✅ ablation_summary: {len(columns)} 個欄位（含信賴區間與 p-value）")
    else:
        print("❌ ablation_summary 建立失敗")
    
    if 'experiment_runs' in tables:
        columns = inspector.get_columns('experiment_runs')
        print(f"✅ experiment_runs: {len(columns)} 個欄位")
    else:
        print("❌ experiment_runs 建立失敗")
    
    if 'evaluation_items' in tables:
        columns = inspector.get_columns('evaluation_items')
        print(f"✅ evaluation_items: {len(columns)} 個欄位")
    else:
        print("❌ evaluation_items 建立失敗")
    
    print("\n" + "="*70)
    print("✅ 初始化完成！")
    print("="*70)
    
    print("\n📚 使用說明：")
    print("1. 執行實驗並自動寫入資料庫：python scripts/evaluate_mcri.py --save-to-db")
    print("2. 計算統計彙總：python utils/compute_ablation_summary.py")
    print("3. 匯出到 CSV：python utils/export_experiment_data.py")
    print("3. 從 CSV 匯入：python utils/import_experiment_data.py --runs <主表.csv> --items <附表.csv>")
    print("4. 查詢統計：python scripts/query_experiment_results.py")


if __name__ == '__main__':
    init_experiment_tables()
