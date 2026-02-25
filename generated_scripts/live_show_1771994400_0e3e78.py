import random
from fractions import Fraction

def generate(level=1, **kwargs):
    def fmt(f):
        s = str(f)
        return f"({s})" if f < 0 else s
    
    n_terms = 2 if level == 1 else 3
    terms = []
    for _ in range(n_terms):
        n = random.randint(-12, 12)
        d = random.randint(1, 10)
        terms.append(Fraction(n, d))
        
    ops = [('+', '+'), ('-', '-'), ('*', '×'), ('/', '÷')]
    q_text = fmt(terms[0])
    ans_val = terms[0]
    
    for i in range(1, n_terms):
        op_type, op_char = random.choice(ops)
        nxt = terms[i]
        if op_type == '/' and nxt == 0:
            nxt = Fraction(random.randint(1, 5), random.randint(1, 5))
        
        q_text += f" {op_char} {fmt(nxt)}"
        
        if op_type == '+': ans_val += nxt
        elif op_type == '-': ans_val -= nxt
        elif op_type == '*': ans_val *= nxt
        elif op_type == '/': ans_val /= nxt
        
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': str(ans_val),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        u_str = str(user_answer).strip().replace(' ', '')
        c_str = str(correct_answer).strip().replace(' ', '')
        is_correct = (Fraction(u_str) == Fraction(c_str))
    except:
        is_correct = False
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }