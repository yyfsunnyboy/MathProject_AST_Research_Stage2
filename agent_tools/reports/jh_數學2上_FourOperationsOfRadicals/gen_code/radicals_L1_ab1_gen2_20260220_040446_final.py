# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 123.44s | Tokens: In=631, Out=8215
# Created At: 2026-02-20 04:04:46
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    k1 = random.randint(1, 3)
    m1 = random.choice([2,3,5,6,7])
    a = k1**2 * m1
    k2 = random.randint(1, 3)
    m2 = random.choice([2,3,5,6,7])
    b = k2**2 * m2
    k3 = random.randint(1, 3)
    m3 = random.choice([2,3,5,6,7])
    d = k3**2 * m3
    c = random.randint(1, 3)
    first_part = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - {c}\\sqrt{{{d}}}"

    k4 = random.randint(1, 3)
    m4 = random.choice([2,3,5,6,7])
    e = k4**2 * m4
    k5 = random.randint(1, 3)
    m5 = random.choice([2,3,5,6,7])
    f = k5**2 * m5
    k6 = random.randint(1, 3)
    m6 = random.choice([2,3,5,6,7])
    g = k6**2 * m6
    h = random.randint(1, 3)
    second_part = f"(\\sqrt{{{e}}} + \\sqrt{{{f}}})\\left(\\sqrt{{{g}}} - {h}\\right)"

    question_text = f"({first_part}) + ({second_part})"
    first_simplified = f"{k1}\\sqrt{{{m1}}} + {k2}\\sqrt{{{m2}}} - {c}{k3}\\sqrt{{{m3}}}"
    term1 = f"{k4}{k6}\\sqrt{{{m4 * m6}}}"
    term2 = f"- {h}{k4}\\sqrt{{{m4}}}"
    term3 = f"{k5}{k6}\\sqrt{{{m5 * m6}}}"
    term4 = f"- {h}{k5}\\sqrt{{{m5}}}"
    second_simplified = f"{term1} + {term2} + {term3} + {term4}"
    correct_answer = f"({first_simplified}) + ({second_simplified})"
    return {
        'question_text': f"${question_text}$",
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}