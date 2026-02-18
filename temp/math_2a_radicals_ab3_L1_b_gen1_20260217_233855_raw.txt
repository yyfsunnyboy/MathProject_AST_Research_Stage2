def generate(level=1, **kwargs):
    from random import choice, randint
    terms1 = []
    radicands = [2,3,5,7,10]
    for _ in range(3):
        k = randint(2,5)
        r = choice(radicands)
        coeff = k*k*r
        terms1.append(RadicalOps.format_term_unsimplified(coeff, r, is_first=len(terms1)==0))
    part1 = ''.join(terms1)
    k2 = randint(2,4)
    radicands2 = [2,3,5]
    terms2 = []
    for _ in range(2):
        r = choice(radicands2)
        terms2.append(RadicalOps.format_term_unsimplified(1, r, is_first=len(terms2)==0))
    part2 = f'{k2}({"".join(terms2)})'
    question = f'化簡 $({part1}) + {part2}$'
    simplified_terms = []
    for term in terms1:
        coeff = int(term.split('√')[0])
        radicand = int(term.split('√')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        simplified_terms.append((new_coeff, new_radicand))
    k2_terms = []
    for term in terms2:
        coeff = int(term.split('√')[0])
        radicand = int(term.split('√')[1].split('}')[0])
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        k2_terms.append((new_coeff, new_radicand))
    k2_total = sum([x[0] for x in k2_terms])
    simplified = []
    for coeff, radicand in simplified_terms:
        simplified.append((coeff, radicand))
    for coeff, radicand in k2_terms:
        simplified.append((coeff*k2, radicand))
    grouped = {}
    for coeff, radicand in simplified:
        if radicand in grouped:
            grouped[radicand] += coeff
        else:
            grouped[radicand] = coeff
    sorted_terms = sorted(grouped.items(), key=lambda x: x[1], reverse=True)
    answer_parts = []
    for radicand, coeff in sorted_terms:
        if coeff > 0:
            answer_parts.append(RadicalOps.format_term(coeff, radicand, is_first=len(answer_parts)==0))
        else:
            answer_parts.append(RadicalOps.format_term(coeff, radicand, is_first=len(answer_parts)==0))
    correct_answer = ''.join(answer_parts)
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': str(user_answer).strip() == str(correct_answer).strip(),
        'result': '正確' if str(user_answer).strip() == str(correct_answer).strip() else '錯誤'
    }