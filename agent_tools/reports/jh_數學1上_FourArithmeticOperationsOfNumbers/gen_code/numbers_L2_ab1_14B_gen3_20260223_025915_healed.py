import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '×', '÷']
    fractions = []
    for _ in range(4):
        numerator = random.randint(1, 10) * random.choice([-1, 1])
        denominator = random.randint(1, 10)
        fractions.append(f"{numerator}/{denominator}")
    
    part1 = f"({random.randint(-5,5)}{random.choice(ops)}{random.randint(-5,5)})×{fractions[0]}"
    part2 = f"{fractions[1]}÷({fractions[2]})" if random.random() > 0.5 else f"{fractions[1]}×({fractions[2]})"
    abs_expr = f"|{random.randint(1,10)}×({fractions[3]}){random.choice(['+', '-'])}{random.randint(1,10)}|"
    
    question = f"計算 $[{part1}] {random.choice(ops)} {part2} + {abs_expr}$ 的值。"
    
    # Calculate correct answer
    def eval_fraction(expr):
        expr = expr.replace('×', '*').replace('÷', '/')
        try:
            result = eval(expr)
            if result.is_integer():
                return str(int(result))
            else:
                return f"{result.as_integer_ratio()[0]}/{result.as_integer_ratio()[1]}"
        except:
            return "0"
    
    correct_answer = eval_fraction(f"({eval(part1)}) {random.choice(ops)} {eval(part2)} + {eval(abs_expr)}")
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    user = user_answer.strip()
    correct = correct_answer.strip()
    
    # Normalize answers
    def normalize(ans):
        if '/' in ans:
            parts = ans.split('/')
            numerator = int(parts[0])
            denominator = int(parts[1])
            gcd = math.gcd(abs(numerator), abs(denominator))
            return f"{numerator//gcd}/{abs(denominator)//gcd}"
        return ans
    
    return {
        'correct': normalize(user) == normalize(correct),
        'result': '正確' if normalize(user) == normalize(correct) else '錯誤'
    }