# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 36.75s | Tokens: In=586, Out=921
# Created At: 2026-02-24 14:07:58
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def get_sq_free(n):
    coeff = 1
    temp = n
    d = 2
    while d * d <= temp:
        while temp % (d * d) == 0:
            coeff *= d
            temp //= (d * d)
        d += 1
    return coeff, temp

def format_term(c, b):
    if b == 1:
        return str(c)
    if c == 1:
        return "\\sqrt{" + str(b) + "}"
    if c == -1:
        return "-\\sqrt{" + str(b) + "}"
    return str(c) + "\\sqrt{" + str(b) + "}"

def generate(level=1, **kwargs):
    bases = [2, 3, 5, 6, 7, 10]
    b1 = random.choice(bases)
    b2 = random.choice([b for b in bases if b != b1])
    
    c1 = random.randint(1, 4)
    c2 = random.randint(1, 4)
    c3 = random.randint(1, 3)
    c4 = random.randint(1, 3)
    
    n1 = (c1**2) * b1
    n2 = (c2**2) * b1
    n3 = b2
    n4 = b1 * b2
    
    # Question: (\sqrt{n1} + \sqrt{n2}) + \sqrt{n3}(\sqrt{n4} - c4)
    # Part 1: c1\sqrt{b1} + c2\sqrt{b1} = (c1+c2)\sqrt{b1}
    # Part 2: \sqrt{b2} * \sqrt{b1*b2} = b2\sqrt{b1}
    # Part 3: \sqrt{b2} * -c4 = -c4\sqrt{b2}
    # Total: (c1+c2+b2)\sqrt{b1} - c4\sqrt{b2}
    
    q_text = "$(\\sqrt{" + str(n1) + "} + \\sqrt{" + str(n2) + "}) + \\sqrt{" + str(n3) + "}(\\sqrt{" + str(n4) + "} - " + str(c4) + ")$"
    
    res_dict = {}
    # Add (c1+c2+b2) for base b1
    res_dict[b1] = c1 + c2 + b2
    # Add -c4 for base b2
    res_dict[b2] = -c4
    
    sorted_bases = sorted(res_dict.keys())
    ans_parts = []
    for b in sorted_bases:
        c = res_dict[b]
        if c == 0: continue
        
        abs_c = abs(c)
        term = format_term(abs_c, b)
        
        if not ans_parts:
            if c < 0:
                ans_parts.append("-" + term)
            else:
                ans_parts.append(term)
        else:
            if c < 0:
                ans_parts.append(" - " + term)
            else:
                ans_parts.append(" + " + term)
    
    correct_ans = "".join(ans_parts) if ans_parts else "0"
    
    return {
        'question_text': q_text,
        'answer': '',
        'correct_answer': correct_ans,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}