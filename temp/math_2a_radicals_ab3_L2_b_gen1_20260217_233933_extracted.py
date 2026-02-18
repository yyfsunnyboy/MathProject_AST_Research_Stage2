def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    for _ in range(3, 4):
        coeff = randint(1, 5)
        radicand = choice([18, 50, 8, 12, 27, 20, 45, 75])
        terms1.append(RadicalOps.format_term_unsimplified(coeff, radicand, is_first=bool(terms1)))
    k = randint(2, 4)
    radicands = [choice([3, 5, 7, 11, 13]), choice([3, 5, 7, 11, 13])]
    part2 = f"{k}({RadicalOps.format_term_unsimplified(1, radicands[0], is_first=True)} {RadicalOps.format_term_unsimplified(1, radicands[1], is_first=False)})"
    question = f"化簡 $({'+'.join(terms1)}) + {part2}$"
    simplified_terms = []
    for t in terms1:
        coeff = int(t.split(' ')[0])
        radicand = int(t.split('{')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    k_part = k
    radicand1 = radicands[0]
    radicand2 = radicands[1]
    new_coeff1, new_radicand1 = RadicalOps.simplify_term(k_part, radicand1)
    new_coeff2, new_radicand2 = RadicalOps.simplify_term(k_part, radicand2)
    simplified_terms.extend([(new_coeff1, new_radicand1), (new_coeff2, new_radicand2)])
    terms_dict = {}
    for coeff, radicand in simplified_terms:
        if radicand in terms_dict:
            terms_dict[radicand] += coeff
        else:
            terms_dict[radicand] = coeff
    sorted_terms = sorted(terms_dict.items(), key=lambda x: x[0])
    correct_answer = RadicalOps.format_expression(terms_dict)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        return abs(eval(user_answer) - eval(correct_answer)) < 1e-6
    except:
        return str(user_answer).strip() == str(correct_answer).strip()