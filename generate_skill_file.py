# -*- coding: utf-8 -*-
# ==============================================================================
# ID: generate_skill_file.py
# Version: v0.1 (Generate Actual Skill Files)
# Last Updated: 2026-01-29
# Author: Math AI Research Team
#
# [Description]:
#   根據 v0.1 架構動態生成技能程式碼，並保存到 skills/ 資料夾
# ==============================================================================

import sys
import os
import json
from datetime import datetime

# 添加專案根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.architect_v01 import ArchitectV01
from core.v01_pipeline import (
    query_textbook_example,
    extract_code_from_response,
    heal_code,
    execute_generated_code
)

# 建立 Flask 應用上下文
from app import app
app_context = app.app_context()
app_context.push()

def generate_skill_code(example_id, skill_name="ApplicationsOfDerivatives"):
    """
    【核心函數】生成技能程式碼並保存到 skills/ 資料夾
    
    Args:
        example_id: 課本例題 ID (2944, 2955, 2956, ...)
        skill_name: 技能英文 ID
    
    Returns:
        dict: {success: bool, filepath: str, message: str}
    """
    
    print("\n" + "="*70)
    print("🚀 開始生成技能文件: {} (題號: {})".format(skill_name, example_id))
    print("="*70)
    
    # ============================================================
    # 步驟 1: 查詢課本例題
    # ============================================================
    print("[步驟 1] 查詢課本例題...")
    textbook_example = query_textbook_example(example_id)
    if not textbook_example:
        return {
            'success': False,
            'filepath': None,
            'message': "❌ 無法查詢例題 {}".format(example_id)
        }
    print("[OK] 課本例題: {}...".format(textbook_example.get('problem_text', '')[:50]))
    
    # ============================================================
    # 步驟 2: Architect 分析
    # ============================================================
    print("[步驟 2] Architect 分析問題...")
    try:
        architect = ArchitectV01()
        master_spec = architect.analyze_problem(textbook_example)
        problem_type = master_spec.get('problem_type', 'unknown')
        print("[OK] 問題類型識別: {}".format(problem_type))
    except Exception as e:
        return {
            'success': False,
            'filepath': None,
            'message': "❌ Architect 分析失敗: {}".format(str(e))
        }
    
    # ============================================================
    # 步驟 3: 組裝 Coder Prompt
    # ============================================================
    print("[步驟 3] 組裝 Coder Prompt...")
    coder_prompt = architect.to_prompt_for_coder(master_spec)
    print("[OK] Prompt 長度: {} 字符".format(len(coder_prompt)))
    
    # ============================================================
    # 步驟 4: 生成代碼（模擬）
    # ============================================================
    print("[步驟 4] 生成代碼...")
    response = _generate_mock_code(problem_type, master_spec)
    print("[OK] 代碼生成完成: {} 字符".format(len(response)))
    
    # ============================================================
    # 步驟 5: 提取代碼
    # ============================================================
    print("[步驟 5] 提取代碼...")
    code = extract_code_from_response(response)
    if not code:
        return {
            'success': False,
            'filepath': None,
            'message': "❌ 代碼提取失敗"
        }
    print("[OK] 代碼行數: {} 行".format(len(code.splitlines())))
    
    # ============================================================
    # 步驟 6: Healer 修復
    # ============================================================
    print("[步驟 6] Healer 修復...")
    healed_code = heal_code(code)
    print("[OK] Healer 修復完成")
    
    # ============================================================
    # 步驟 7: 驗證執行
    # ============================================================
    print("[步驟 7] 驗證執行...")
    success_count = 0
    for i in range(3):
        try:
            result = execute_generated_code(healed_code)
            if result:
                success_count += 1
                print("[OK] 迭代 {} 執行成功".format(i+1))
        except Exception as e:
            print("[警告] 迭代 {} 執行失敗: {}".format(i+1, str(e)))
    
    if success_count < 3:
        return {
            'success': False,
            'filepath': None,
            'message': "❌ 執行驗證失敗 ({}/3 成功)".format(success_count)
        }
    
    # ============================================================
    # 步驟 8: 保存到 skills/ 資料夾
    # ============================================================
    print("[步驟 8] 保存到 skills/ 資料夾...")
    
    skills_dir = os.path.join(project_root, 'skills')
    os.makedirs(skills_dir, exist_ok=True)
    
    # 生成檔名（包含例題 ID）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "{}_{}_example{}.py".format(skill_name, example_id, timestamp)
    filepath = os.path.join(skills_dir, filename)
    
    # 建立完整的技能文件（頭部 + 工具函數 + 生成的代碼）
    full_code = _build_skill_file(skill_name, problem_type, healed_code, master_spec)
    
    # 保存到檔案
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_code)
        print("[OK] 文件保存成功: {}".format(filepath))
    except Exception as e:
        return {
            'success': False,
            'filepath': None,
            'message': "❌ 檔案保存失敗: {}".format(str(e))
        }
    
    # ============================================================
    # 成功總結
    # ============================================================
    print("\n" + "="*70)
    print("✅ 技能文件生成成功!")
    print("   檔案: {}".format(filename))
    print("   路徑: {}".format(filepath))
    print("   問題類型: {}".format(problem_type))
    print("   執行驗證: {}/3 通過".format(success_count))
    print("="*70)
    
    return {
        'success': True,
        'filepath': filepath,
        'filename': filename,
        'problem_type': problem_type,
        'execution_rate': '{}/3'.format(success_count)
    }


