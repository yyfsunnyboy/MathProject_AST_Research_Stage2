import random
import math

def generate(level=1, **kwargs):
    terms1_data = []
    num_terms = random.randint(3, 4)
    radicands_pool = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    
    for i in range(num_terms):
        c = random.choice([x for x in range(-5, 6) if x != 0])
        r = random.choice(radicands_pool)
        terms1_data.append((c, r))
    
    part1_strs = []
    for i, (c, r) in enumerate(terms1_data):
        s = RadicalOps.format_term_unsimplified(c, r, is_first=(i == 0))
        part1_strs.append(s)
    part1_latex = "".join(part1_strs)
    
    k = random.randint(2, 4)
    r_a = random.choice([2, 3, 5, 6, 7, 10])
    r_b = random.choice([2, 3, 5, 6, 7, 10])
    while r_a == r_b:
        r_b = random.choice([2, 3, 5, 6, 7, 10])
        
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
    
    filtered_terms = {k: v for k, v in final_terms.items() if v != 0}
    if not filtered_terms:
        correct_answer = "0"
    else:
        correct_answer = RadicalOps.format_expression(filtered_terms)
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}