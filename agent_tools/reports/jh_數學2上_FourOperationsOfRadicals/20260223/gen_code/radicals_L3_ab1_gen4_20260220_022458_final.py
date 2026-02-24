# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 77.53s | Tokens: In=586, Out=497
# Created At: 2026-02-20 02:24:58
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def format_radical(a, b):
    if a == 0:
        return "0"
    if b == 1:
        return str(a)
    if a == 1:
        return "\\sqrt{" + str(b) + "}"
    if a == -1:
        return "-\\sqrt{" + str(b) + "}"
    return str(a) + "\\sqrt{" + str(b) + "}"

def generate(level=1, **kwargs):
    m = random.choice([2, 3, 5, 7])
    nums = random.sample(range(2, 6 + level), 3)
    p, q, r = nums[0], nums[1], nums[2]
    n1 = m * p * p
    n2 = m * q * q
    n3 = m * r * r
    choice = random.randint(1, 3)
    if choice == 1:
        q_text = "\\sqrt{" + str(n1) + "} + \\sqrt{" + str(n2) + "} - \\sqrt{" + str(n3) + "}"
        ans_str = format_radical(p + q - r, m)
    elif choice == 2:
        q_text = "\\sqrt{" + str(n1) + "} \\times \\sqrt{" + str(m) + "}"
        ans_str = str(p * m)
    else:
        q_text = "(\\sqrt{" + str(n1) + "} + \\sqrt{" + str(n2) + "}) \\div \\sqrt{" + str(m) + "}"
        ans_str = str(p + q)
    return {
        'question_text': "Simplify $" + q_text + "$",
        'answer': '',
        'correct_answer': ans_str,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}