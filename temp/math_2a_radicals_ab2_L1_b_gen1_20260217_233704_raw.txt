def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    for _ in range(3, 5):
        coeff = randint(1, 5)
        radicand = choice([18, 50, 8, 12, 27, 20, 45, 18, 50])
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=len(terms1)==0))
    part1 = '(' + '+'.join(terms1).replace('+ -', '-').replace('+-', '-') + ')'
    
    k = randint(2, 5)
    radicands = choice([[12, 27], [20, 45], [8, 18]])
    terms2 = []
    for i, r in enumerate(radicands):
        coeff = 1 if i == 0 else -1
        terms2.append(RadicalOps.format_term_unsimplified(coeff, r, is_first=i==0))
    part2 = f'{k}({"+".join(terms2).replace("+ -", "-").replace("+-", "-")})'
    
    question_text = f'化簡 ${part1} + {part2}$'
    
    simplified_terms = []
    for term in terms1:
        coeff = int(term.split('√')[0].replace(' ', ''))
        radicand = int(term.split('√')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
    for term in terms2:
        coeff = int(term.split('√')[0].replace(' ', ''))
        radicand = int(term.split('√')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    
    correct_answer = RadicalOps.format_expression(simplified_terms, denominator=1)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return abs(eval(user_answer) - eval(correct_answer)) < 1e-6
    except:
        return str(user_answer).strip() == str(correct_answer).strip()