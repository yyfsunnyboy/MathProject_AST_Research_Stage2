import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    
    last_ans = None
    last_math_str = None
    
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-100, -1)
        v2 = IntegerOps.random_nonzero(-100, -1)
        v3 = IntegerOps.random_nonzero(1, 100)
        v4 = IntegerOps.random_nonzero(1, 100)
        try:
            eval_str = f"({v1})/(({v2})*{v3}-{v4})"
            try:
                ans = safe_eval(eval_str)
                last_ans = ans
                last_math_str = f"({v1})\\div[({v2})\\times{fmt(v3)}-{fmt(v4)}]"
                
                # 倒算法 (Reverse Calculation) 替代：使用 Monte Carlo 尋找完美的整數解
                if type(ans).__name__ == "Fraction":
                    if ans.denominator == 1:
                        return {
                            'question_text': "計算 $" + last_math_str + "$ 的值。",
                            'correct_answer': str(ans.numerator),
                            'mode': 1
                        }
                elif abs(ans - round(ans)) < 1e-6:
                    return {
                        'question_text': "計算 $" + last_math_str + "$ 的值。",
                        'correct_answer': str(int(round(ans))),
                        'mode': 1
                    }
            except Exception:
                pass
        except Exception:
            continue
            
    # 如果 3000 次都找不到整數解，則退避到最後一次的浮點數或分數結果
    if last_ans is not None:
        if type(last_ans).__name__ == "Fraction":
            if last_ans.denominator == 1:
                final_ans = str(last_ans.numerator)
            else:
                final_ans = f"{last_ans.numerator}/{last_ans.denominator}"
        else:
            final_ans = f"{last_ans:.2f}"
        return {
            'question_text': "計算 $" + last_math_str + "$ 的值。",
            'correct_answer': final_ans,
            'mode': 1
        }
        
    return {'question_text': 'Error', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    try:
        if str(user_answer).strip() == str(correct_answer).strip():
            return {'correct': True, 'result': '正確'}
        if abs(float(user_answer) - float(correct_answer)) < 1e-6:
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}
