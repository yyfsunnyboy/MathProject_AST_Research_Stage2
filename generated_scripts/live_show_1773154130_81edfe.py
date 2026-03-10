def generate(level=1, **kwargs):
    question_text = '(-60) \\div [(-7) \times 2 - 1]'
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
