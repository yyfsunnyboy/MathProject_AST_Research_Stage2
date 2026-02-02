#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比較 Ab2 和 Ab3 的關鍵差異
分析為什麼 Ab3 沒有出現 Ab2 的問題
"""

import difflib
from pathlib import Path

# 讀取兩個檔案
ab2_path = Path("E:/Python/MathProject_AST_Research/skills/gh_ApplicationsOfDerivatives_14b_Ab2.py")
ab3_path = Path("E:/Python/MathProject_AST_Research/skills/gh_ApplicationsOfDerivatives_14b_Ab3.py")

with open(ab2_path, 'r', encoding='utf-8') as f:
    ab2_lines = f.readlines()

with open(ab3_path, 'r', encoding='utf-8') as f:
    ab3_lines = f.readlines()

print("="*80)
print("🔍 Ab2 vs Ab3 差異分析")
print("="*80)

# Header 資訊對比
print("\n【Header 對比】")
print(f"Ab2: {''.join(ab2_lines[:8])}")
print("-" * 80)
print(f"Ab3: {''.join(ab3_lines[:8])}")

# 統計資訊
print("\n【統計對比】")
print(f"Ab2 總行數: {len(ab2_lines)}")
print(f"Ab3 總行數: {len(ab3_lines)}")
print(f"差異: {len(ab2_lines) - len(ab3_lines)} 行")

# 尋找關鍵字差異
print("\n【關鍵字出現次數】")
keywords = [
    'clean_latex_output',
    'derivative_symbols_latex',
    '_deriv_symbol_latex',
    'Advanced Healer',
    'Regex='
]

for keyword in keywords:
    ab2_count = sum(1 for line in ab2_lines if keyword in line)
    ab3_count = sum(1 for line in ab3_lines if keyword in line)
    diff = ab2_count - ab3_count
    diff_str = f"({diff:+d})" if diff != 0 else ""
    print(f"  {keyword:30s}: Ab2={ab2_count}, Ab3={ab3_count} {diff_str}")

# 找出 generate() 函數的差異
print("\n【generate() 函數差異】")
print("尋找題目組合部分...")

# 在 Ab2 中找 "組合題目"
ab2_gen_start = None
for i, line in enumerate(ab2_lines):
    if '步驟 8:' in line or '組合題目' in line:
        ab2_gen_start = i
        break

# 在 Ab3 中找類似位置
ab3_gen_start = None
for i, line in enumerate(ab3_lines):
    if 'poly_latex = _poly_to_latex' in line:
        ab3_gen_start = i
        break

if ab2_gen_start:
    print(f"\nAb2 (行 {ab2_gen_start+1} 開始):")
    print(''.join(ab2_lines[ab2_gen_start:ab2_gen_start+6]))

if ab3_gen_start:
    print(f"\nAb3 (行 {ab3_gen_start+1} 開始):")
    print(''.join(ab3_lines[ab3_gen_start:ab3_gen_start+6]))

# 詳細 diff
print("\n【關鍵段落 Unified Diff】")
if ab2_gen_start and ab3_gen_start:
    ab2_snippet = ab2_lines[ab2_gen_start:ab2_gen_start+10]
    ab3_snippet = ab3_lines[ab3_gen_start:ab3_gen_start+10]
    
    diff = difflib.unified_diff(
        ab2_snippet,
        ab3_snippet,
        fromfile='Ab2',
        tofile='Ab3',
        lineterm=''
    )
    
    for line in diff:
        if line.startswith('+'):
            print(f"  \033[32m{line}\033[0m")  # 綠色
        elif line.startswith('-'):
            print(f"  \033[31m{line}\033[0m")  # 紅色
        elif line.startswith('@@'):
            print(f"  \033[36m{line}\033[0m")  # 青色
        else:
            print(f"  {line}")

# 結論
print("\n" + "="*80)
print("📊 結論")
print("="*80)

# 檢查 Ab2 是否有 clean_latex_output(q) 在 generate 中
ab2_has_clean = any('clean_latex_output(q)' in line for line in ab2_lines)
ab3_has_clean = any('clean_latex_output(q)' in line for line in ab3_lines)

print(f"\nAb2 在 generate() 中呼叫 clean_latex_output(q): {'❌ 是 (已修復)' if ab2_has_clean else '✅ 否'}")
print(f"Ab3 在 generate() 中呼叫 clean_latex_output(q): {'❌ 是' if ab3_has_clean else '✅ 否'}")

# 檢查修復狀態
print("\n修復狀態：")
print("  Ab2: [Basic Cleanup] | Regex=0 → 沒有被 Healer 修復")
print("  Ab3: [Advanced Healer] | Regex=4 → 被 Healer 修復了 4 次")

print("\n推論：")
print("  1. Ab2 和 Ab3 使用同一份 prompt")
print("  2. AI 生成時可能都犯了類似錯誤")
print("  3. Ab3 的 Advanced Healer 自動修復了問題")
print("  4. Ab2 的 Healer 沒有檢測到或修復不完整")
print("  5. 這就是為什麼 Ab3 沒有爆炸，而 Ab2 爆炸了")

print("\n建議：")
print("  → 檢查 Healer 的 Regex 規則，看看第 4 次修復做了什麼")
print("  → 將該規則加入 Ab2 的修復邏輯")
