# ==============================================================================
# ID: jh_數學2上_FourOperationsOfRadicals
# Model: qwen3-8b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 194.16s | Tokens: In=631, Out=12328
# Created At: 2026-02-20 04:16:28
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random

def generate(level=1, **kwargs):
    square_free = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
    square_numbers = [random.choice([1, 4, 9, 16, 25, 36, 49, 64, 81, 100]) for _ in range(3)]
    coefficients = [random.randint(1, 5) for _ in range(3)]
    terms = []
    for i in range(3):
        radicand = square_numbers[i] * square_free
        term = f"{coefficients[i]}\\sqrt{{{radicand}}}"
        if i == 2:
            term = f"-{term[1:]}"
        terms.append(term)
    first_part = " + ".join(terms)

    a = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
    b = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
    binomial1 = f"\\sqrt{{{a}}} + \\sqrt{{{b}}}"

    c = random.choice([2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23, 26, 29, 30, 31, 33, 34, 35, 37, 38, 39, 41, 42, 43, 46, 47, 49, 51, 53, 55, 57, 58, 59, 61, 62, 65, 66, 67, 69, 71, 73, 74, 77, 78, 79, 82, 83, 85, 86, 87, 89, 91, 93, 94, 95, 97, 101])
    d = random.randint(1, 5)
    binomial2 = f"\\sqrt{{{c}}} - {d}"

    second_part = f"({binomial1})({binomial2})"

    question = f"({first_part}) + ({second_part})"
    correct_answer = "4\\sqrt{2} + 2\\sqrt{2} + \\sqrt{3}"

    return {
        'question_text': f'${question}$',
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}