#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速測試數據庫插入"""
import sys
import os
from pathlib import Path
from datetime import datetime, UTC

os.chdir('e:\\Python\\MathProject_AST_Research')
sys.path.insert(0, 'scripts')

import sqlite3
from evaluate_mcri import create_database

db_path = Path('instance/kumon_math.db')

print(f"測試數據庫: {db_path}")
print("="*60)

# 建立數據庫
create_database(str(db_path))
conn = sqlite3.connect(str(db_path))

# 準備測試數據
test_run = {
    'run_id': 'test_001',
    'timestamp': datetime.now(UTC).isoformat(),
    'model_name': 'test-model',
    'skill_name': 'TestSkill',
    'ablation_id': 1,
    'sample_index': 1,
    'code_commit_hash': 'abc123',
    'python_version': '3.11.0',
    'mcri_version': '4.2.2',
    'model_temperature': 0.7,
    'repetitions_planned': 20,
    'repetitions_completed': 20,
    'fail_count': 0,
    'pass_rate': 1.0,
    'avg_exec_time': 0.5,
    'score_l1_total': 20,
    'score_l1_1_syntax': 10,
    'score_l1_2_runtime': 10,
    'score_l2_total': 20,
    'score_l2_1_contract': 10,
    'score_l2_2_purity': 10,
    'avg_l3_total': 30.0,
    'avg_l3_1_internal': 15.0,
    'avg_l3_2_external': 15.0,
    'avg_l4_total': 30.0,
    'avg_l4_1_numeric': 15.0,
    'avg_l4_2_visual': 15.0,
    'avg_mcri_total': 100.0,
    'source_code_path': '/test/path.py',
    'notes': 'Test notes',
    'batch_id': 'batch_001',
    'golden_prompt_path': '/prompt/path',
    'prompt_hash': 'hash123',
    'prompt_tokens': 100,
    'completion_tokens': 50,
    'total_tokens': 150,
    'latency_ms': 500,
    'healer_applied': 0,
    'healer_fix_count': 0,
}

# 嘗試插入
cursor = conn.cursor()
try:
    cursor.execute("""
        INSERT INTO experiment_runs 
        (run_id, timestamp, model_name, skill_name, ablation_id, sample_index,
         code_commit_hash, python_version, mcri_version, model_temperature,
         repetitions_planned, repetitions_completed, fail_count, pass_rate, avg_exec_time,
         score_l1_total, score_l1_1_syntax, score_l1_2_runtime,
         score_l2_total, score_l2_1_contract, score_l2_2_purity,
         avg_l3_total, avg_l3_1_internal, avg_l3_2_external,
         avg_l4_total, avg_l4_1_numeric, avg_l4_2_visual,
         avg_mcri_total, source_code_path, notes,
         batch_id, golden_prompt_path, prompt_hash,
         prompt_tokens, completion_tokens, total_tokens,
         latency_ms, healer_applied, healer_fix_count)
        VALUES
        (:run_id, :timestamp, :model_name, :skill_name, :ablation_id, :sample_index,
         :code_commit_hash, :python_version, :mcri_version, :model_temperature,
         :repetitions_planned, :repetitions_completed, :fail_count, :pass_rate, :avg_exec_time,
         :score_l1_total, :score_l1_1_syntax, :score_l1_2_runtime,
         :score_l2_total, :score_l2_1_contract, :score_l2_2_purity,
         :avg_l3_total, :avg_l3_1_internal, :avg_l3_2_external,
         :avg_l4_total, :avg_l4_1_numeric, :avg_l4_2_visual,
         :avg_mcri_total, :source_code_path, :notes,
         :batch_id, :golden_prompt_path, :prompt_hash,
         :prompt_tokens, :completion_tokens, :total_tokens,
         :latency_ms, :healer_applied, :healer_fix_count)
    """, test_run)
    conn.commit()
    print("✅ 成功插入測試數據")
    
    # 驗證
    cursor.execute('SELECT COUNT(*) FROM experiment_runs')
    count = cursor.fetchone()[0]
    print(f"✅ 表中現有 {count} 條記錄")
    
except Exception as e:
    print(f"❌ 插入失敗: {type(e).__name__}: {e}")

conn.close()
