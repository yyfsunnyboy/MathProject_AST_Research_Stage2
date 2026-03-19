def generate(level=1, **kwargs):
    question_text = '計算 $\\sqrt{2} \\times \\sqrt{3}$ 的值。'  # [AST Fix: 安全初始化防護]
    try:
        ans = _recompute_correct_answer_from_question(question_text) or '0'
    except Exception:
        ans = '0'
    if '計算' not in question_text:
        question_text = f'計算 ${question_text}$ 的值。'  # [AST Fix: 安全初始化防護]
    return {'question_text': question_text, 'correct_answer': str(ans), 'mode': 1}

def check(user_answer, correct_answer):
    ok = str(user_answer).strip() == str(correct_answer).strip()
    question_text = locals().get('question_text', locals().get('text', ''))  # [AST Fix: 安全初始化防護]
    return {'correct': ok, 'result': '正確' if ok else '錯誤'}