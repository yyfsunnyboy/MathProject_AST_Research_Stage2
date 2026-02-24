import random
from fractions import Fraction

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = [Fraction(random.randint(1, 10), random.randint(1, 10)) for _ in range(4)]
    while fractions[0].denominator == 0 or fractions[1].denominator == 0 or fractions[2].denominator == 0 or fractions[3].denominator == 0:
        fractions = [Fraction(random.randint(1, 10), random.randint(1, 10)) for _ in range(4)]
    
    part1 = f"({fractions[0].numerator}/{fractions[0].denominator}{ops[0]}{fractions[1].numerator}/{fractions[1].denominator})"
    part2 = f"{ops[1]}{fractions[2].numerator}/{fractions[2].denominator}"
    part3 = f"{ops[2]}{fractions[3].numerator}/{fractions[3].denominator}"
    part4 = f"|{fractions[0].numerator*fractions[2].numerator}/{fractions[0].denominator*fractions[2].denominator}{ops[3]}{fractions[3].numerator}/{fractions[3].denominator}|"
    
    question = f"計算 `{part1}{part2}{part3} + {part4}` 的值。"
    correct = str(Fraction(part1.replace('×', '*').replace('÷', '/').replace('(', '').replace(')', '') + part2 + part3 + '+' + part4.replace('×', '*').replace('÷', '/').replace('(', '').replace(')', '')))
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user = Fraction(user_answer)
        correct = Fraction(correct_answer)
        return {'correct': user == correct, 'result': '正確' if user == correct else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}