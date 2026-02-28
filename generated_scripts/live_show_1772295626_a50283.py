import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    # [Step 1: 定義重試迴圈]
    # 不管題目長短，直接跑 3000 次測試
    for _ in range(3000):
        
        # [Step 2: 隨機生成變數 (依據圖片結構 3 個數字)]
        v1 = IntegerOps.random_nonzero(-15, 15)  # 對應 -56
        v2 = IntegerOps.random_nonzero(2, 9)     # 對應 6
        v3 = IntegerOps.random_nonzero(-10, 10)  # 對應 -7
        
        # [Step 3: 隨機生成運算符 (2個符號)]
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['*', '/'])
        
        try:
            # [Step 4: 安全字串運算分塊 (Safe Chunked Eval)]
            
            # 區塊 A: 中括號內部 [6 + 2 * (-7)]
            # 注意：圖片中是 6 + 2 * (-7)，但我們要確保運算順序正確
            # 因此，我們直接構造字串並用 eval 計算
            bracket_str = f"{v2} {op1} {v3} {op2} {v3}"
            # 但圖片中是 6 + 2 * (-7)，所以我們需要調整變數
            # 重新定義：讓 v2 = 6, v3 = -7, 並固定運算符為 '+' 和 '*'
            # 但為了保持隨機性，我們保留原結構，但強制運算順序
            # 這裡我們直接使用圖片中的結構：6 + 2 * (-7)
            # 所以我們需要重新定義變數
            v2_fixed = 6
            v3_fixed = -7
            bracket_str = f"{v2_fixed} + 2 * {fmt(v3_fixed)}"
            val_bracket = eval(bracket_str)
            
            # 總和計算 (v1 ÷ val_bracket)
            ans = eval(f"{fmt(v1)} \\div {val_bracket}")
            
            # [Step 5: 黃金判斷 - 是否整除?]
            # 檢查是否為整數 (允許些微浮點誤差)
            if abs(ans - round(ans)) < 1e-6:
                final_ans = int(round(ans))
                
                # [Step 6: 成功！組裝 LaTeX]
                # 定義符號轉換 helper
                def to_latex(op):
                    if op == '+': return '+'
                    if op == '-': return '-'
                    if op == '*': return '\\times'
                    if op == '/': return '\\div'
                    return op
                
                # 填入 LaTeX (使用 fmt 處理負號)
                str_dividend = fmt(v1)
                str_bracket = f"\\left[ {v2_fixed} + 2 \\times {fmt(v3_fixed)} \\right]"
                
                math_str = f"{str_dividend} \\div {str_bracket}"
                
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