def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    for _ in range(3, 5):
        coeff = randint(1, 5)
        radicand = choice([2, 3, 5, 6, 7, 8, 10, 12, 15, 18, 20, 24, 27, 30])
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=len(terms1)==0))
    part1 = ''.join(terms1)
    
    k = randint(2, 4)
    radicands = [choice([2, 3, 5, 6, 7, 8, 10, 12, 15, 18, 20, 24, 27, 30]) for _ in range(2)]
    terms2 = []
    for i, rad in enumerate(radicands):
        terms2.append(RadicalOps.format_term_unsimplified(1, rad, is_first=i==0))
    part2 = f"{k}({'+'.join(terms2)})" if len(radicands) > 1 else f"{k}(\\sqrt{{{radicands[0]}}})"
    
    question_text = f"化簡 $${part1} + {part2}$$"
    
    simplified_terms = []
    for term in terms1.split('+'):
        coeff = int(term.split('sqrt')[0].strip())
        radicand = int(term.split('{')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
    k2 = int(part2.split('(')[0])
    radicands2 = [int(x.split('{')[1].split('}')[0]) for x in part2.split('(')[1].split(')')[0].split('+')]
    simplified_terms2 = []
    for rad in radicands2:
        new_coeff, new_radicand = RadicalOps.simplify_term(1, rad)
        simplified_terms2.append((new_coeff, new_radicand))
    
    terms_dict = {}
    for coeff, radicand in simplified_terms + [(k2 * c, r) for c, r in simplified_terms2]:
        if (radicand, 1) in terms_dict:
            terms_dict[(radicand, 1)] += coeff
        else:
            terms_dict[(radicand, 1)] = coeff
    
    correct_answer = RadicalOps.format_expression(terms_dict)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': str(user_answer).strip() == str(correct_answer).strip(),
        'result': '正確' if str(user_answer).strip() == str(correct_answer).strip() else '錯誤'
    }