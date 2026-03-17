pattern_id = "RadicalOps"  # 強制攔截器已啟動，此行將被刪除，但為確保同構，保留此註解

```python
import random
import sympy as sp

def generate(level=1, **kwargs):
    r1 = random.choice([5, 7, 11, 13])
    r2 = random.choice([5, 7, 11, 13])
    while r1 == r2:
        r2 = random.choice([5, 7, 11, 13])
    c1 = random.choice([1, 2, 3, 4])
    c2 = random.choice([1, 2, 3, 4])

    question_text = f"\\sqrt{{{r1}}} \\div \\sqrt{{{r2}}}"
    expr = sp.sqrt(r1) / sp.sqrt(r2)
    ans_latex = sp.latex(sp.simplify(expr))

    return {
        'question_text': question_text,
        'correct_answer': ans_latex,
        'solution_steps': ["將根式相除，化簡為單一根式。"],
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '正確'}