#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
显示Ab2文件中参考例题的部分内容
"""

filepath = r'e:\python\MathProject_AST_Research\experiments\golden_prompts\temp\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab2.txt'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到参考例题部分
example_start = content.find('【參考例題】')
example_end = content.find('### MASTER_SPEC:')

if example_start > -1 and example_end > example_start:
    example_section = content[example_start:example_end]
    print("=== Ab2 文件中的參考例題部分 ===\n")
    print(example_section)
else:
    print("未找到參考例題部分")
