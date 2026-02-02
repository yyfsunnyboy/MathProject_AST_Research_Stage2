#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試 Ab1/Ab2/Ab3 的題目生成
"""

import sys
import importlib.util
from pathlib import Path

def test_skill_file(file_path, ablation_name):
    """測試單個技能檔案"""
    print(f"\n{'='*80}")
    print(f"🧪 測試 {ablation_name}: {file_path.name}")
    print(f"{'='*80}")
    
    try:
        # 載入模組
        spec = importlib.util.spec_from_file_location("skill_module", file_path)
        skill_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(skill_module)
        
        # 測試 3 次生成
        for i in range(3):
            print(f"\n【測試 {i+1}】")
            try:
                result = skill_module.generate()
                question = result.get('question_text', '')
                answer = result.get('correct_answer', '')
                
                # 處理 dict 格式的答案（Ab1 使用）
                if isinstance(answer, dict):
                    answer = str(answer)
                
                # 檢查問題
                issues = []
                
                if not question or len(question.strip()) < 10:
                    issues.append("❌ 題目太短或空白")
                
                if '__LATEX_BLOCK_' in question or '$LATEX$' in question or '$BLOCK$' in question:
                    issues.append("❌ 發現未替換的佔位符")
                
                if 'None' in question or 'undefined' in question:
                    issues.append("⚠️ 包含 None 或 undefined")
                
                if not answer or len(answer.strip()) < 1:
                    issues.append("❌ 答案空白")
                
                # 顯示結果
                if issues:
                    print("  " + "\n  ".join(issues))
                    print(f"  題目: {question[:100]}...")
                    print(f"  答案: {answer[:50]}...")
                else:
                    print(f"  ✅ 題目: {question}")
                    print(f"  ✅ 答案: {answer[:80]}...")
                    
            except Exception as e:
                print(f"  ❌ 生成失敗: {type(e).__name__}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 載入失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

# 測試三個檔案
project_root = Path("E:/Python/MathProject_AST_Research")
skills_dir = project_root / "skills"

files_to_test = [
    (skills_dir / "gh_ApplicationsOfDerivatives_14b_Ab1.py", "Ab1 (Bare)"),
    (skills_dir / "gh_ApplicationsOfDerivatives_14b_Ab2.py", "Ab2 (Engineered)"),
    (skills_dir / "gh_ApplicationsOfDerivatives_14b_Ab3.py", "Ab3 (Full Healer)"),
]

print("="*80)
print("🔬 題目生成測試")
print("="*80)

results = {}
for file_path, name in files_to_test:
    if file_path.exists():
        results[name] = test_skill_file(file_path, name)
    else:
        print(f"\n❌ 檔案不存在: {file_path}")
        results[name] = False

# 總結
print("\n" + "="*80)
print("📊 測試總結")
print("="*80)
for name, success in results.items():
    status = "✅ 通過" if success else "❌ 失敗"
    print(f"  {name}: {status}")
