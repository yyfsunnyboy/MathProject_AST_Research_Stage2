#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to test gh_ApplicationsOfDerivatives
"""

import sys
sys.path.insert(0, '.')

from skills.gh_ApplicationsOfDerivatives import generate

print("=" * 60)
print("【Debug Test】gh_ApplicationsOfDerivatives")
print("=" * 60)

try:
    result = generate(level=1)
    print("\n✓ 生成成功!")
    print(f"\nQuestion: {result.get('question_text')}")
    print(f"Answer: {result.get('answer')}")
    print(f"Mode: {result.get('mode')}")
    
    # 检查是否是真正的导数题目
    question = result.get('question_text', '')
    if '導數' in question or '求導' in question or '導' in question:
        print("\n✓ 这是导数题目")
    else:
        print("\n✗ 这NOT是导数题目！")
        print("  问题: 题目是关于算术运算,而不是导数应用")
        
except Exception as e:
    print(f"\n✗ 错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
