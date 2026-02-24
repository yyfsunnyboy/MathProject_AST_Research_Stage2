import random
import math
# RadicalOps is injected automatically

def generate(level=1, **kwargs):
    terms1_data = []
    for _ in range(random.randint(3, 4)):
        c = random.choice([x for x in range(-5, 6) if x != 0])
        r = random.choice([2, 3, 5, 6, 8, 12, 18, 20, 24, 27, 32, 50])
        terms1_data.append((c, r))
    part1_strs = []
    for i, (c, r) in enumerate(terms1_data):
        is_first = (i == 0)
        s = RadicalOps.format_term_unsimplified(c, r, is_first)
        part1_strs.append(s)
    part1_latex = "".join(part1_strs)
    k = random.randint(2, 5)
    r_a = random.choice([2, 3, 5, 7])
    r_b = random.choice([2, 3, 5, 7])
    part2_latex = f"{k}(\\sqrt{{{r_a}}} + \\sqrt{{{r_b}}})"
    question_text = f"化簡 $$({part1_latex}) + {part2_latex}$$"
    final_terms = {}
    for c, r in terms1_data:
        new_c, new_r = RadicalOps.simplify_term(c, r)
        final_terms[new_r] = final_terms.get(new_r, 0) + new_c
    c_a, r_a_sim = RadicalOps.simplify_term(k, r_a)
    final_terms[r_a_sim] = final_terms.get(r_a_sim, 0) + c_a
    c_b, r_b_sim = RadicalOps.simplify_term(k, r_b)
    final_terms[r_b_sim] = final_terms.get(r_b_sim, 0) + c_b
    correct_answer = RadicalOps.format_expression(final_terms)
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}