import random
import math
from fractions import Fraction
import operator

# ==============================================================================
# [INJECTED UTILS] - 系統工具庫 (保留以確保 Data-flow 一致性)
# ==============================================================================

op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}

def safe_eval(expr):
    """安全計算表達式"""
    try:
        # 替換運算符以符合 Python 語法
        clean = expr.replace('\\times', '*').replace('\\div', '/')
        return eval(clean, {"__builtins__": None}, {})
    except:
        return None

def to_latex(num):
    """轉 LaTeX 格式"""
    if isinstance(num, int): return str(num)
    if isinstance(num, float): return str(int(num)) if num.is_integer() else f"{num:.2f}"
    return str(num)

class IntegerOps:
    """整數運算專用工具"""
    @staticmethod
    def random_nonzero(a, b):
        val = random.randint(a, b)
        while val == 0:
            val = random.randint(a, b)
        return val

    @staticmethod
    def fmt_num(n):
        """格式化數字：負數加括號"""
        return f"({n})" if n < 0 else f"{n}"

    @staticmethod
    def fmt_op(op):
        return op_latex.get(op, op)

# ==============================================================================
# Golden Standard Generation Logic
# 基於 Ab3 優化後的標準邏輯：整數四則運算
# ==============================================================================

def generate(level=1, **kwargs):
    """
    Golden Template for Integer Arithmetic
    標準邏輯：
    1. 隨機決定運算結構 (例如: (A op1 B) op2 C)
    2. 逆向推導：確保計算過程整除且結果為整數
    3. 格式化輸出
    """
    # [Structural Requirement] 強健性：Retry Loop
    for _ in range(100):
        try:
            # 1. 隨機選擇運算符
            ops = ['+', '-', '*', '/']
            op1 = random.choice(ops)
            op2 = random.choice(ops)
            
            # 2. 生成數字與逆向推導
            # 目標結構：Term1 op2 C = Result
            # Term1 = A op1 B
            
            # 先生成 A, B
            A = IntegerOps.random_nonzero(-20, 20)
            B = IntegerOps.random_nonzero(-20, 20)
            
            # 處理除法整除約束
            if op1 == '/':
                A = B * IntegerOps.random_nonzero(-10, 10) # 確保 A/B 整除
            
            # 計算 Term1
            val_term1 = safe_eval(f"{A} {op1.replace('/', '//')} {B}")
            if val_term1 is None: continue

            # 生成 C
            C = IntegerOps.random_nonzero(-20, 20)
            
            # 處理第二層除法整除
            if op2 == '/':
                # 如果是除法，調整 Term1 讓它能被 C 整除，或者調整 C
                # 簡單策略：重設 Term1 為 C 的倍數 (這會改變 A 或 B，較複雜)
                # 這裡採用 Ab3 的策略：如果不能整除就換一個 C
                if C == 0 or val_term1 % C != 0:
                    # 嘗試構造：讓 C 成為 val_term1 的因數
                    factors = [i for i in range(1, abs(int(val_term1)) + 1) if val_term1 % i == 0]
                    if not factors: continue
                    C = random.choice(factors) * random.choice([1, -1])
            
            # 3. 計算最終結果
            # 注意：Python 的 eval 順序與數學順序一致
            expression_math = f"{A} {op1} {B} {op2} {C}"
            
            # 為了確保運算優先級顯示正確，我們通常需要加括號
            # 這裡模擬一個簡單的結構：(A op1 B) op2 C
            # 如果 op2 優先級高於 op1，則 (A op1 B) 需要括號
            
            need_parens = False
            if op2 in ['*', '/'] and op1 in ['+', '-']:
                need_parens = True
            
            # 格式化顯示
            str_A = IntegerOps.fmt_num(A)
            str_B = IntegerOps.fmt_num(B)
            str_C = IntegerOps.fmt_num(C)
            
            latex_op1 = IntegerOps.fmt_op(op1)
            latex_op2 = IntegerOps.fmt_op(op2)
            
            if need_parens:
                question_latex = f"({str_A} {latex_op1} {str_B}) {latex_op2} {str_C}"
                eval_expr = f"({A} {op1.replace('/','//')} {B}) {op2.replace('/','//')} {C}"
            else:
                question_latex = f"{str_A} {latex_op1} {str_B} {latex_op2} {str_C}"
                eval_expr = f"{A} {op1.replace('/','//')} {B} {op2.replace('/','//')} {C}"
            
            final_ans = safe_eval(eval_expr)
            
            if final_ans is None: continue
            
            # 4. 輸出
            question_text = f"計算：${question_latex}$"
            correct_answer = str(int(final_ans))
            
            return {
                'question_text': question_text,
                'correct_answer': correct_answer,
                'answer': correct_answer,
                'mode': 1
            }

        except Exception:
            continue
            
    # Fallback
    return {
        'question_text': '計算：$1 + 1$',
        'correct_answer': '2',
        'answer': '2',
        'mode': 1
    }