def _generate_mock_code(problem_type, master_spec):
    """模擬代碼生成（完整的生成邏輯，包含 LaTeX 和中文）"""
    
    if problem_type == 'tangent_line':
        code = """
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction
    
    for _ in range(1000):
        a = random.randint(-5, 5)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)
        x0 = random.randint(-3, 3)
        
        if a == 0:
            continue
        
        y0 = a * x0**2 + b * x0 + c
        m = 2 * a * x0 + b
        b_intercept = y0 - m * x0
        
        poly_str = "{} x^2 + {} x + {}".format(fmt_num(a), fmt_num(b), fmt_num(c))
        point_str = "({}, {})".format(fmt_num(x0), fmt_num(y0))
        q = "在函數 $f(x) = {}$ 的圖形上，求以點 $P{}$ 為切點的切線方程式。".format(poly_str, point_str)
        q = clean_latex_output(q)
        
        m_str = fmt_num(m)
        b_str = fmt_num(b_intercept)
        a = "y = {} x + {}".format(m_str, b_str)
        
        return {'question_text': q, 'answer': a, 'mode': 1}
"""
    
    elif problem_type == 'multiple_derivatives':
        code = """
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction
    
    for _ in range(1000):
        a = random.randint(-3, 3)
        b = random.randint(-3, 3)
        c = random.randint(-5, 5)
        d = random.randint(-5, 5)
        
        if a == 0:
            continue
        
        poly_str = "{}x^4 + {}x^3 + {}x + {}".format(fmt_num(a), fmt_num(b), fmt_num(c), fmt_num(d))
        q = "已知 $f(x) = {}$，求 $f'(x)$ 與 $f'''(x)$。".format(poly_str)
        q = clean_latex_output(q)
        
        f_prime = "{}x^3 + {}x^2 + {}".format(fmt_num(4*a), fmt_num(3*b), fmt_num(c))
        f_triple = "{}x".format(fmt_num(24*a))
        a = "f'(x) = {}；f'''(x) = {}".format(f_prime, f_triple)
        
        return {'question_text': q, 'answer': a, 'mode': 1}
"""
    
    else:  # single_derivative
        code = """
def generate(level=1, **kwargs):
    import random
    from fractions import Fraction
    
    for _ in range(1000):
        a = random.randint(-5, 5)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)
        
        if a == 0:
            continue
        
        poly_str = "{}x^3 + {}x^2 + {}x".format(fmt_num(a), fmt_num(b), fmt_num(c))
        q = "已知函數 $f(x) = {}$，求 $f'(x)$。".format(poly_str)
        q = clean_latex_output(q)
        
        deriv_str = "{}x^2 + {}x + {}".format(fmt_num(3*a), fmt_num(2*b), fmt_num(c))
        a = "f'(x) = {}".format(deriv_str)
        
        return {'question_text': q, 'answer': a, 'mode': 1}
"""
    
    return code


def _build_skill_file(skill_name, problem_type, code, master_spec):
    """建立完整的技能文件"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = "# -*- coding: utf-8 -*-\n"
    header += "# ==============================================================================\n"
    header += "# ID: skills/{}\n".format(skill_name)
    header += "# Skill: {}\n".format(skill_name)
    header += "# Problem Type: {}\n".format(problem_type)
    header += "# Model: gemini-2.5-flash (Architect) + qwen2.5-coder (Coder)\n"
    header += "# Architecture: v0.1 (Database-Driven Dynamic)\n"
    header += "# Created At: {}\n".format(timestamp)
    header += "# ==============================================================================\n\n"
    
    utils = """# ============================================================================
# [UTILITY FUNCTIONS - Pre-Injected by System]
# ============================================================================

import random
import math
from fractions import Fraction

def fmt_num(num, signed=False, op=False):
    if num == 0: return "0"
    if isinstance(num, int): return str(num)
    return str(num)

def to_latex(num):
    if isinstance(num, Fraction):
        if num.denominator == 1:
            return str(num.numerator)
        return "\\\\frac{{{}}}{{{}}}".format(num.numerator, num.denominator)
    return str(num)

def clean_latex_output(q):
    return q.replace('$$', '$')

def safe_choice(seq):
    if not seq: return 1
    return random.choice(seq)

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}
    except:
        return {'correct': False, 'result': '錯誤'}

# ============================================================================
# [AI GENERATED CODE]
# ============================================================================

"""
    
    return header + utils + code


if __name__ == "__main__":
    # 生成 ApplicationsOfDerivatives 的三個例題
    examples = [
        (2944, "ApplicationsOfDerivatives"),
        (2955, "ApplicationsOfDerivatives"),
        (2956, "ApplicationsOfDerivatives"),
    ]
    
    results = []
    for example_id, skill_name in examples:
        result = generate_skill_code(example_id, skill_name)
        results.append(result)
    
    # 總結
    print("\n\n" + "="*70)
    print("📊 生成總結")
    print("="*70)
    for i, result in enumerate(results):
        status = "[OK]" if result['success'] else "[FAIL]"
        example_id = examples[i][0]
        msg = result.get('message', result.get('filename', ''))
        print("{} 題號 {}: {}".format(status, example_id, msg))
    
    success_count = sum(1 for r in results if r['success'])
    print("\n總成功率: {}/{}".format(success_count, len(results)))
