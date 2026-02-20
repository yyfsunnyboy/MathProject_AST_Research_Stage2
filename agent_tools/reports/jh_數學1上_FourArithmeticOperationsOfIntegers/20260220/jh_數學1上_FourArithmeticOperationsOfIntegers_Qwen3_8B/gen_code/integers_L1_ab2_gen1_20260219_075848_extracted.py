import random
import math
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        r_min, r_max = -20, 20
        div_max = 10
    elif level == 2:
        r_min, r_max = -50, 50
        div_max = 20
    else:
        r_min, r_max = -100, 100
        div_max = 30
        
    def rand_nz(a, b):
        choices = [x for x in range(a, b+1) if x != 0]
        return random.choice(choices)
    
    divisor = rand_nz(2, div_max)
    quotient = rand_nz(-15, 15)
    dividend = divisor * quotient
    
    m = rand_nz(2, 5)
    a_approx = dividend // m
    a = rand_nz(a_approx - 5, a_approx + 5)
    b = dividend - (a * m)
    
    part1_str = f"[({IntegerOps.fmt_num(a)} \\times {IntegerOps.fmt_num(m)}) + {IntegerOps.fmt_num(b)}] \\div {IntegerOps.fmt_num(divisor)}"
    part1_val = quotient
    
    d = rand_nz(-10, 15)
    e = rand_nz(-10, 10)
    f = rand_nz(1, 20)
    g = rand_nz(-10, 10)
    
    if level == 1:
        part2_str = f"|{IntegerOps.fmt_num(d)} \\times {IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)}|"
        part2_val = abs(d * e - f)
    else:
        part2_str = f"|{IntegerOps.fmt_num(d)} \\times {IntegerOps.fmt_num(e)} - {IntegerOps.fmt_num(f)} + {IntegerOps.fmt_num(g)}|"
        part2_val = abs(d * e - f + g)
    
    h = rand_nz(-10, 10)
    i = rand_nz(2, 5)
    j = rand_nz(1, 10)
    part3_str = f"({IntegerOps.fmt_num(h)} \\times {IntegerOps.fmt_num(i)} - {IntegerOps.fmt_num(j)})"
    part3_val = h * i - j
    
    k = rand_nz(-50, 50)
    
    if level == 1:
        question_text = f"計算 $${part1_str} + {part2_str}$$ 的值。"
        ans = part1_val + part2_val
    elif level == 2:
        question_text = f"計算 $${part1_str} - {part2_str} + {part3_str}$$ 的值。"
        ans = part1_val - part2_val + part3_val
    else:
        question_text = f"計算 $$- {part1_str} + {part2_str} - {part3_str} + {IntegerOps.fmt_num(k)}$$ 的值。"
        ans = -part1_val + part2_val - part3_val + k
        
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': str(int(ans)),
        'mode': 1
    }