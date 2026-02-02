#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Ab2 修復後的題目生成
"""

import sys
from pathlib import Path

# 載入技能檔案
skill_path = Path("E:/Python/MathProject_AST_Research/skills/gh_ApplicationsOfDerivatives_14b_Ab2.py")

import importlib.util
spec = importlib.util.spec_from_file_location("skill_module", skill_path)
skill_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_module)

print("="*80)
print("🧪 測試 Ab2 題目生成（修復後）")
print("="*80)

# 測試 5 次生成
for i in range(5):
    print(f"\n【測試 {i+1}】")
    try:
        result = skill_module.generate()
        question = result.get('question_text', '')
        answer = result.get('correct_answer', '')
        
        print(f"題目: {question}")
        print(f"答案: {answer[:100]}..." if len(answer) > 100 else f"答案: {answer}")
        
        # 檢查是否有異常的佔位符
        if '__LATEX_BLOCK_' in question or '$LATEX$' in question or '$BLOCK$' in question:
            print("❌ 發現未替換的佔位符！")
        else:
            print("✅ 題目格式正常")
            
    except Exception as e:
        print(f"❌ 生成失敗: {e}")

print("\n" + "="*80)
print("測試完成")
print("="*80)
