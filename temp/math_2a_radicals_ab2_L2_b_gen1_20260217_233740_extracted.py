def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    for _ in range(3, 5):
        coeff = randint(2, 5)
        radicand = choice([2, 3, 5, 6, 7, 10])
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand*randint(2, 5), is_first=len(terms1)==0))
    part1 = '(' + '+'.join(terms1) + ')'
    
    k = randint(2, 5)
    terms2 = []
    for _ in range(2):
        coeff = randint(2, 5)
        radicand = choice([2, 3, 5, 6, 7, 10])
        terms2.append(RadicalOps.format_term_unsimplified(coeff, radicand*randint(2, 5), is_first=len(terms2)==0))
    part2 = f'{k}({"+".join(terms2)})'
    
    question_text = f'化簡 ${part1} + {part2}$'
    
    simplified_terms = []
    for term in terms1:
        coeff = int(term.split(' ')[0])
        radicand = int(term.split('{')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
    simplified_terms2 = []
    for term in terms2:
        coeff = int(term.split(' ')[0])
        radicand = int(term.split('{')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms2.append((new_coeff, new_radicand))
    
    simplified_terms = simplified_terms + [(k * simplified_terms2[0][0], simplified_terms2[0][1])] + [(k * simplified_terms2[1][0], simplified_terms2[1][1])]
    
    terms_dict = {}
    for coeff, radicand in simplified_terms:
        if radicand in terms_dict:
            terms_dict[radicand] += coeff
        else:
            terms_dict[radicand] = coeff
    
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