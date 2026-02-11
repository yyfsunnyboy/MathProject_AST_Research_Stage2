#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为FourArithmeticOperationsOfNumbers技能生成所有Golden Prompts
"""
import sys
import os
import subprocess

# 路径修正
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))

# 运行build_golden_prompts脚本
python_exe = r'E:/Python/MathProject_AST_Research/.venv-1/Scripts/python.exe'
result = subprocess.run(
    [python_exe, 'scripts/build_golden_prompts.py', 'jh_數學1上_FourArithmeticOperationsOfNumbers'],
    cwd=project_root,
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print(f"\nExit Code: {result.returncode}")

