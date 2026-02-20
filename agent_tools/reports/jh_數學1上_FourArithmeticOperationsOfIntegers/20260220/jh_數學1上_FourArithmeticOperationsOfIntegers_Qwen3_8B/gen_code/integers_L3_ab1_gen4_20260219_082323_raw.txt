import random

def generate(level=1, **kwargs):
    structure = random.choice([1, 2, 3])
    if structure == 1:
        B = random.randint(-10, 10)
        while B == 0:
            B = random.randint(-10, 10)
        K = random.randint(-5, 5)
        C = random.randint(-5, 5)
        D = random.randint(-5, 5)
        E = random.randint(-5, 5)
        F = random.randint(-5, 5)
        A = B * K
        expr = f"[{B}×{K}] ÷ {B} × {C} + |{D}×{E} - {F}|"
        part1 = (A // B) * C
        part2 = abs(D * E - F)
        correct_answer = part1 + part2
    elif structure == 2:
        E = random.randint(-10, 10)
        while E == 0:
            E = random.randint(-10, 10)
        M = random.randint(-5, 5)
        D = E * M
        C = random.randint(-5, 5)
        A = random.randint(-10, 10)
        B = random.randint(-10, 10)
        F = random.randint(-5, 5)
        expr = f"[{A} + {B}] × {C} - |{D} ÷ {E} + {F}|"
        part1 = (A + B) * C
        part2 = abs(D // E + F)
        correct_answer = part1 - part2
    elif structure == 3:
        A = random.randint(-10, 10)
        B = random.randint(-10, 10)
        C = random.randint(-10, 10)
        D = random.randint(-10, 10)
        while D == 0:
            D = random.randint(-10, 10)
        E = random.randint(-10, 10)
        F = random.randint(-10, 10)
        expr = f"|{A}×{B} - {C}| ÷ {D} + {E} × {F}"
        part1 = abs(A * B - C) // D
        part2 = E * F
        correct_answer = part1 + part2
    return {
        'question_text': expr,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_num = int(user_answer)
        correct_num = int(correct_answer)
        return {'correct': user_num == correct_num, 'result': '正確' if user_num == correct_num else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}