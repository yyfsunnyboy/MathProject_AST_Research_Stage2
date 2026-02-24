import random
import math
# RadicalOps is injected automatically

def generate(level=1, **kwargs):
    if level == 1:
        terms1_data = [(random.choice([x for x in range(-5, 6) if x != 0]), random.choice([2, 3, 5, 6, 8, 12, 18, 20, 24, 27, 32, 50])) for _ in range(2)]
        part1_strs = [RadicalOps.format_term_unsimplified(c, r, i == 0) for i, (c, r) in enumerate(terms1_data)]
        part1_latex = "".join(part1_strs)
        question_text = f"化簡 $${part1_latex}$$"
        final_terms = {}
        for c, r in terms1_data:
            new_c, new_r = RadicalOps.simplify_term(c, r)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c
        correct_answer = RadicalOps.format_expression(final_terms)
        return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1}
    elif level == 2:
        terms1_data = [(random.choice([x for x in range(-5, 6) if x != 0]), random.choice([2, 3, 5, 6, 8, 12, 18, 20, 24, 27, 32, 50])) for _ in range(random.randint(3, 4))]
        part1_strs = [RadicalOps.format_term_unsimplified(c, r, i == 0) for i, (c, r) in enumerate(terms1_data)]
        part1_latex = "".join(part1_strs