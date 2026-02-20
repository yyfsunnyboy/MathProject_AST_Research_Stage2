import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*', '/']
    a = random.randint(2, 20)
    b = random.randint(2, 20)
    c = random.randint(2, 20)
    d = random.randint(2, 20)
    e = random.randint(2, 20)
    f = random.randint(2, 20)
    op1 = random.choice(ops)
    op2 = random.choice(ops)
    op3 = random.choice(ops)
    
    expr = f"(${\\sqrt{{{a}}} + \\sqrt{{{b}}}} {op1} {\\sqrt{{{c}}}} {op2} {\\sqrt{{{d}}}} {op3} {\\sqrt{{{e}}}} {op3} {\\sqrt{{{f}}}}$)"
    
    # Simplify and calculate correct answer
    def simplify(radical):
        val = radical
        for i in range(2, int(math.sqrt(val)) + 1):
            while val % (i*i) == 0:
                val //= i*i
        return val
    
    parts = []
    parts.append(f"{math.isqrt(a)}\\sqrt{{{simplify(a)}}}")
    parts.append(f"{math.isqrt(b)}\\sqrt{{{simplify(b)}}}")
    parts.append(f"{math.isqrt(c)}\\sqrt{{{simplify(c)}}}")
    parts.append(f"{math.isqrt(d)}\\sqrt{{{simplify(d)}}}")
    parts.append(f"{math.isqrt(e)}\\sqrt{{{simplify(e)}}}")
    parts.append(f"{math.isqrt(f)}\\sqrt{{{simplify(f)}}}")
    
    correct_answer = f"{sum([math.isqrt(a), math.isqrt(b), -math.isqrt(c), -math.isqrt(d), math.isqrt(e), math.isqrt(f)])}\\sqrt{{{simplify(a)}}}"
    
    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}