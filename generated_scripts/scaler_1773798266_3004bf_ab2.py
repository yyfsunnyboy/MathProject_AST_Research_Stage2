pattern_id
p2f_int_mult_rad
import random
c = random.choice([-3, -2, 2, 3])
r = 5
t1 = RadicalOps.format_term_unsimplified(c, r, True)
return {
    'question_text': f"化簡 ${t1}$",
    'correct_answer': RadicalOps.format_expression({r: c}),
    'mode': 1
}