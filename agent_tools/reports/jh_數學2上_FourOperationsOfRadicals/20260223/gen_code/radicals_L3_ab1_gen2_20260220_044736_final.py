# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 178.14s | Tokens: In=631, Out=11445
# Created At: 2026-02-20 04:47:36
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    m_list = [2, 3, 5, 6, 7, 10, 11, 13, 14, 15]
    m = random.choice(m_list)
    a = random.randint(1, 5)
    b = random.randint(1, 5)
    c = random.randint(1, 5)
    k1 = random.randint(1, 3)
    k2 = random.randint(1, 3)
    k3 = random.randint(1, 3)
    first_simplified = a*k1 + b*k2 - c*k3
    first_part = f"({a*k1}\\sqrt{{{m}}} + {b*k2}\\sqrt{{{m}}} - {c*k3}\\sqrt{{{m}}})"

    a1 = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
    a2 = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
    b1 = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
    b2 = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15])
    term1 = f"\\sqrt{{{a1*b1}}}"
    term2 = f"-\\sqrt{{{a1*b2}}}"
    term3 = f"+\\sqrt{{{a2*b1}}}"
    term4 = f"-\\sqrt{{{a2*b2}}}"

    def simplify_term(n):
        if n == 0:
            return (0, 1)
        if n == 1:
            return (1, 1)
        max_square = 1
        for i in range(1, int(n**0.5) + 1):
            if n % (i*i) == 0:
                max_square = i*i
        remaining = n // max_square
        coefficient = int(max_square**0.5)
        return (coefficient, remaining)

    term1_coeff, term1_rad = simplify_term(a1*b1)
    term2_coeff, term2_rad = simplify_term(a1*b2)
    term3_coeff, term3_rad = simplify_term(a2*b1)
    term4_coeff, term4_rad = simplify_term(a2*b2)
    simplified_second = f"{term1_coeff}\\sqrt{{{term1_rad}}}{term2_coeff}\\sqrt{{{term2_rad}}}{term3_coeff}\\sqrt{{{term3_rad}}}{term4_coeff}\\sqrt{{{term4_rad}}}"

    correct_answer = f"{first_simplified}\\sqrt{{{m}}} + {simplified_second}"
    question_text = f"({first_part}) + ({term1} + {term2} + {term3} + {term4})"
    return {
        'question_text': f'${question_text}$',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}