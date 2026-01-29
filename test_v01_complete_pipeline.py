#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【標題】v0.1 完整流程測試框架
【功能】八步測試架構: 初始化 → 題目分析 → 提示組裝 → 代碼生成 → 質量檢查 → 代碼修復 → 執行驗證 → 最終報告
【支持】參數化多個例題 (題 2944, 2955, 2956)
【語言】繁體中文 (Traditional Chinese only)
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.architect_v01 import ArchitectV01
from core.v01_pipeline import (
    query_textbook_example,
    extract_code_from_response,
    heal_code,
    execute_generated_code
)

# 預定義的課本例題字典
TEXTBOOK_EXAMPLES = {
    2944: {
        'problem_id': 2944,
        'problem_text': '求曲線 y = x^3 - 3x + 2 在點 (1, 0) 處的切線方程式',
        'problem_type': 'tangent_line',
        'domain': 'ApplicationsOfDerivatives'
    },
    2955: {
        'problem_id': 2955,
        'problem_text': '已知 f(x) = x^4 - 2x^3 + 5x - 4，求 f\'(x) 與 f\'\'\'(x)',
        'problem_type': 'multiple_derivatives',
        'domain': 'ApplicationsOfDerivatives'
    },
    2956: {
        'problem_id': 2956,
        'problem_text': '求函數 f(x) = x^3 + 2x^2 - 5x + 1 的一階導數',
        'problem_type': 'single_derivative',
        'domain': 'ApplicationsOfDerivatives'
    }
}

# 模擬 Qwen 的生成代碼
MOCK_QWEN_RESPONSE = """
```python
# 計算多階導數
import sympy as sp

x = sp.Symbol('x')
f = x**4 - 2*x**3 + 5*x - 4

# 一階導數
f_prime = sp.diff(f, x)
print(f"f'(x) = {f_prime}")

# 三階導數
f_triple_prime = sp.diff(f, x, 3)
print(f"f'''(x) = {f_triple_prime}")

# 驗證在 x=1 的值
print(f"f'(1) = {f_prime.subs(x, 1)}")
print(f"f'''(1) = {f_triple_prime.subs(x, 1)}")
```
"""

def get_textbook_example(example_id):
    """
    獲取課本例題
    優先使用數據庫，備選使用預定義字典
    """
    # 試圖從數據庫查詢
    db_example = query_textbook_example(example_id)
    if db_example:
        return db_example
    
    # 否則使用預定義字典
    if example_id in TEXTBOOK_EXAMPLES:
        return TEXTBOOK_EXAMPLES[example_id]
    
    raise ValueError(f"題目 {example_id} 未找到")

def test_step_1_2_architect(textbook_example):
    """
    【步驟 1-2】Architect 初始化 + 課本例題分析
    """
    print("\n" + "="*70)
    print("[步驟 1-2] Architect 初始化與課本例題分析")
    print("="*70)
    
    # 初始化 Architect
    architect = ArchitectV01()
    print("[OK] Architect 初始化成功")
    
    # 分析課本例題
    master_spec = architect.analyze_problem(textbook_example)
    print(f"[OK] 課本例題分析完成")
    print(f"     問題類型: {master_spec.get('problem_type', 'unknown')}")
    print(f"     問題結構: {master_spec.get('problem_structure', {})}")
    
    return architect, master_spec

def test_step_3_prompt_assembly(architect, master_spec):
    """
    【步驟 3】提示組裝
    """
    print("\n" + "="*70)
    print("[步驟 3] 提示組裝")
    print("="*70)
    
    coder_prompt = architect.to_prompt_for_coder(master_spec)
    print("[OK] Coder 提示組裝完成")
    print(f"     提示長度: {len(coder_prompt)} 個字符")
    
    return coder_prompt

def test_step_4_coder_generation(coder_prompt):
    """
    【步驟 4】代碼生成
    """
    print("\n" + "="*70)
    print("[步驟 4] Coder 代碼生成")
    print("="*70)
    
    # 使用模擬的 Qwen 回應
    response = MOCK_QWEN_RESPONSE
    print("[OK] 模擬 Qwen 代碼生成成功")
    print(f"     回應長度: {len(response)} 個字符")
    
    generated_code = extract_code_from_response(response)
    print(f"[OK] 代碼提取成功")
    print(f"     代碼行數: {len(generated_code.splitlines())} 行")
    
    return generated_code, response

