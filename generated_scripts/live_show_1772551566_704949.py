import random

def generate(level=1, **kwargs):
    while True:
        n_terms = random.randint(3, 4)
        nums = [random.randint(-20, 20) for _ in range(n_terms)]
        for i in range(len(nums)):
            if nums[i] == 0:
                nums[i] = random.randint(1, 10)
        ops = [random.choice(['+', '-', '*', '/']) for _ in range(n_terms - 1)]
        py_expr = ""
        for i in range(n_terms):
            py_expr += f"({nums[i]})"
            if i < len(ops):
                py_expr += ops[i]
        try:
            val = eval(py_expr)
            if isinstance(val, (int, float)) and val == int(val):
                f = lambda n: f"({n})" if n < 0 else str(n)
                d_expr = f(nums[0])
                for i in range(len(ops)):
                    op_sym = {'+':'+', '-':'-', '*':r'\times', '/':r'\div'}[ops[i]]
                    d_expr += f"{op_sym}{f(nums[i+1])}"
                return {
                    'question_text': d_expr,
                    'answer': '',
                    'correct_answer': str(int(val)),
                    'mode': 1
                }
        except ZeroDivisionError:
            continue

def check(user_answer, correct_answer):
    is_correct = str(user_answer).strip() == str(correct_answer).strip()
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
    }