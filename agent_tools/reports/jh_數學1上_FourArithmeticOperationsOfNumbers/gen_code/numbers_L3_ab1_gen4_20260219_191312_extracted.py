import random
import math

def generate(level=1, **kwargs):
    def simplify_fraction(numerator, denominator):
        if denominator == 0:
            return (0, 1)
        gcd_val = math.gcd(abs(numerator), abs(denominator))
        return (numerator // gcd_val, denominator // gcd_val)
    
    def fraction_to_str(frac):
        num, den = frac
        if den == 1:
            return str(num)
        return f"{num}/{den}"
    
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        while denominator == 0:
            denominator = random.randint(1, 10)
        return (numerator, denominator)
    
    def generate_operation():
        ops = ['+', '-', '×', '÷']
        return random.choice(ops)
    
    def generate_abs_part():
        part1 = generate_fraction()
        part2 = generate_fraction()
        op = generate_operation()
        expr = f"{fraction_to_str(part1)} {op} {fraction_to_str(part2)}"
        return expr
    
    def generate_bracket_part():
        part1 = generate_fraction()
        part2 = generate_fraction()
        op = generate_operation()
        expr = f"({fraction_to_str(part1)} {op} {fraction_to_str(part2)})"
        return expr
    
    def calculate(expr):
        try:
            return eval(expr)
        except:
            return None
    
    part1 = generate_bracket_part()
    part2 = generate_fraction()
    op1 = generate_operation()
    part3 = generate_abs_part()
    op2 = generate_operation()
    
    question = f"[{part1} {op1} {fraction_to_str(part2)}] {op2} {part3}"
    
    def compute_answer():
        try:
            bracket_result = calculate(part1 + op1 + fraction_to_str(part2))
            bracket_result = simplify_fraction(bracket_result[0], bracket_result[1])
            abs_result = calculate(part3)
            abs_result = simplify_fraction(abs_result[0], abs_result[1])
            final_result = simplify_fraction(
                (bracket_result[0] * abs_result[1] + abs_result[0] * bracket_result[1]) 
                if op2 == '+' else 
                (bracket_result[0] * abs_result[1] - abs_result[0] * bracket_result[1]) 
                if op2 == '-' else 
                (bracket_result[0] * abs_result[1] * abs_result[0] * bracket_result[1]) 
                if op2 == '×' else 
                (bracket_result[0] * abs_result[1] / (abs_result[0] * bracket_result[1]))
            )
            return fraction_to_str(final_result)
        except:
            return ""
    
    correct_answer = compute_answer()
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        user_frac = tuple(map(int, user_answer.split('/'))) if '/' in user_answer else (int(user_answer), 1)
        correct_frac = tuple(map(int, correct_answer.split('/'))) if '/' in correct_answer else (int(correct_answer), 1)
        
        user_num, user_den = user_frac
        correct_num, correct_den = correct_frac
        
        if user_den == 0 or correct_den == 0:
            return {'correct': False, 'result': '錯誤'}
        
        user_gcd = math.gcd(abs(user_num), abs(user_den))
        correct_gcd = math.gcd(abs(correct_num), abs(correct_den))
        
        user_simplified = (user_num // user_gcd, user_den // user_gcd)
        correct_simplified = (correct_num // correct_gcd, correct_den // correct_gcd)
        
        return {'correct': user_simplified == correct_simplified, 'result': '正確' if user_simplified == correct_simplified else '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}