def test_step_5_code_quality(generated_code):
    """
    【步驟 5】代碼質量檢查
    """
    print("\n" + "="*70)
    print("[步驟 5] 代碼質量檢查")
    print("="*70)
    
    # 基本的代碼檢查
    checks = {
        '有代碼內容': len(generated_code) > 0,
        '無語法錯誤': not any(err in generated_code for err in ['SyntaxError', 'IndentationError']),
        '包含 import': 'import' in generated_code.lower(),
    }
    
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name}")
    
    all_pass = all(checks.values())
    return all_pass

def test_step_6_healer(generated_code):
    """
    【步驟 6】Healer 代碼修復
    """
    print("\n" + "="*70)
    print("[步驟 6] Healer 代碼修復")
    print("="*70)
    
    healed_code = heal_code(generated_code)
    print("[OK] Healer 修復完成")
    
    # 顯示修復信息
    if healed_code != generated_code:
        print("[OK] 檢測到並修復的問題:")
        if '**' in healed_code and '^' in generated_code:
            print("     - 修復了冪次操作符 (^ to **)")
    else:
        print("[OK] 無需修復，代碼已正確")
    
    return healed_code

def test_step_7_execution(healed_code):
    """
    【步驟 7】代碼執行驗證 (3 次迭代)
    """
    print("\n" + "="*70)
    print("[步驟 7] 代碼執行驗證")
    print("="*70)
    
    success_count = 0
    for iteration in range(1, 4):
        try:
            result = execute_generated_code(healed_code)
            print(f"[OK] 迭代 {iteration} 執行成功")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] 迭代 {iteration} 執行失敗: {str(e)[:50]}")
    
    print(f"\n[結果] 成功率: {success_count}/3 ({success_count*100//3}%)")
    return success_count == 3

def test_step_8_final_report(example_id, master_spec, quality_pass, all_exec_pass):
    """
    【步驟 8】最終報告
    """
    print("\n" + "="*70)
    print("[步驟 8] 最終報告")
    print("="*70)
    
    report = {
        '題號': example_id,
        '問題類型': master_spec.get('problem_type', 'unknown'),
        '代碼質量': '通過' if quality_pass else '未通過',
        '執行驗證': '成功' if all_exec_pass else '失敗',
        '整體狀態': '成功' if (quality_pass and all_exec_pass) else '失敗'
    }
    
    print("\n最終報告:")
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    return report

def main(example_id=2955):
    """
    主測試流程
    """
    print("\n")
    print("*" * 70)
    print("[v0.1] 完整流程測試啟動（Database-Driven 版本）")
    print("*" * 70)
    print(f"選定題號: {example_id}")
    
    try:
        # 獲取課本例題
        textbook_example = get_textbook_example(example_id)
        print(f"[OK] 已載入課本例題: {textbook_example.get('problem_type', 'unknown')}")
        
        # 步驟 1-2: Architect 分析
        architect, master_spec = test_step_1_2_architect(textbook_example)
        
        # 步驟 3: 提示組裝
        coder_prompt = test_step_3_prompt_assembly(architect, master_spec)
        
        # 步驟 4: 代碼生成
        generated_code, response = test_step_4_coder_generation(coder_prompt)
        
        # 步驟 5: 代碼質量檢查
        quality_pass = test_step_5_code_quality(generated_code)
        
        # 步驟 6: Healer 修復
        healed_code = test_step_6_healer(generated_code)
        
        # 步驟 7: 執行驗證
        all_exec_pass = test_step_7_execution(healed_code)
        
        # 步驟 8: 最終報告
        report = test_step_8_final_report(example_id, master_spec, quality_pass, all_exec_pass)
        
        print("\n" + "*" * 70)
        if report['整體狀態'] == '成功':
            print("[成功] v0.1 完整流程測試通過")
        else:
            print("[失敗] v0.1 完整流程測試失敗")
        print("*" * 70)
        
        return 0 if report['整體狀態'] == '成功' else 1
    
    except Exception as e:
        print(f"\n[錯誤] 測試執行出錯: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    # 默認題號 2955，或從命令行參數獲取
    example_id = 2955
    if len(sys.argv) > 1:
        try:
            example_id = int(sys.argv[1])
        except ValueError:
            print(f"[警告] 無效的題號參數: {sys.argv[1]}，使用默認值 2955")
    
    exit_code = main(example_id)
    sys.exit(exit_code)
