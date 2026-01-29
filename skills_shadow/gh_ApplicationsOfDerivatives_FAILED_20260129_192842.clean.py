```python
import random

def generate(level=1, **kwargs):
    op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
    while True:
        a1 = random.choice([-3, -2, -1, 1, 2, 3])
        b1 = random.randint(-5, 5)
        a2 = random.choice([-3, -2, -1, 1, 2, 3])
        b2 = random.randint(-5, 5)
        n = random.randint(2, 4)
        x0 = random.randint(-3, 3)

        term1_linear_fn = lambda x: a1 * x - b1
        term2_base_linear_fn = lambda x: a2 * x - b2

        val_term1_at_x0 = term1_linear_fn(x0)
        val_term2_base_at_x0 = term2_base_linear_fn(x0)

        y0 = val_term1_at_x0 * (val_term2_base_at_x0 ** n)

        d_term1_dx = a1
        d_term2_base_dx = a2
        d_term2_power_dx = lambda x: n * (term2_base_linear_fn(x) ** (n - 1)) * d_term2_base_dx

        f_prime_x = d_term1_dx * (term2_base_linear_fn(x0) ** n) + term1_linear_fn(x0) * d_term2_power_dx(x0)

        m = f_prime_x
        c = y0 - m * x0

        if isinstance(y0, int) and isinstance(m, int) and isinstance(c, int):
            if m != 0 and abs(y0) <= 1000 and abs(m) <= 1000:
                break

    term1_content = fmt_num(a1) + "x"
    if b1 != 0:
        term1_content += op_latex['+'] + fmt_num(-b1)
    term1_latex = f"({term1_content})"

    term2_base_content = fmt_num(a2) + "x"
    if b2 != 0:
        term2_base_content += op_latex['+'] + fmt_num(-b2)
    term2_latex = f"({term2_base_content})^{fmt_num(n)}"

    fx_latex_str = term1_latex + term2_latex
    P_latex = f"P({fmt_num(x0)}, {fmt_num(y0)})"

    q = f"在函數 $f(x) = {fx_latex_str}$ 的圖形上，求以點 $P{P_latex}$ 為切點的切線方程式。"
    question_output = clean_latex_output(q)

    ans_str = f"y = {m}x"
    if c > 0:
        ans_str += f" + {c}"
    elif c < 0:
        ans_str += f" - {abs(c)}"

    return {'question_text': question_output, 'answer': ans_str, 'mode': 1}
```