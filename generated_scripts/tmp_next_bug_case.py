from fractions import Fraction

def generate(level=1, **kwargs):
    eval_str_init = "Fraction(2,3)+Fraction(1,6)"
    ans = IntegerOps.safe_eval(eval_str_init)
    return {"question_text":"計算 $2/3+1/6$ 的值。", "correct_answer": str(ans)}

def check(user_answer, correct_answer):
    return {"correct": str(user_answer).strip()==str(correct_answer).strip(), "result":"正確" if str(user_answer).strip()==str(correct_answer).strip() else "錯誤"}
