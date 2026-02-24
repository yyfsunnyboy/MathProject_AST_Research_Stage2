import random
import math

def generate(level=1, **kwargs):
    ops = ['+', '-', '*']
    a = random.randint(2, 20)
    b = random.randint(2, 20)
    c = random.randint(2, 20)
    d = random.randint(2, 20)
    e = random.randint(2, 20)
    f = random.randint(2, 20)
    g = random.randint(2, 20)
    h = random.randint(2, 20)
    
    part1 = f"\\sqrt{{{a}}} + \\sqrt{{{b}}} - {random.randint(1,3)}\\sqrt{{{c}}}"
    part2 = f"(\\sqrt{{{d}}} + \\sqrt{{{e}}})(\\sqrt{{{f}}} - \\sqrt{{{g}}})"
    
    question = f"{part1} + {part2}"
    correct = f"{math.sqrt(a)+math.sqrt(b)-random.randint(1,3)*math.sqrt(c)} + {math.sqrt(d)*math.sqrt(f) + math.sqrt(e)*math.sqrt(f) - math.sqrt(d)*math.sqrt(g) - math.sqrt(e)*math.sqrt(g)}"
    
    return {
        'question_text': f"化簡 ${question}$",
        'answer': '',
        'correct_answer': f"{correct}",
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}