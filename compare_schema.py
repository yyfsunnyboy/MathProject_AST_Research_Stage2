#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""比較程式碼中定義的 schema 與實際資料庫 schema"""

import sqlite3
from pathlib import Path

# 程式碼中定義的欄位 (從 evaluate_mcri.py)
code_schema = {
    'experiment_runs': [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'code_commit_hash', 'python_version', 'mcri_version', 'model_temperature',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual', 'avg_l4_3_artifacts',  # [V4.4]
        'avg_complexity_math_ops', 'avg_complexity_ast_nodes', 'avg_complexity_loop_depth',  # [V4.4]
        'avg_mcri_total', 'source_code_path', 'notes',
        'batch_id', 'golden_prompt_path', 'prompt_hash',
        'prompt_tokens', 'completion_tokens', 'total_tokens',
        'latency_ms', 'healer_applied', 'healer_fix_count'
    ],
    'evaluation_items': [
        'item_id', 'run_id', 'repetition_index',
        'generated_question', 'generated_answer', 'generated_correct_answer',
        'status', 'error_log', 'included_in_avg',
        'exec_time_ms',
        'score_l2_1_contract', 'score_l2_2_purity',
        'score_l3_total', 'score_l3_1_internal', 'score_l3_2_external',
        'score_l4_total', 'score_l4_1_numeric', 'score_l4_2_visual', 'score_l4_3_artifacts',
        'complexity_math_ops', 'complexity_ast_nodes', 'complexity_loop_depth',  # [V4.4]
        'student_input_test', 'student_input_result'
    ],
    'ablation_summary': [
        'summary_id', 'skill_name', 'ablation_id', 'model_name',
        'sample_count', 'total_runs',
        'mean_mcri_total', 'std_mcri_total', 'ci95_lower', 'ci95_upper',
        'mean_l3_external', 'mean_l4_numeric', 'p_value_vs_ab1', 'notes'
    ]
}

# 從資料庫取得實際欄位
db_path = Path('instance/kumon_math.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

db_schema = {}
for table_name in code_schema.keys():
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    db_schema[table_name] = [col[1] for col in columns]

conn.close()

# 比較
print("="*80)
print("SCHEMA COMPARISON: Code vs Database")
print("="*80)

for table_name in code_schema.keys():
    print(f"\n{'='*80}")
    print(f"TABLE: {table_name}")
    print('='*80)
    
    code_cols = code_schema[table_name]
    db_cols = db_schema.get(table_name, [])
    
    print(f"Code defines:     {len(code_cols)} columns")
    print(f"Database has:     {len(db_cols)} columns")
    print(f"Difference:       {len(code_cols) - len(db_cols)}")
    
    # 缺少的欄位 (在程式碼中但不在資料庫)
    missing = set(code_cols) - set(db_cols)
    if missing:
        print(f"\n[MISSING in DB] {len(missing)} columns NOT in database:")
        for col in sorted(missing):
            print(f"  - {col}")
    
    # 多餘的欄位 (在資料庫中但不在程式碼)
    extra = set(db_cols) - set(code_cols)
    if extra:
        print(f"\n[EXTRA in DB] {len(extra)} columns in database but NOT in code:")
        for col in sorted(extra):
            print(f"  + {col}")
    
    if not missing and not extra:
        print("\n✓ Schema matches perfectly!")

print(f"\n{'='*80}")
print("SUMMARY")
print('='*80)

total_missing = sum(len(set(code_schema[t]) - set(db_schema.get(t, []))) for t in code_schema.keys())
print(f"Total missing columns: {total_missing}")

if total_missing > 0:
    print("\nYou need to:")
    print("1. Delete the old database: rm instance/kumon_math.db")
    print("2. Run: python scripts/evaluate_mcri.py")
    print("   (or call create_database() to recreate with new schema)")
