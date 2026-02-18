def generate(level=1, **kwargs):
    terms1 = []
    for _ in range(3, 4):
        coeff = 1
        radicand = 18
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=len(terms1)==0))
    terms2 = []
    coeff = 3
    radicand1 = 12
    radicand2 = 27
    terms2.append(RadicalOps.format_term_unsimplified(1, radicand1, is_first=True))
    terms2.append(RadicalOps.format_term_unsimplified(1, radicand2, is_first=False))
    expr = f"({'+'.join(terms1)}) + {coeff}({'+'.join(terms2)})"
    simplified_terms = []
    for term in terms1:
        coeff, radicand = RadicalOps.simplify_term(term)
        simplified_terms.append((coeff, radicand))
    for term in terms2:
        coeff, radicand = RadicalOps.simplify_term(term)
        simplified_terms.append((coeff, radicand))
    correct_answer = RadicalOps.format_expression(simplified_terms)
    return {
        'question_text': f'化簡 ${expr}$',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': str(user_answer).strip() == str(correct_answer).strip(),
        'result': '正確' if str(user_answer).strip() == str(correct_answer).strip() else '錯誤'
    }