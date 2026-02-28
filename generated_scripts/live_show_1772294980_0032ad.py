import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-15, 15)  # 對應 9
        v2 = IntegerOps.random_nonzero(-15, 15)  # 對應 -4
        v3 = IntegerOps.random_nonzero(-15, 15)  # 對應 -5
        v4 = IntegerOps.random_nonzero(-15, 15)  # 對應 21
        v5 = IntegerOps.random_nonzero(-15, 15)  # 對應 -125
        v6 = IntegerOps.random_nonzero(-15, 15)  # 對應 4
        v7 = IntegerOps.random_nonzero(-15, 15)  # 對應 -10
        
        op1 = random.choice(['*', '/'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['*', '/'])
        op4 = random.choice(['+', '-']) # 兩個區塊之間的加號
        op5 = random.choice(['*', '/'])
        op6 = random.choice(['+', '-'])
        
        try:
            # [Step 4: 安全字串運算分塊 (Safe Chunked Eval)]
            
            # 區塊 A: 絕對值內部 9 - 4 * (-5) + 21
            inner_str = f"{fmt(v1)} {op2} {fmt(v2)} {op1} ({fmt(v3)}) {op2} {fmt(v4)}"
            val_inner = eval(inner_str)
            # 安全轉換絕對值
            part_abs = abs(val_inner)
            
            # 區塊 B: 中括號內部 -125 * 4 ÷ (-10)
            bracket_str = f"{fmt(v5)} {op5} {fmt(v6)} {op6} {fmt(v7)}"
            part_bracket = eval(bracket_str)
            
            # 總和計算 (part_abs 和 part_bracket 之間的運算)
            ans = eval(f"{part_abs} {op4} {part_bracket}")
            
            # [Step 5: 黃金判斷 - 是否整除?]
            # 檢查是否為整數 (允許些微浮點誤差)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                
                # [Step 6: 成功！組裝 LaTeX]
                # 定義符號轉換 helper
                def to_latex(op):
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op
                
                l_op1 = to_latex(op1)
                l_op2 = to_latex(op2)
                l_op3 = to_latex(op3)
                l_op4 = to_latex(op4)
                l_op5 = to_latex(op5)
                l_op6 = to_latex(op6)
                
                # 填入 LaTeX (使用 fmt 處理負號)
                str_abs = f"|{fmt(v1)} {l_op2} {fmt(v2)} {l_op1} ({fmt(v3)}) {l_op2} {fmt(v4)}|"
                str_bracket = f"\\left[ {fmt(v5)} {l_op5} {fmt(v6)} {l_op6} {fmt(v7)} \\right]"
                
                math_str = f"{str_abs} {l_op4} {str_bracket}"
                
                question_text = r"計算 $$" + math_str + r"$$ 的值。"
                
                return {
                    'question_text': question_text,
                    'correct_answer': str(final_ans),
                    'mode': 1
                }
        except (ZeroDivisionError, SyntaxError): # Add SyntaxError for robustness with eval
            continue
            
    # 保底機制
    return {'question_text': "Error", 'correct_answer': "0", 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip(): return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6: return {'correct': True, 'result': '正確'}
    except: pass
    return {'correct': False, 'result': '錯誤'}