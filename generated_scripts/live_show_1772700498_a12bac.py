def generate(level=1, **kwargs):
    question_text = '計算 (-2 1/6)+1 2/9-(-1 1/3) 的值。\n\n【題型同構硬性約束】\n1) 運算子順序必須完全一致：divide -> plus -> divide -> minus -> divide\n2) 二元運算子總數必須一致：5\n2.1) 數字總數必須一致：6\n2.2) 加減乘除統計必須一致：+=1, -=1, ×=0, ÷=3\n3) 禁止新增中括號 []。\n4) 禁止新增絕對值符號 | | 或 abs()。\n5) 負數必須以括號形式表達（例如 (-7)）。\n6) 禁止新增未出現的運算子：times'
    try:
        from core.code_utils.live_show_math_utils import _recompute_correct_answer_from_question
        ans = _recompute_correct_answer_from_question(question_text) or "0"
    except Exception:
        ans = "0"
    if "計算" not in question_text:
        question_text = f"計算 ${question_text}$ 的值。"
    return {
        "question_text": question_text,
        "correct_answer": str(ans),
        "mode": 1
    }

def check(user_answer, correct_answer):
    ok = str(user_answer).strip() == str(correct_answer).strip()
    return {"correct": ok, "result": "正確" if ok else "錯誤"}
