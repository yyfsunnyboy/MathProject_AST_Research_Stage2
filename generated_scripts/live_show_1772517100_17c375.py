import random
import math

def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num
    for _ in range(3000):
        v1 = IntegerOps.random_nonzero(-20, -1)
        v2 = IntegerOps.random_nonzero(-20, -1)
        v3 = IntegerOps.random_nonzero(1, 20)
        v4 = IntegerOps.random_nonzero(1, 20)
        try:
            eval_str = f"({v1})/(({v2})*{v3}-{v4})"
            try:
                ans = safe_eval(eval_str)
                if type(ans).__name__ == "Fraction":
                    if ans.denominator == 1:
                        final_ans = str(ans.numerator)
                    else:
                        final_ans = f"{ans.numerator}/{ans.denominator}"
                elif abs(ans - round(ans)) < 1e-6:
                    final_ans = str(int(round(ans)))
                else:
                    final_ans = f"{ans:.2f}"
            except Exception:
                final_ans = "0"
            
            math_str = f"({v1})\\div[({v2})\\times{fmt(v3)}-{fmt(v4)}]"
            question_text = "計算 $" + math_str + "$ 的值。"
            return {
                'question_text': question_text,
                'correct_answer': final_ans,
                'mode': 1
            }
        except Exception:
            continue
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
