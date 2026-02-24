import random
import math

def generate(level=1, **kwargs):
    question = ""
    answer = ""
    correct_answer = ""
    mode = 1

    if level == 1:
        a = random.randint(2, 10)
        b = random.randint(2, 10)
        c = random.randint(2, 10)
        d = random.randint(2, 10)
        e = random.randint(2, 10)
        f = random.randint(2, 10)
        g = random.randint(2, 10)
        h = random.randint(2, 10)
        i = random.randint(2, 10)
        j = random.randint(2, 10)
        k = random.randint(2, 10)
        l = random.randint(2, 10)
        m = random.randint(2, 10)
        n = random.randint(2, 10)
        o = random.randint(2, 10)
        p = random.randint(2, 10)
        q = random.randint(2, 10)
        r = random.randint(2, 10)
        s = random.randint(2, 10)
        t = random.randint(2, 10)
        u = random.randint(2, 10)
        v = random.randint(2, 10)
        w = random.randint(2, 10)
        x = random.randint(2, 10)
        y = random.randint(2, 10)
        z = random.randint(2, 10)

        term1 = f"{a}\\sqrt{{{b}}}"
        term2 = f"{c}\\sqrt{{{d}}}"
        term3 = f"{e}\\sqrt{{{f}}}"
        term4 = f"{g}\\sqrt{{{h}}}"
        term5 = f"{i}\\sqrt{{{j}}}"
        term6 = f"{k}\\sqrt{{{l}}}"
        term7 = f"{m}\\sqrt{{{n}}}"
        term8 = f"{o}\\sqrt{{{p}}}"
        term9 = f"{q}\\sqrt{{{r}}}"
        term10 = f"{s}\\sqrt{{{t}}}"
        term11 = f"{u}\\sqrt{{{v}}}"
        term12 = f"{w}\\sqrt{{{x}}}"
        term13 = f"{y}\\sqrt{{{z}}}"

        question = f"化簡 $({term1} + {term2} - {term3}) + ({term4} + {term5})(\\sqrt{{{term6}}} - {term7})$"
        answer = f"{term8} + {term9} + {term10} + {term11} + {term12} + {term13}"
        correct_answer = answer

    return {'question_text': question, 'answer': answer, 'correct_answer': correct_answer, 'mode': mode}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}