# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): test_experiment_db.py
功能說明 (Description): 測試 MCRI V4.2 實驗資料表的完整功能
執行語法 (Usage): python utils/test_experiment_db.py
版本資訊 (Version): V1.0
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import db, ExperimentRun, EvaluationItem


def test_create_experiment():
    """測試建立實驗記錄"""
    print("\n" + "="*70)
    print("🧪 測試 1：建立實驗記錄")
    print("="*70)
    
    # 使用測試資料庫
    test_db = 'instance/test_experiment.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    engine = create_engine(f'sqlite:///{test_db}')
    
    # 建立資料表
    ExperimentRun.__table__.create(engine, checkfirst=True)
    EvaluationItem.__table__.create(engine, checkfirst=True)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 建立測試實驗
    run_id = str(uuid.uuid4())
    
    run = ExperimentRun(
        run_id=run_id,
        timestamp=datetime.now(),
        model_name='qwen-14b',
        skill_name='gh_ApplicationsOfDerivatives',
        ablation_id=3,
        sample_index=1,
        code_commit_hash='test123',
        python_version='3.9.13',
        mcri_version='V4.2',
        model_temperature=0.7,
        repetitions_planned=20,
        repetitions_completed=0,
        fail_count=0,
        score_l1_total=17,
        score_l1_1_syntax=7,
        score_l1_2_runtime=10,
        score_l2_total=20,
        score_l2_1_contract=10,
        score_l2_2_purity=10,
        source_code_path='skills/test.py',
        notes='測試記錄'
    )
    
    session.add(run)
    session.commit()
    
    print(f"✅ 建立實驗記錄: {run_id[:8]}...")
    print(f"   技能: {run.skill_name}")
    print(f"   配置: Ab{run.ablation_id}")
    print(f"   L1: {run.score_l1_total}/20, L2: {run.score_l2_total}/20")
    
    session.close()
    engine.dispose()  # 關閉連線
    return test_db, run_id


