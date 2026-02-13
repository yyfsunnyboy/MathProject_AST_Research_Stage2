import random
from random import randint, choice
import math
from fractions import Fraction
import re
import ast
import operator
import os

# ==============================================================================
# [INJECTED UTILS] - 這是系統架構的一部分，必須保留在 Golden Reference 中
# ==============================================================================

op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

def safe_choice(seq):
    if not seq: return 1
    return random.choice(seq)

def to_latex(num):
    if isinstance(num, int): return str(num)
    if isinstance(num, float): num = Fraction(str(num)).limit_denominator(100)
    if isinstance(num, Fraction):
        if num.denominator > 100: num = num.limit_denominator(100)
        if num == 0: return "0"
        if num.denominator == 1: return str(num.numerator)
        is_neg = num < 0
        sign_str = "-" if is_neg else ""
        abs_num = abs(num)
        if abs_num.numerator > abs_num.denominator:
            whole = abs_num.numerator // abs_num.denominator
            rem_num = abs_num.numerator % abs_num.denominator
            if rem_num == 0: return f"{sign_str}{whole}"
            return f"{sign_str}{whole}\\frac{{{rem_num}}}{{{abs_num.denominator}}}"
        return f"{sign_str}\\frac{{{abs_num.numerator}}}{{{abs_num.denominator}}}"
    return str(num)

def fmt_num(num, signed=False, op=False):
    latex_val = to_latex(num)
    if num == 0 and not signed and not op: return "0"
    is_neg = (num < 0)
    if is_neg:
        if latex_val.startswith("-"): abs_latex_val = latex_val[1:] 
        else: abs_latex_val = latex_val
    else: abs_latex_val = latex_val
    if op: return f" - {abs_latex_val}" if is_neg else f" + {abs_latex_val}"
    if signed: return f"-{abs_latex_val}" if is_neg else f"+{abs_latex_val}"
    if is_neg: return f"({latex_val})"
    return latex_val

def fmt_term(coeff, power, var='x'):
    if coeff == 0: return ""
    sign = ""
    if coeff < 0: sign = "-"
    abs_c = abs(coeff)
    c_str = ""
    if abs_c != 1 or power == 0: c_str = fmt_num(abs_c)
    v_str = ""
    if power == 1: v_str = var
    elif power > 1: v_str = f"{var}^{{{power}}}"
    return f"{sign}{c_str}{v_str}"

def safe_eval(expr_str):
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos}
    def _eval(node):
        if isinstance(node, ast.Constant): return node.value
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num): return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Div): return Fraction(left, right)
            return ops[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp): return ops[type(node.op)](_eval(node.operand))
        raise TypeError(f"Unsupported type: {node}")
    try:
        clean_expr = str(expr_str).replace('\\times', '*').replace('\\div', '/')
        return _eval(ast.parse(clean_expr, mode='eval').body)
    except Exception: return 0

# ==============================================================================
# [DOMAIN HELPERS] - 領域相關工具，Data-flow 的關鍵節點
# ==============================================================================

def _poly_to_latex(terms):
    if not terms: return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0: continue
        sign = '' if i == 0 else (' + ' if c > 0 else ' - ')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0: var_str = str(abs_c)
        elif e == 1: var_str = f'{coeff_str}x' if coeff_str else 'x'
        else: var_str = f'{coeff_str}x^{{{e}}}' if coeff_str else f'x^{{{e}}}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

def _differentiate_poly(terms, order=1):
    result = list(terms)
    for _ in range(order):
        new_terms = []
        for c, e in result:
            if e > 0:
                new_c = c * e
                new_terms.append((new_c, e - 1))
        result = new_terms
    return result

def _deriv_symbol_latex(order):
    if order == 1: return "f'(x)"
    elif order == 2: return "f''(x)"
    else: return f"f^{{({order})}}(x)"

def _format_polynomial_for_answer(terms):
    # 重寫為純文本邏輯，對應 Ab3 的 _poly_to_plain
    if not terms: return '0'
    parts = []
    for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
        if c == 0: continue
        sign = '' if i == 0 else ('+' if c > 0 else '-')
        abs_c = abs(c)
        coeff_str = '' if (abs_c == 1 and e > 0) else str(abs_c)
        if e == 0: var_str = str(abs_c)
        elif e == 1: var_str = f'{coeff_str}x' if coeff_str else 'x'
        else: var_str = f'{coeff_str}x^{e}' if coeff_str else f'x^{e}'
        parts.append(f'{sign}{var_str}')
    return ''.join(parts).strip()

# ==============================================================================
# Golden Standard Generation Logic
# 這是基於 Ab3 (Healer) 優化後的標準邏輯
# ==============================================================================

def generate(level=1, **kwargs):
    # [Structural Requirement] 必須包含 retry loop 以確保強健性
    for _safety_counter in range(1000):
        try:
            # 1. 參數設定
            max_degree = random.randint(3, 5)
            num_terms = random.randint(3, 5)
            
            # 2. 生成係數
            # 這裡的邏輯必須足夠複雜，才能對應到 Ab3 的 AST 深度
            exponents = sorted(random.sample(range(max_degree + 1), num_terms), reverse=True)
            if max_degree not in exponents: exponents[0] = max_degree # 確保最高次
            
            original_polynomial_terms = []
            for exp in exponents:
                coeff = random.randint(-10, 10)
                if exp == max_degree and coeff == 0: coeff = 1 # 修正最高次係數
                if coeff != 0:
                    original_polynomial_terms.append((coeff, exp))
            
            if len(original_polynomial_terms) < 2: continue

            # 3. 導數設定
            orders = sorted(random.sample([1, 2, 3], random.randint(2, 3)))
            
            # 4. 計算與驗證
            calculated_derivs = {}
            current_terms = original_polynomial_terms
            
            # 模擬 Ab3 的逐步計算流
            for order in range(1, max(orders) + 1):
                current_terms = _differentiate_poly(current_terms, 1)
                if order in orders:
                    calculated_derivs[order] = current_terms
                    # [Constraint Check] 係數檢查
                    for c, _ in current_terms:
                        if abs(c) > 100: raise ValueError("Coefficient too large")

            # 5. 輸出組裝
            poly_latex = _poly_to_latex(original_polynomial_terms)
            deriv_symbols = ' 與 '.join([f'${_deriv_symbol_latex(o)}$' for o in orders])
            
            question_text = f'已知 $f(x) = {poly_latex}$，求 {deriv_symbols}。'
            
            answer_parts = []
            for order in orders:
                ans = _format_polynomial_for_answer(calculated_derivs[order])
                answer_parts.append(ans)
            
            correct_answer = ','.join(answer_parts)
            
            return {
                'question_text': question_text, 
                'correct_answer': correct_answer, 
                'answer': correct_answer, 
                'mode': 1
            }

        except Exception:
            continue
            
    # Fallback
    return {'question_text': 'Error', 'answer': 'Error', 'mode': 1}