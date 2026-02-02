"""
驗證資料庫 Schema 清理 - 確認已刪除 3 個欄位
"""
import sqlite3
import os

def check_database_schema():
    """檢查資料庫 schema 是否正確移除 3 個欄位"""
    
    db_path = "reports/mcri_evaluation_test.db"
    
    # 刪除舊資料庫（如果存在）
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  已刪除舊資料庫: {db_path}")
    
    # 建立資料庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 建立 experiment_runs 表（使用新 schema）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            model_name TEXT,
            skill_name TEXT,
            ablation_id INTEGER,
            sample_index INTEGER,
            repetitions_planned INTEGER,
            repetitions_completed INTEGER,
            fail_count INTEGER,
            pass_rate REAL,
            avg_exec_time REAL,
            score_l1_total INTEGER,
            score_l1_1_syntax INTEGER,
            score_l1_2_runtime INTEGER,
            score_l2_total INTEGER,
            score_l2_1_contract INTEGER,
            score_l2_2_purity INTEGER,
            avg_l3_total REAL,
            avg_l3_1_internal REAL,
            avg_l3_2_external REAL,
            avg_l4_total REAL,
            avg_l4_1_numeric REAL,
            avg_l4_2_visual REAL,
            avg_mcri_total REAL,
            source_code_path TEXT,
            mcri_version TEXT,
            notes TEXT
        )
    """)
    
    conn.commit()
    
    # 檢查欄位
    cursor.execute("PRAGMA table_info(experiment_runs)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print("\n" + "="*80)
    print("📋 experiment_runs 表結構檢查")
    print("="*80)
    
    print(f"\n✅ 總欄位數: {len(column_names)} 個")
    print(f"   (原本 30 個 → 現在 27 個，已刪除 3 個)")
    
    # 檢查已刪除的欄位
    removed_fields = ['code_commit_hash', 'python_version', 'model_temperature']
    print(f"\n🔴 確認已刪除的欄位 (3 個):")
    
    all_removed = True
    for field in removed_fields:
        if field in column_names:
            print(f"   ❌ {field} - 仍然存在！")
            all_removed = False
        else:
            print(f"   ✅ {field} - 已成功刪除")
    
    # 檢查保留的欄位
    expected_fields = [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual',
        'avg_mcri_total', 'source_code_path', 'mcri_version', 'notes'
    ]
    
    print(f"\n✅ 確認保留的欄位 (27 個):")
    all_exist = True
    for field in expected_fields:
        if field not in column_names:
            print(f"   ❌ {field} - 遺失！")
            all_exist = False
    
    if all_exist:
        print(f"   ✅ 所有 27 個欄位都正確保留")
    
    # 最終結果
    print("\n" + "="*80)
    if all_removed and all_exist and len(column_names) == 27:
        print("🎉 Schema 清理成功！")
        print("   - 已刪除: code_commit_hash, python_version, model_temperature")
        print("   - 保留欄位: 27 個")
        print("   - 資料庫結構: 正確 ✓")
    else:
        print("❌ Schema 清理失敗，請檢查程式碼")
    print("="*80)
    
    conn.close()
    
    # 刪除測試資料庫
    os.remove(db_path)
    print(f"\n🗑️  測試完成，已刪除測試資料庫\n")

if __name__ == "__main__":
    check_database_schema()
