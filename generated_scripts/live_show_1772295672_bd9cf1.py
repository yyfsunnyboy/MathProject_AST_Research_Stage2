import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    # [Step 1: 定義重試迴圈]
    for _ in range(3000):
        
        # [Step 2: 隨機生成變數 (依據圖片結構 3 個數字)]
        v1 = IntegerOps.random_nonzero(-15, 15)  # 對應 -9
        v2 = IntegerOps.random_nonzero(15, 30)   # 對應 24
        v3 = IntegerOps.random_nonzero(-10, 10)  # 對應 -8
        
        # [Step 3: 隨機生成運算符 (2個符號)]
        op1 = random.choice(['*', '/'])
        op2 = random.choice(['+', '-'])
        
        try:
            # [Step 4: 安全字串運算分塊 (Safe Chunked Eval)]
            
            # 區塊 A: 中括號內部 [24 - 8 * (-2)]
            bracket_str = f"{v2} {op2} {v3} {op1} ({-2})"
            val_bracket = eval(bracket_str)
            
            # 總和計算 (v1 和 val_bracket 之間的運算)
            ans = eval(f"{fmt(v1)} \\times {val_bracket}")
            
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
                
                # 填入 LaTeX (使用 fmt 處理負號)
                str_bracket = f"\\left[ {fmt(v2)} {l_op2} {fmt(v3)} {l_op1} (-2) \\right]"
                
                math_str = f"({fmt(v1)}) \\times {str_bracket}"
                
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