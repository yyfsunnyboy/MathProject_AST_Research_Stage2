#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Ab1和Ab2文件中的参考例题
"""

def check_file(filepath, ablation_type):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_example = '【參考例題】' in content
    has_master_spec = '### MASTER_SPEC:' in content
    file_size = len(content)
    
    print(f"\n{ablation_type}:")
    print(f"  文件大小: {file_size} 字符")
    print(f"  包含【參考例題】: {has_example}")
    print(f"  包含### MASTER_SPEC: {has_master_spec}")
    
    if has_example and has_master_spec:
        example_pos = content.find('【參考例題】')
        master_spec_pos = content.find('### MASTER_SPEC:')
        print(f"  参考例题位置: {example_pos}")
        print(f"  MASTER_SPEC位置: {master_spec_pos}")
        print(f"  顺序正确: {example_pos < master_spec_pos}")

base_dir = r'e:\python\MathProject_AST_Research\experiments\golden_prompts\temp'
ab1_file = base_dir + r'\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab1.txt'
ab2_file = base_dir + r'\jh_數學1上_FourArithmeticOperationsOfNumbers_Ab2.txt'

print("检查 FourArithmeticOperationsOfNumbers 的 Prompt 文件:")
check_file(ab1_file, "Ab1 (BARE_MINIMAL_PROMPT)")
check_file(ab2_file, "Ab2 (UNIVERSAL_GEN_CODE_PROMPT)")
