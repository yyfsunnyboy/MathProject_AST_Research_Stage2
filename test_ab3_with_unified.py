# -*- coding: utf-8 -*-
"""測試新統一 Healer 是否修復實際的 AB3 生成"""

import sys
import os
sys.path.insert(0, r'e:\python\MathProject_AST_Research')
os.chdir(r'e:\python\MathProject_AST_Research')

# 配置
os.environ['HEALER_DEBUG'] = '0'
os.environ['HEALER_VERBOSE'] = '1'

from core.code_generator import CodeGenerator
from models import db

print("=" * 70)
print("TEST: AB3 Generation with Unified Healer")
print("=" * 70)

# 使用某個真實的技能來進行代生成
skill_id = "jh_數學1上_FourArithmeticOperationsOfIntegers"

try:
    print(f"\n🔍 生成技能: {skill_id}")
    print(f"   Ablation: AB3 (使用統一 Healer)")
    
    generator = CodeGenerator(skill_id=skill_id, ablation_id=3)
    
    print("\n📝 開始生成代碼...")
    code = generator.generate()
    
    if code:
        print("✅ 代碼生成成功")
        
        # 檢查污染
        pollution_checks = {
            'IntegerOps = 0': "污染: IntegerOps 被覆蓋",
            'fmt_num = 0': "污染: fmt_num 被覆蓋",
            'fmt_num = None': "污染: fmt_num 被覆蓋（None版本）",
            'clean_latex_output = None': "污染: clean_latex_output 被覆蓋",
            'to_latex = None': "污染: to_latex 被覆蓋",
            'op_latex = None': "污染: op_latex 被覆蓋",
        }
        
        print("\n🔍 檢查污染...")
        pollution_found = False
        for pattern, desc in pollution_checks.items():
            if pattern in code:
                print(f"   ❌ {desc}")
                pollution_found = True
        
        if not pollution_found:
            print("   ✅ 無污染")
        
        # 檢查語法
        print("\n🔍 檢查語法...")
        try:
            import ast
            ast.parse(code)
            print("   ✅ 語法正確")
        except SyntaxError as e:
            print(f"   ❌ 語法錯誤: {e}")
        
        # 顯示代碼片段
        print("\n【代碼片段 - 開始部分】")
        print("-" * 50)
        lines = code.split('\n')
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d}: {line}")
        
    else:
        print("❌ 生成失敗，返回 None")
        
except Exception as e:
    print(f"❌ 異常: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("完成測試")
print("=" * 70)
