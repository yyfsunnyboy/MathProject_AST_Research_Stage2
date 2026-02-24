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
        r_inner1 = random.choice(simple_radicands)
        r_inner2 = random.choice([x for x in simple_radicands if x != r_inner1])
        r_inner3 = random.choice(simple_radicands)
        r_inner4 = random.choice([x for x in simple_radicands if x != r_inner3])
        
        c1, c2, c3, c4 = [random.choice([x for x in range(-3, 4) if x != 0]) for _ in range(4)]
        
        term1_latex = RadicalOps.format_expression({r_inner1: c1, r_inner2: c2})
        term2_latex = RadicalOps.format_expression({r_inner3: c3, r_inner4: c4})
        
        question_text = f"化簡 $$({term1_latex})({term2_latex})$$"
        
        pairs = [(c1, r_inner1, c3, r_inner3), (c1, r_inner1, c4, r_inner4), 
                 (c2, r_inner2, c3, r_inner3), (c2, r_inner2, c4, r_inner4)]
        
        for ca, ra, cb, rb in pairs:
            new_c, new_r = RadicalOps.simplify_term(ca * cb, ra * rb)
            final_terms[new_r] = final_terms.get(new_r, 0) + new_c

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