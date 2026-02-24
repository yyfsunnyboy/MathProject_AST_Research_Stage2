# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfNumbers
# Model: qwen3-14b | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: DISABLED | Advanced Healer: OFF
# Performance: 54.76s | Tokens: In=636, Out=1593
# Created At: 2026-02-23 02:58:22
# Fix Status: [Bare] | Fixes: Basic=0, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PENDING
# ==============================================================================
import random
import fractions

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions1 = [str(fractions.Fraction(random.randint(-10, 10), random.randint(1, 10))) for _ in range(2)]
    fractions2 = [str(fractions.Fraction(random.randint(-10, 10), random.randint(1, 10))) for _ in range(2)]
    fractions3 = [str(fractions.Fraction(random.randint(-10, 10), random.randint(1, 10))) for _ in range(2)]
    
    part1 = f"({fractions1[0]}{random.choice(ops)}{fractions1[1]}){random.choice(['×', '÷'])}{fractions2[0]}"
    part2 = f"|{fractions3[0]}×{fractions3[1]}{random.choice(['+', '-'])}{fractions2[1]}|"
    question_text = f"計算 ${part1} {random.choice(['+', '-'])} {part2}$ 的值"
    
    expr = f"({fractions1[0]} + {fractions1[1]}) * {fractions2[0]} / {fractions2[1]} + abs({fractions3[0]} * {fractions3[1]} - {fractions2[1]})"
    correct_answer = str(fractions.Fraction(eval(expr)))
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = str(fractions.Fraction(user_answer))
        correct = str(fractions.Fraction(correct_answer))
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}