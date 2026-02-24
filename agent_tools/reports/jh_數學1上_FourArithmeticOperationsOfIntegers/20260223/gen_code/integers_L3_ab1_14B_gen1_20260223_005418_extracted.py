import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '÷', '×']
    nums = []
    for _ in range(4):
        if level == 1:
            num = random.randint(-50, 50)
        else:
            num = random.randint(-100, 100)
        nums.append(num)
    
    a, b, c, d = nums
    e = random.randint(-20, 20)
    f = random.randint(-20, 20)
    
    # Ensure division is valid
    while c == 0:
        c = random.randint(-20, 20)
    while d == 0:
        d = random.randint(-20, 20)
    
    # Calculate parts
    part1 = a + b
    part2 = part1 // c
    part3 = part2 * d
    part4 = e * f
    part5 = part4 - random.randint(-20, 20)
    abs_val = abs(part5)
    
    # Build question text
    question = f"[({a}{ops[0]}{b})]{ops[1]}{c}{ops[2]}{d}+|{e}{ops[3]}{f}{ops[0]}{random.randint(-20, 20)}|"
    
    # Calculate correct answer
    correct_answer = part3 + abs_val
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(correct_answer),
        'mode': 1
    }

def check(user_answer, correct_answer):
    return {
        'correct': user_answer == correct_answer,
        'result': '正確' if user_answer == correct_answer else '錯誤'
    }