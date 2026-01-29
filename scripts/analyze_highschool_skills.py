#!/usr/bin/env python3
"""分析高中 (gh_) 技能的複雜度"""

import os
import re
from pathlib import Path

backup_dir = Path("skills/backup_GenByGemini")

skills_data = []

for py_file in sorted(backup_dir.glob("gh_*.py")):
    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = len(content.split('\n'))
    
    # 計算 helper functions 數量
    helper_funcs = len(re.findall(r'\ndef [a-zA-Z_][a-zA-Z0-9_]*\(', content))
    
    # 估計複雜度
    if lines >= 800:
        complexity = 3
    elif lines >= 500:
        complexity = 2
    else:
        complexity = 1
    
    # 計算例題數量（簡單估計）
    examples = max(1, lines // 50)
    
    skills_data.append({
        'name': py_file.stem,
        'lines': lines,
        'helpers': helper_funcs,
        'complexity': complexity,
        'examples': examples
    })

# 按複雜度分類
complexity_3 = [s for s in skills_data if s['complexity'] == 3]
complexity_2 = [s for s in skills_data if s['complexity'] == 2]
complexity_1 = [s for s in skills_data if s['complexity'] == 1]

print("=" * 80)
print("📊 高中 (gh_) 技能分析 - backup_GenByGemini")
print("=" * 80)
print(f"\n【複雜度 3 (800+行)】{len(complexity_3)} 個\n")
for s in sorted(complexity_3, key=lambda x: x['lines'], reverse=True)[:10]:
    print(f"  • {s['name']:<50} | {s['lines']:>4}行 | {s['helpers']:>2}助函")

print(f"\n【複雜度 2 (500-800行)】{len(complexity_2)} 個\n")
for s in sorted(complexity_2, key=lambda x: x['lines'], reverse=True)[:10]:
    print(f"  • {s['name']:<50} | {s['lines']:>4}行 | {s['helpers']:>2}助函")

print(f"\n【複雜度 1 (<500行)】{len(complexity_1)} 個\n")
for s in sorted(complexity_1, key=lambda x: x['lines'], reverse=True)[:5]:
    print(f"  • {s['name']:<50} | {s['lines']:>4}行 | {s['helpers']:>2}助函")

print(f"\n\n📈 統計總結")
print(f"  • 總高中技能: {len(skills_data)}")
print(f"  • 複雜度3: {len(complexity_3)} 個 ({100*len(complexity_3)/len(skills_data):.1f}%)")
print(f"  • 複雜度2: {len(complexity_2)} 個 ({100*len(complexity_2)/len(skills_data):.1f}%)")
print(f"  • 複雜度1: {len(complexity_1)} 個 ({100*len(complexity_1)/len(skills_data):.1f}%)")
print(f"  • 平均行數: {sum(s['lines'] for s in skills_data) / len(skills_data):.0f}")
print(f"  • 最高行數: {max(s['lines'] for s in skills_data)}")
print(f"  • 最低行數: {min(s['lines'] for s in skills_data)}")
