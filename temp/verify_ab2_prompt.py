#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证修改后的Ab2 prompt文件
"""
import os

filepath = r'e:\python\MathProject_AST_Research\experiments\golden_prompts\temp\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab2.txt'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查关键部分
example_pos = content.find('【參考例題】')
master_spec_pos = content.find('### MASTER_SPEC:')

print("检查修改结果:")
print(f"1. 参考例题位置: {example_pos}")
print(f"2. MASTER_SPEC位置: {master_spec_pos}")

if example_pos > 0 and master_spec_pos > example_pos:
    print("3. 结果: 成功 - 参考例题正确添加在MASTER_SPEC之前")
    
    # 显示内容
    section = content[example_pos:master_spec_pos]
    print("\n--- 参考例题部分 (前200字符) ---")
    print(section[:200])
else:
    print("3. 结果: 失败")