def test_add_evaluation_items(test_db, run_id):
    """測試添加評估項目（會自動計算平均分）"""
    print("\n" + "="*70)
    print("🧪 測試 2：添加評估項目")
    print("="*70)
    
    engine = create_engine(f'sqlite:///{test_db}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 添加 3 個評估項目
    scores = [
        (25, 28),  # L3=25, L4=28
        (27, 29),
        (23, 27)
    ]
    
    for i, (l3, l4) in enumerate(scores, 1):
        item = EvaluationItem(
            item_id=str(uuid.uuid4()),
            run_id=run_id,
            repetition_index=i,
            generated_question=f'測試題目 {i}',
            generated_answer='',
            generated_correct_answer='2x+3',
            status='Success',
            exec_time_ms=150.5,
            included_in_avg=True,
            score_l3_total=l3,
            score_l3_1_internal=15,
            score_l3_2_external=l3-15,
            score_l4_total=l4,
            score_l4_1_numeric=15,
            score_l4_2_visual=l4-15
        )
        session.add(item)
        print(f"✅ 添加項目 #{i}: L3={l3}, L4={l4}")
    
    session.commit()
    
    # 查詢更新後的 run（平均分應該自動計算）
    # 注意：SQLite 的觸發器在 SQLAlchemy 中可能不會自動觸發
    # 需要手動重新查詢或重新計算
    
    session.close()
    engine.dispose()  # 關閉連線


def test_manual_avg_calculation(test_db, run_id):
    """測試手動計算平均分"""
    print("\n" + "="*70)
    print("🧪 測試 3：計算平均分")
    print("="*70)
    
    engine = create_engine(f'sqlite:///{test_db}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        run = session.query(ExperimentRun).filter_by(run_id=run_id).first()
        items = session.query(EvaluationItem).filter_by(run_id=run_id, included_in_avg=True).all()
        
        if items:
            # 計算平均
            avg_l3 = sum(i.score_l3_total for i in items) / len(items)
            avg_l4 = sum(i.score_l4_total for i in items) / len(items)
            avg_mcri = run.score_l1_total + run.score_l2_total + avg_l3 + avg_l4
            
            # 更新
            run.avg_l3_total = avg_l3
            run.avg_l3_1_internal = sum(i.score_l3_1_internal for i in items) / len(items)
            run.avg_l3_2_external = sum(i.score_l3_2_external for i in items) / len(items)
            run.avg_l4_total = avg_l4
            run.avg_l4_1_numeric = sum(i.score_l4_1_numeric for i in items) / len(items)
            run.avg_l4_2_visual = sum(i.score_l4_2_visual for i in items) / len(items)
            run.avg_mcri_total = avg_mcri
            run.repetitions_completed = len(items)
            run.pass_rate = len([i for i in items if i.status == 'Success']) / len(items)
            
            session.commit()
            
            print(f"✅ 平均分計算完成:")
            print(f"   L1: {run.score_l1_total}/20")
            print(f"   L2: {run.score_l2_total}/20")
            print(f"   L3: {run.avg_l3_total:.1f}/30")
            print(f"   L4: {run.avg_l4_total:.1f}/30")
            print(f"   MCRI: {run.avg_mcri_total:.1f}/100")
            print(f"   通過率: {run.pass_rate*100:.0f}%")
    finally:
        session.close()
        engine.dispose()  # 確保關閉所有連線


def test_export_import(test_db):
    """測試匯出匯入功能"""
    print("\n" + "="*70)
    print("🧪 測試 4：CSV 匯出匯入")
    print("="*70)
    
    # 匯出
    from export_experiment_data import export_to_csv
    runs_file, items_file = export_to_csv(db_path=test_db, output_dir='instance/test_export')
    
    if runs_file and items_file:
        print(f"✅ 匯出成功")
        print(f"   主表: {runs_file}")
        print(f"   附表: {items_file}")
        
        # 匯入到新資料庫
        test_db2 = 'instance/test_experiment2.db'
        if os.path.exists(test_db2):
            os.remove(test_db2)
        
        from import_experiment_data import import_from_csv
        runs_count, items_count = import_from_csv(
            runs_csv=f'instance/test_export/{runs_file}',
            items_csv=f'instance/test_export/{items_file}',
            db_path=test_db2,
            skip_duplicates=False
        )
        
        print(f"\n✅ 匯入成功")
        print(f"   主表: {runs_count} 筆")
        print(f"   附表: {items_count} 筆")
    else:
        print("❌ 匯出失敗（資料庫為空）")


def test_to_dict():
    """測試 to_dict 方法"""
    print("\n" + "="*70)
    print("🧪 測試 5：to_dict 序列化")
    print("="*70)
    
    run = ExperimentRun(
        run_id='test-uuid',
        timestamp=datetime.now(),
        model_name='qwen-14b',
        skill_name='test_skill',
        ablation_id=1,
        sample_index=1,
        code_commit_hash='abc123',
        python_version='3.9.13',
        source_code_path='test.py',
        score_l1_total=10
    )
    
    data = run.to_dict()
    
    print(f"✅ 序列化成功")
    print(f"   欄位數: {len(data)}")
    print(f"   範例欄位: run_id={data['run_id']}, skill_name={data['skill_name']}")
    
    # 驗證所有必要欄位都存在
    required_fields = ['run_id', 'model_name', 'skill_name', 'ablation_id', 'sample_index']
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        print(f"❌ 缺少欄位: {missing}")
    else:
        print("✅ 所有必要欄位都存在")


def cleanup():
    """清理測試檔案"""
    print("\n" + "="*70)
    print("🧹 清理測試檔案")
    print("="*70)
    
    import time
    import shutil
    
    # 等待檔案釋放
    time.sleep(1)
    
    test_files = [
        'instance/test_experiment.db',
        'instance/test_experiment2.db'
    ]
    
    for f in test_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✅ 刪除: {f}")
            except PermissionError:
                print(f"⚠️ 無法刪除 {f}（檔案被鎖定），請手動刪除")
    
    # 清理匯出目錄
    if os.path.exists('instance/test_export'):
        try:
            shutil.rmtree('instance/test_export')
            print(f"✅ 刪除: instance/test_export/")
        except Exception as e:
            print(f"⚠️ 無法刪除 instance/test_export/: {e}")


def main():
    print("="*70)
    print("🧪 MCRI V4.2 實驗資料表測試")
    print("="*70)
    
    try:
        # 測試 1-3：基本 CRUD
        test_db, run_id = test_create_experiment()
        test_add_evaluation_items(test_db, run_id)
        test_manual_avg_calculation(test_db, run_id)
        
        # 測試 4：匯出匯入
        test_export_import(test_db)
        
        # 測試 5：序列化
        test_to_dict()
        
        print("\n" + "="*70)
        print("✅ 所有測試通過！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        cleanup()


if __name__ == '__main__':
    main()
