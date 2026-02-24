# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 79.34s | Tokens: In=586, Out=843
# Created At: 2026-02-20 02:31:25
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import math

def get_radical(n):
    c, r = 1, n
    d = 2
    while d * d <= r:
        while r % (d * d) == 0:
            c *= d
            r //= (d * d)
        d += 1
    return c, r

def format_ans(terms):
    keys = sorted(terms.keys(), reverse=True)
    parts = []
    for r in keys:
        c = terms[r]
        if c == 0: continue
        p = ""
        if c > 0 and parts:
            p += "+"
        if r == 1:
            p += str(c)
        else:
            if c == 1:
                p += "\\sqrt{" + str(r) + "}"
            elif c == -1:
                p += "-\\sqrt{" + str(r) + "}"
            else:
                p += str(c) + "\\sqrt{" + str(r) + "}"
        parts.append(p)
    return "".join(parts) if parts else "0"

def generate(level=1, **kwargs):
    nums = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75, 80]
    r_list = random.sample(nums, 3)
    c_list = [random.randint(1, 3) for _ in range(3)]
    m_list = random.sample([2, 3, 5, 6, 7, 10], 3)
    m4 = random.randint(1, 5)
    def term_str(c, r):
        if c == 1: return "\\sqrt{" + str(r) + "}"
        return str(c) + "\\sqrt{" + str(r) + "}"
    q = "(" + term_str(c_list[0], r_list[0]) + " + " + term_str(c_list[1], r_list[1]) + " - " + term_str(c_list[2], r_list[2]) + ") + (\\sqrt{" + str(m_list[0]) + "} + \\sqrt{" + str(m_list[1]) + "})(\\sqrt{" + str(m_list[2]) + "} - " + str(m4) + ")"
    res = {}
    def add(c, r):
        co, ra = get_radical(r)
        res[ra] = res.get(ra, 0) + c * co
    add(c_list[0], r_list[0])
    add(c_list[1], r_list[1])
    add(-c_list[2], r_list[2])
    add(1, m_list[0] * m_list[2])
    add(-m4, m_list[0])
    add(1, m_list[1] * m_list[2])
    add(-m4, m_list[1])
    return {
        'question_text': "Simplify $" + q + "$",
        'answer': '',
        'correct_answer': format_ans(res),
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}