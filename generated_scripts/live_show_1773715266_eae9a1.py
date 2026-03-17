pattern_id = 'radical_division_same_root'
c1 = 7
r1 = 14
c2 = 1
r2 = 14
expr = sp.sqrt(c1 * r1) / sp.sqrt(c2 * r2)
ans_latex = sp.latex(sp.simplify(expr))
return {'question_text': question_text, 'correct_answer': ans_latex, 'solution_steps': ['利用根式除法性質:$\\sqrt{a} \\div \\sqrt{b} = \\sqrt{a/b}$,並化簡結果。'], 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate(level=1, **kwargs):
    return {'question_text': 'Fallback due to missing generate() wrapper', 'correct_answer': '\\text{Failed}'}