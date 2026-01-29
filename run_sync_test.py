#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試修復後的 sync_skills_files.py"""

import subprocess
import sys
import os

os.chdir(r'e:\Python\MathProject_AST_Research')

# 準備輸入序列
inputs = [
    "0",      # Curriculum: ALL
    "0",      # Grade: ALL  
    "0",      # Volume: ALL
    "0",      # Chapter: ALL
    "0",      # Skill: ALL
    "4",      # Mode: 4 (Full Pipeline + AST Healing)
    "3",      # Ablation ID: 3 (Full Healing)
    "2",      # Model Size: 2 (14B)
    "y",      # Confirm: yes
]

input_str = "\n".join(inputs) + "\n"

print("=" * 70)
print("🚀 開始執行 sync_skills_files.py (Mode 4, Ablation 3)")
print("=" * 70)
print(f"輸入序列: {inputs}")
print("=" * 70)

# 執行
proc = subprocess.Popen(
    [sys.executable, "scripts/sync_skills_files.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

stdout, _ = proc.communicate(input=input_str, timeout=300)
print(stdout)

print("\n" + "=" * 70)
print(f"✅ 執行完成 (Exit Code: {proc.returncode})")
print("=" * 70)
