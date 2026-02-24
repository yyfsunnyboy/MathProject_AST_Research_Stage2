import random
import math

def generate(level=1, **kwargs):
    if level == 1:
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        c = random.randint(1, 5)
        d = random.randint(1, 5)
        e = random.randint(1, 5)
        f = random.randint(1, 5)
        g = random.randint(1, 5)
        h = random.randint(1, 5)
        i = random.randint(1, 5)
        j = random.randint(1, 5)
        k = random.randint(1, 5)
        l = random.randint(1, 5)
        m = random.randint(1, 5)
        n = random.randint(1, 5)
        o = random.randint(1, 5)
        p = random.randint(1, 5)
        q = random.randint(1, 5)
        r = random.randint(1, 5)
        s = random.randint(1, 5)
        t = random.randint(1, 5)
        u = random.randint(1, 5)
        v = random.randint(1, 5)
        w = random.randint(1, 5)
        x = random.randint(1, 5)
        y = random.randint(1, 5)
        z = random.randint(1, 5)
        a1 = random.randint(1, 5)
        b1 = random.randint(1, 5)
        c1 = random.randint(1, 5)
        d1 = random.randint(1, 5)
        e1 = random.randint(1, 5)
        f1 = random.randint(1, 5)
        g1 = random.randint(1, 5)
        h1 = random.randint(1, 5)
        i1 = random.randint(1, 5)
        j1 = random.randint(1, 5)
        k1 = random.randint(1, 5)
        l1 = random.randint(1, 5)
        m1 = random.randint(1, 5)
        n1 = random.randint(1, 5)
        o1 = random.randint(1, 5)
        p1 = random.randint(1, 5)
        q1 = random.randint(1, 5)
        r1 = random.randint(1, 5)
        s1 = random.randint(1, 5)
        t1 = random.randint(1, 5)
        u1 = random.randint(1, 5)
        v1 = random.randint(1, 5)
        w1 = random.randint(1, 5)
        x1 = random.randint(1, 5)
        y1 = random.randint(1, 5)
        z1 = random.randint(1, 5)
        a2 = random.randint(1, 5)
        b2 = random.randint(1, 5)
        c2 = random.randint(1, 5)
        d2 = random.randint(1, 5)

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
        term14 = f"{a1}\\sqrt{{{b1}}}"
        term15 = f"{c1}\\sqrt{{{d1}}}"
        term16 = f"{e1}\\sqrt{{{f1}}}"
        term17 = f"{g1}\\sqrt{{{h1}}}"
        term18 = f"{i1}\\sqrt{{{j1}}}"
        term19 = f"{k1}\\sqrt{{{l1}}}"
        term20 = f"{m1}\\sqrt{{{n1}}}"
        term21 = f"{o1}\\sqrt{{{p1}}}"
        term22 = f"{q1}\\sqrt{{{r1}}}"
        term23 = f"{s1}\\sqrt{{{t1}}}"
        term24 = f"{u1}\\sqrt{{{v1}}}"
        term25 = f"{w1}\\sqrt{{{x1}}}"
        term26 = f"{y1}\\sqrt{{{z1}}}"
        term27 = f"{a2}\\sqrt{{{b2}}}"

        question_text = f"\\left({term1} + {term2} - {term3}\\right) + \\left({term4} + {term5}\\right)\\left({term6} - {term7}\\right)"
        answer = ""
        correct_answer = ""

        return {
            'question_text': question_text,
            'answer': answer,
            'correct_answer': correct_answer,
            'mode': 1
        }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': 'Correct' if correct else 'Wrong'}