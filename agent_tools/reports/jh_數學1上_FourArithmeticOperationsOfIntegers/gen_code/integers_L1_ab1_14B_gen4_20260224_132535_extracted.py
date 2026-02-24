import random

def generate(level=1, **kwargs):
    question_text = ""
    answer = ""
    correct_answer = ""
    mode = 1

    if level == 1:
        num1 = random.randint(-50, 50)
        num2 = random.randint(-50, 50)
        num3 = random.randint(-50, 50)
        num4 = random.randint(-50, 50)
        num5 = random.randint(-50, 50)
        num6 = random.randint(-50, 50)
        op1 = random.choice(['+', '-'])
        op2 = random.choice(['+', '-'])
        op3 = random.choice(['+', '-'])
        op4 = random.choice(['+', '-'])
        op5 = random.choice(['+', '-'])
        abs_flag = random.choice([True, False])

        question = f"[({num1}{op1}{num2}){op2}({num3}{op3}{num4})]÷({num5}{op4}{num6})"
        if abs_flag:
            question += f"+|{num1}{op1}{num2}×{num3}{op3}{num4}-({num5}{op4}{num6})|"
        else:
            question += f"+{num1}{op1}{num2}×{num3}{op3}{num4}-({num5}{op4}{num6})"

        question_text = f"計算 `{question}` 的值。"

        # 計算正確答案
        try:
            expr = question.replace("÷", "/").replace("×", "*")
            correct_answer = str(eval(expr))
        except:
            correct_answer = ""

    return {
        'question_text': question_text,
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': mode
    }

def check(user_answer, correct_answer):
    try:
        user_answer = int(user_answer)
        correct_answer = int(correct_answer)
        correct = user_answer == correct_answer
    except:
        correct = False

    return {
        'correct': correct,
        'result': '正確' if correct else '錯誤'
    }