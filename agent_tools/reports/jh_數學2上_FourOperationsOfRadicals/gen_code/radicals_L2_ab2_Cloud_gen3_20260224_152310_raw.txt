import random
import math

def generate(level=1, **kwargs):
    radicands_pool = [2, 3, 5, 6, 7, 8, 10, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple_radicands = [2, 3, 5, 7]
    
    final_terms = {}
    
    if level == 1:
        terms_data = []
        for i in range(2):
            c = random.choice([x for x in range(-5, 6) if x != 0])
            r = random.choice(radicands_pool)
            terms_data.append((c, r))
        
        part_strs = []
        for i, (c, r) in enumerate(terms_data):
            s = RadicalOps.format_term_unsimplified(c, r, i == 0)
            part_strs.append(s)
            new_c, new_r = RadicalOps.simplify_term(c, r)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c
            
        question_text = f"化簡 $${''.join(part_strs)}$$"
        
    elif level == 2:
        terms_data = []
        for i in range(random.randint(3, 4)):
            c = random.choice([x for x in range(-5, 6) if x != 0])
            r = random.choice(radicands_pool)
            terms_data.append((c, r))
            
        part1_strs = []
        for i, (c, r) in enumerate(terms_data):
            s = RadicalOps.format_term_unsimplified(c, r, i == 0)
            part1_strs.append(s)
            new_c, new_r = RadicalOps.simplify_term(c, r)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c
            
        k = random.randint(2, 5)
        r_a = random.choice(simple_radicands)
        r_b = random.choice([x for x in simple_radicands if x != r_a])
        
        part2_latex = f"{k}(\\sqrt{{{r_a}}} + \\sqrt{{{r_b}}})"
        
        c_a, r_a_sim = RadicalOps.simplify_term(k, r_a)
        final_terms[r_a_sim] = final_terms.get(r_a_sim, 0) + c_a
        c_b, r_b_sim = RadicalOps.simplify_term(k, r_b)
        final_terms[r_b_sim] = final_terms.get(r_b_sim, 0) + c_b
        
        question_text = f"化簡 $$({''.join(part1_strs)}) + {part2_latex}$$"
        
    else:
        r_m = random.choice([2, 3, 5])
        r_n = random.choice([x for x in [2, 3, 5] if x != r_m])
        r_p = random.choice([2, 3, 5])
        r_q = random.choice([x for x in [2, 3, 5] if x != r_p])
        
        part_latex = f"(\\sqrt{{{r_m}}} + \\sqrt{{{r_n}}})(\\sqrt{{{r_p}}} - \\sqrt{{{r_q}}})"
        
        pairs = [(1, r_m * r_p), (1, r_m * r_q * -1), (1, r_n * r_p), (1, r_n * r_q * -1)]
        for c, r in pairs:
            sign = 1 if r > 0 else -1
            abs_r = abs(r)
            new_c, new_r = RadicalOps.simplify_term(c * sign, abs_r)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c
            
        question_text = f"化簡 $${part_latex}$$"

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