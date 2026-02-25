import random

    def generate(level=1, **kwargs):
        def f(n):
            return f"({n})" if n < 0 else str(n)
        case = random.randint(1, 4)
        if case == 1:
            v1 = random.choice([i for i in range(-20, 21) if i != 0])
            v2 = random.randint(2, 15)
            v3 = random.choice([i for i in range(-20, 21) if i != 0])
            v4 = random.randint(2, 15)
            v5 = random.randint(1, 10)
            ans = v1 * v2 + abs(v3 * v4 - v5)
            question_text = f"計算 $${f(v1)} \\times {f(v2)} + \\left| {f(v3)} \\times {f(v4)} - {f(v5)} \\right|$$ 的值。"
        elif case == 2:
            v1 = random.randint(-40, 40)
            v2 = random.randint(-20, 20)
            v3 = random.choice([i for i in range(-10, 11) if i != 0])
            v4 = random.randint(2, 10)
            ans = v1 - (v2 + v3 * v4)
            question_text = f"計算 $${f(v1)} - [{f(v2)} + {f(v3)} \\times {f(v4)}]$$ 的值。"
        elif case == 3:
            v1 = random.randint(-15, 15)
            v2 = random.randint(-15, 15)
            v3 = random.randint(-15, 15)
            v4 = random.randint(-15, 15)
            ans = (v1 + v2) * (v3 - v4)
            question_text = f"計算 $$({f(v1)} + {f(v2)}) \\times ({f(v3)} - {f(v4)})$$ 的值。"
        else:
            v2 = random.choice([i for i in range(-12, 13) if i != 0])
            v_q = random.randint(-12, 12)
            v1 = v2 * v_q
            v3 = random.randint(-30, 30)
            ans = v_q + v3
            question_text = f"計算 $${f(v1)} \\div {f(v2)} + {f(v3)}$$ 的值。"
        return {
            'question_text': question_text,
            'answer': '',
            'correct_answer': str(ans),
            'mode': 1
        }

    def check(user_answer, correct_answer):
        try:
            ua = str(user_answer).strip()
            ca = str(correct_answer).strip()
            is_correct = int(ua) == int(ca)
        except:
            is_correct = False
        return {
            'correct': is_correct,
            'result': '正確' if is_correct else '錯誤'
        }