def generate(level=1, **kwargs):
    from random import choice, randint
    terms_part1 = []
    for _ in range(3, 4):
        coeff = randint(1, 5)
        base = choice([2, 3, 5, 7])
        radicand = coeff**2 * base
        terms_part1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=bool(terms_part1)))
    part1 = '(' + '+'.join(terms_part1) + ')'
    
    k = randint(2, 4)
    terms_part2 = []
    for _ in range(2):
        coeff = randint(1, 3)
        base = choice([2, 3, 5, 7])
        radicand = coeff**2 * base
        terms_part2.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=bool(terms_part2)))
    part2 = f'{k}({"+".join(terms_part2)})'
    
    question_text = f'化簡 ${part1} + {part2}$'
    
    simplified_terms = []
    for term in terms_part1:
        coeff = int(term.split(' ')[0])
        radicand = int(term.split('}')[0].split(' ')[1][1:])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
    for term in terms_part2:
        coeff = int(term.split(' ')[0])
        radicand = int(term.split('}')[0].split(' ')[1][1:])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
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