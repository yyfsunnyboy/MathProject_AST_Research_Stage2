def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    for _ in range(3, 5):
        coeff = randint(1, 5)
        radicand = choice([2, 3, 5, 6, 7, 8, 10, 12, 15, 18, 20, 24, 27, 30])
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=bool(terms1)))
    part1 = ''.join(terms1)
    
    k = randint(2, 5)
    radicands = [choice([2, 3, 5, 6, 7, 10, 12, 15, 18, 20, 24, 27, 30]) for _ in range(2)]
    signs = ['+', '-'][randint(0,1)]
    part2 = f"{k}({RadicalOps.format_term_unsimplified(1, radicands[0], is_first=True)}{signs}{RadicalOps.format_term_unsimplified(1, radicands[1], is_first=False)})"

    question_text = f'化簡 $${part1} + {part2}$$'
    
    simplified_terms = []
    for term in terms1.split('+'):
        term = term.strip()
        if '-' in term:
            coeff, radicand = term.split('√')
            coeff = int(coeff)
            radicand = int(radicand)
            simplified = RadicalOps.simplify_term(coeff, radicand)
            simplified_terms.append(RadicalOps.format_term(simplified[0], simplified[1], is_first=bool(simplified_terms)))
        else:
            coeff, radicand = term.split('√')
            coeff = int(coeff)
            radicand = int(radicand)
            simplified = RadicalOps.simplify_term(coeff, radicand)
            simplified_terms.append(RadicalOps.format_term(simplified[0], simplified[1], is_first=bool(simplified_terms)))
    
    k_part = part2.split('(')[0]
    k = int(k_part)
    radicands = part2.split('(')[1].split(')')[0].split()
    signs = [1 if '+' in radicands[i] else -1 for i in range(len(radicands))]
    radicands = [int(r.split('√')[1]) for r in radicands]
    simplified_k_terms = []
    for i in range(len(radicands)):
        coeff = 1 * k * signs[i]
        radicand = radicands[i]
        simplified = RadicalOps.simplify_term(coeff, radicand)
        simplified_k_terms.append(RadicalOps.format_term(simplified[0], simplified[1], is_first=bool(simplified_k_terms)))
    
    all_simplified_terms = simplified_terms + simplified_k_terms
    correct_answer = RadicalOps.format_expression(all_simplified_terms)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return str(user_answer).strip() == str(correct_answer).strip()
    except:
        return False