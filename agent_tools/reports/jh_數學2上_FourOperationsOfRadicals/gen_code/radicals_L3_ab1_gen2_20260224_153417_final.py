# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 297.53s | Tokens: In=586, Out=815
# Created At: 2026-02-24 15:34:17
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def simplify(n):
    coeff, base = 1, n
    d = 2
    while d * d <= base:
        while base % (d * d) == 0:
            coeff *= d
            base //= (d * d)
        d += 1
    return coeff, base

def format_res(res_dict):
    sorted_bases = sorted(res_dict.keys())
    parts = []
    for b in sorted_bases:
        c = res_dict[b]
        if c == 0:
            continue
        sign = "+" if c > 0 else "-"
        abs_c = abs(c)
        if b == 1:
            term = str(abs_c)
        else:
            c_str = str(abs_c) if abs_c != 1 else ""
            term = f"{c_str}\\sqrt{{{b}}}"
        if not parts:
            parts.append(f"{'' if sign == '+' else '-'}{term}")
        else:
            parts.append(f"{sign}{term}")
    return "".join(parts) if parts else "0"

def generate(level=1, **kwargs):
    res_dict = {}
    if level == 1:
        b_list = [2, 3, 5, 6, 7, 10]
        chosen_bases = random.sample(b_list, 2)
        terms = []
        for i in range(3):
            base = chosen_bases[0] if i < 2 else chosen_bases[1]
            a = random.randint(2, 5)
            k = random.randint(1, 3)
            coeff = k if random.random() > 0.5 else -k
            val = (a**2) * base
            res_dict[base] = res_dict.get(base, 0) + (coeff * a)
            abs_k = abs(coeff)
            k_str = str(abs_k) if abs_k != 1 else ""
            t_str = f"{k_str}\\sqrt{{{val}}}"
            if i == 0:
                terms.append(f"{'' if coeff > 0 else '-'}{t_str}")
            else:
                terms.append(f"{'+' if coeff > 0 else '-'}{t_str}")
        question = "".join(terms)
    else:
        n = [random.choice([2, 3, 5, 6, 7, 8, 10, 12]) for _ in range(4)]
        for i in range(2):
            for j in range(2, 4):
                c, b = simplify(n[i] * n[j])
                res_dict[b] = res_dict.get(b, 0) + c
        question = f"(\\sqrt{{{n[0]}}} + \\sqrt{{{n[1]}}})(\\sqrt{{{n[2]}}} + \\sqrt{{{n[3]}}})"
    
    return {
        'question_text': f"Simplify ${question}$",
        'answer': '',
        'correct_answer': format_res(res_dict),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}