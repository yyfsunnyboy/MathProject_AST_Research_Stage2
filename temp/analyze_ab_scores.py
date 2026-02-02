#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 Ab1 vs Ab2 vs Ab3 的得分差異
找出為什麼 Ab2 分數比 Ab1 低
"""

import pandas as pd
from pathlib import Path

# 讀取評估結果
csv_path = Path("E:/Python/MathProject_AST_Research/reports/csv/experiment_runs.csv")

if not csv_path.exists():
    print("❌ 找不到評估結果檔案")
    exit(1)

df = pd.read_csv(csv_path)

print("="*80)
print("📊 Ab1 vs Ab2 vs Ab3 得分比較")
print("="*80)

# 按 ablation_id 分組計算平均值
summary = df.groupby('ablation_id').agg({
    'avg_mcri_total': ['mean', 'std'],
    'score_l1_total': ['mean', 'std'],
    'score_l2_total': ['mean', 'std'],
    'avg_l3_total': ['mean', 'std'],
    'avg_l4_total': ['mean', 'std'],
    'avg_l4_1_numeric': ['mean', 'std'],
    'avg_l4_2_visual': ['mean', 'std'],
    'pass_rate': 'mean',
    'fail_count': 'sum'
}).round(2)

print("\n【總分對比】")
print("-"*80)
for ab_id in [1, 2, 3]:
    if ab_id in summary.index:
        total_mean = summary.loc[ab_id, ('avg_mcri_total', 'mean')]
        total_std = summary.loc[ab_id, ('avg_mcri_total', 'std')]
        print(f"Ab{ab_id}: {total_mean:.2f} ± {total_std:.2f}")

print("\n【各層級得分詳細對比】")
print("-"*80)
print(f"{'Ablation':<10} {'L1':<10} {'L2':<10} {'L3':<12} {'L4':<12} {'L4.1':<10} {'L4.2':<10} {'總分':<10}")
print("-"*80)

for ab_id in [1, 2, 3]:
    if ab_id in summary.index:
        l1 = summary.loc[ab_id, ('score_l1_total', 'mean')]
        l2 = summary.loc[ab_id, ('score_l2_total', 'mean')]
        l3 = summary.loc[ab_id, ('avg_l3_total', 'mean')]
        l4 = summary.loc[ab_id, ('avg_l4_total', 'mean')]
        l4_1 = summary.loc[ab_id, ('avg_l4_1_numeric', 'mean')]
        l4_2 = summary.loc[ab_id, ('avg_l4_2_visual', 'mean')]
        total = summary.loc[ab_id, ('avg_mcri_total', 'mean')]
        
        print(f"Ab{ab_id:<9} {l1:<10.2f} {l2:<10.2f} {l3:<12.2f} {l4:<12.2f} {l4_1:<10.2f} {l4_2:<10.2f} {total:<10.2f}")

print("\n【關鍵問題：為什麼 Ab2 < Ab1？】")
print("-"*80)

# 找出 Ab1 和 Ab2 的數據
if 1 in summary.index and 2 in summary.index:
    ab1_total = summary.loc[1, ('avg_mcri_total', 'mean')]
    ab2_total = summary.loc[2, ('avg_mcri_total', 'mean')]
    
    if ab2_total < ab1_total:
        diff = ab1_total - ab2_total
        print(f"⚠️  Ab2 比 Ab1 低 {diff:.2f} 分！")
        print()
        
        # 逐項對比差異
        print("差異分析：")
        for metric in ['score_l1_total', 'score_l2_total', 'avg_l3_total', 'avg_l4_total']:
            ab1_val = summary.loc[1, (metric, 'mean')]
            ab2_val = summary.loc[2, (metric, 'mean')]
            diff_val = ab2_val - ab1_val
            
            metric_name = metric.replace('score_', '').replace('avg_', '').replace('_total', '')
            sign = "↑" if diff_val > 0 else "↓"
            
            print(f"  {metric_name.upper():<6}: Ab1={ab1_val:.2f}, Ab2={ab2_val:.2f}, Diff={diff_val:+.2f} {sign}")
        
        # 特別檢查 L4.2（視覺可讀性）
        print()
        print("🔍 L4.2 視覺可讀性細節：")
        ab1_l42 = summary.loc[1, ('avg_l4_2_visual', 'mean')]
        ab2_l42 = summary.loc[2, ('avg_l4_2_visual', 'mean')]
        diff_l42 = ab2_l42 - ab1_l42
        
        print(f"  Ab1 L4.2: {ab1_l42:.2f}/15")
        print(f"  Ab2 L4.2: {ab2_l42:.2f}/15")
        print(f"  差異: {diff_l42:+.2f}")
        
        if diff_l42 < -3:
            print()
            print("  💡 推論：Ab2 的 L4.2 分數明顯較低")
            print("     可能原因：LaTeX 格式錯誤（$LATEX$ $BLOCK$ bug）")
            print("     已修復：derivative_symbols_latex 現在有正確的 $ $ 包裹")

# 檢查實際的 sample 資料
print("\n【Ab2 樣本檢查】")
print("-"*80)
ab2_samples = df[df['ablation_id'] == 2].head(3)

if not ab2_samples.empty:
    print("\n前 3 個 Ab2 樣本的 L4.2 分數：")
    for idx, row in ab2_samples.iterrows():
        print(f"  Sample {row['sample_index']}: L4.2 = {row['avg_l4_2_visual']:.2f}/15")
        
print("\n【建議】")
print("-"*80)
print("1. 刪除舊資料庫: del reports\\mcri_evaluation.db")
print("2. 刪除舊 CSV: del reports\\csv\\*.csv")
print("3. 重新執行評估: python scripts\\evaluate_mcri.py")
print("4. 檢查修復後 Ab2 的 L4.2 分數是否提升")
