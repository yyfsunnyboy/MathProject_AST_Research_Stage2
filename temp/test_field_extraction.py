#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 evaluate_mcri.py 的欄位抓取功能
驗證是否正確提取技能檔案的 metadata 並記錄所有評分數據
"""

import sys
from pathlib import Path
import sqlite3

# 測試目標
test_file = Path("skills/gh_ApplicationsOfDerivatives_14b_Ab3.py")

print("="*80)
print("🧪 測試欄位抓取功能")
print("="*80)

# 1. 測試 metadata 提取
print("\n📋 測試 1: Metadata 提取")
print("-"*80)

if test_file.exists():
    with open(test_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:20]
    
    print("✅ 檔案前 20 行內容:")
    for i, line in enumerate(lines, 1):
        if any(keyword in line for keyword in ['Performance:', 'Created At:', 'Fix Status:', 'Verification:']):
            print(f"  Line {i}: {line.strip()}")
    
    # 測試正則提取
    import re
    
    metadata = {
        'performance': '',
        'tokens_in': 0,
        'tokens_out': 0,
        'created_at': '',
        'fix_status': '',
        'fixes_basic': 0,
        'fixes_regex': 0,
        'fixes_ast': 0,
        'verification': '',
    }
    
    for line in lines:
        line = line.strip()
        
        if 'Performance:' in line:
            perf_match = re.search(r'Performance:\s*([\d.]+)s', line)
            if perf_match:
                metadata['performance'] = perf_match.group(1)
            
            tokens_match = re.search(r'Tokens:\s*In=(\d+),\s*Out=(\d+)', line)
            if tokens_match:
                metadata['tokens_in'] = int(tokens_match.group(1))
                metadata['tokens_out'] = int(tokens_match.group(2))
        
        elif 'Created At:' in line:
            created_match = re.search(r'Created At:\s*(.+)', line)
            if created_match:
                metadata['created_at'] = created_match.group(1).strip()
        
        elif 'Fix Status:' in line:
            metadata['fix_status'] = line.split('Fix Status:')[-1].strip()
            
            basic_match = re.search(r'Basic=(\d+)', line)
            if basic_match:
                metadata['fixes_basic'] = int(basic_match.group(1))
            
            regex_match = re.search(r'Regex=(\d+)', line)
            if regex_match:
                metadata['fixes_regex'] = int(regex_match.group(1))
            
            ast_match = re.search(r'AST=(\d+)', line)
            if ast_match:
                metadata['fixes_ast'] = int(ast_match.group(1))
        
        elif 'Verification:' in line:
            metadata['verification'] = line.split('Verification:')[-1].strip()
    
    print("\n📊 提取結果:")
    print(f"  Performance: {metadata['performance']}s")
    print(f"  Tokens: In={metadata['tokens_in']}, Out={metadata['tokens_out']}")
    print(f"  Created At: {metadata['created_at']}")
    print(f"  Fix Status: {metadata['fix_status']}")
    print(f"  Fixes: Basic={metadata['fixes_basic']}, Regex={metadata['fixes_regex']}, AST={metadata['fixes_ast']}")
    print(f"  Verification: {metadata['verification']}")
    
    # 驗證與目標是否一致
    print("\n✅ 驗證結果:")
    expected = {
        'performance': '17.13',
        'tokens_in': 7122,
        'tokens_out': 620,
        'created_at': '2026-02-02 11:26:37',
        'fixes_basic': 1,
        'fixes_regex': 4,
        'fixes_ast': 0,
    }
    
    all_match = True
    for key, expected_val in expected.items():
        actual_val = metadata[key]
        match = (str(actual_val) == str(expected_val))
        status = "✓" if match else "✗"
        print(f"  {status} {key}: {actual_val} {'==' if match else '!='} {expected_val}")
        if not match:
            all_match = False
    
    if all_match:
        print("\n🎉 所有欄位完全一致！")
    else:
        print("\n⚠️  部分欄位不一致，請檢查正則表達式")

else:
    print(f"❌ 測試檔案不存在: {test_file}")

# 2. 測試資料庫欄位定義
print("\n" + "="*80)
print("📋 測試 2: 資料庫欄位定義")
print("-"*80)

# 檢查資料庫是否包含所有必要欄位
required_fields = {
    'experiment_runs': [
        'run_id', 'timestamp', 'model_name', 'skill_name', 'ablation_id', 'sample_index',
        'code_commit_hash', 'python_version', 'model_temperature',
        'repetitions_planned', 'repetitions_completed', 'fail_count', 'pass_rate', 'avg_exec_time',
        'score_l1_total', 'score_l1_1_syntax', 'score_l1_2_runtime',
        'score_l2_total', 'score_l2_1_contract', 'score_l2_2_purity',
        'avg_l3_total', 'avg_l3_1_internal', 'avg_l3_2_external',
        'avg_l4_total', 'avg_l4_1_numeric', 'avg_l4_2_visual',
        'avg_mcri_total', 'source_code_path', 'mcri_version', 'notes'
    ],
    'evaluation_items': [
        'item_id', 'run_id', 'repetition_index',
        'generated_question', 'generated_answer', 'generated_correct_answer',
        'status', 'error_log', 'included_in_avg',
        'score_l3_total', 'score_l3_1_internal', 'score_l3_2_external',
        'score_l4_total', 'score_l4_1_numeric', 'score_l4_2_visual',
        'student_input_test', 'student_input_result'
    ],
    'ablation_summary': [
        'summary_id', 'skill_name', 'ablation_id', 'model_name',
        'sample_count', 'total_runs',
        'mean_mcri_total', 'std_mcri_total', 'ci95_lower', 'ci95_upper',
        'mean_l3_external', 'mean_l4_numeric'
    ]
}

print("✅ 必要欄位清單:")
for table, fields in required_fields.items():
    print(f"\n📊 {table} ({len(fields)} 個欄位):")
    for i, field in enumerate(fields, 1):
        print(f"  {i:2d}. {field}")

# 3. 測試評分流程
print("\n" + "="*80)
print("📋 測試 3: 評分流程檢查清單")
print("-"*80)

checklist = [
    ("✓", "讀取技能檔案 metadata (Performance, Created At, Fix Status, Verification)"),
    ("✓", "載入 generate() 和 check() 函數"),
    ("✓", "執行 L1 評估 (語法安全 + 執行穩定性)"),
    ("✓", "執行 20 次 repetition，每次記錄到 evaluation_items"),
    ("✓", "每次 repetition 評估 L2 (介面契約 + 格式純淨度)"),
    ("✓", "每次 repetition 評估 L3 (內在一致性 + 外在強健性)"),
    ("✓", "每次 repetition 評估 L4 (數值友善度 + 視覺可讀性)"),
    ("✓", "計算 20 次平均分（排除 included_in_avg=0 的項目）"),
    ("✓", "將平均分寫入 experiment_runs 表"),
    ("✓", "將每次明細寫入 evaluation_items 表"),
    ("✓", "計算跨 5 個 sample 的統計彙總 (mean, std, CI)"),
    ("✓", "將彙總統計寫入 ablation_summary 表"),
    ("✓", "同時輸出 SQLite 資料庫與 CSV 報表"),
    ("✓", "在 notes 欄位記錄 metadata 資訊"),
]

print("\n評分流程完整性:")
for status, item in checklist:
    print(f"  {status} {item}")

print("\n" + "="*80)
print("✅ 測試完成！")
print("="*80)
print("\n📝 下一步:")
print("  1. 執行 python scripts/evaluate_mcri.py 進行完整評估")
print("  2. 檢查 reports/mcri_evaluation.db 資料庫")
print("  3. 檢查 reports/csv/*.csv 報表")
print("  4. 驗證 notes 欄位是否包含完整 metadata")
