#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 input() 攔截邏輯
"""
import sys
import subprocess
from io import StringIO
import os

os.chdir('e:\\Python\\MathProject_AST_Research')

# 用 subprocess 運行，並提供輸入
process = subprocess.Popen(
    [sys.executable, 'scripts/evaluate_mcri.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    errors='replace'
)

# 提供輸入：y（確認開始）
try:
    output, errors = process.communicate(input='y\n', timeout=120)
    print(output)
    if errors:
        print("STDERR:", errors)
except subprocess.TimeoutExpired:
    process.kill()
    print("進程超時")
