```python
import random

def generate(level=1, **kwargs):
    # 確保 a, c 非零且在範圍內
    while True:
        a = random.randint(-3, 3)
        if a != 0:
            break
    
    b = random.randint(-3, 3)
    
    while True:
        c = random.randint(-3, 3)
        if c != 0:
            break
    
    d = random.randint(-3, 3)
    n = random.choice([2, 3])
    x0 = random.randint(-2, 2)
    
    # 確保 cx0 + d 不為零，除非 n=2 且 cx0+d=0
    if c * x0 + d == 0 and n != 2:
        while True:
            x0 = random.randint(-2, 2)
            if c * x0 + d != 0:
                break
    
    # 計算 y0
    val_cx_plus_d = c * x0 + d
    val_ax_plus_b = a * x0 + b
    y0 = val_ax_plus_b * (val_cx_plus_d ** n)
    
    # 計算導函數 f'(x) 在 x0 點的值 m
    first_term_prime = a * (val_cx_plus_d ** n)
    second_term_prime = val_ax_plus_b * n * c * (val_cx_plus_d ** (n-1))
    m = first_term_prime + second_term_prime
    
    # 計算截距 k
    k = y0 - m * x0
    
    # 確保 m 和 k 在指定範圍內
    if not (-50 <= m <= 50) or not (-100 <= k <= 100):
        return generate(level, **kwargs)
    
    # 格式化函數表示
    factor1_str = fmt_num(a) + "x" if a != -1 else "-x"
    if b > 0:
        factor1_str += "+" + fmt_num(b)
    elif b < 0:
        factor1_str += "-" + fmt_num(-b, with_sign=True)
    
    factor2_str = "("
    factor2_inner = fmt_num(c) + "x" if c != -1 else "-x"
    if d > 0:
        factor2_inner += "+" + fmt_num(d)
    elif d < 0:
        factor2_inner += "-" + fmt_num(-d, with_sign=True)
    factor2_str += factor2_inner + ")"
    
    # 組合題目字串
    q = f"在函數 $f(x) = {factor1_str}{factor2_str}^{fmt_num(n)}$ 的圖形上，求以點 $P({fmt_num(x0)}, {fmt_num(y0)})$ 為切點的切線方程式。"
    q = clean_latex_output(q)
    
    # 格式化答案
    if m == 1:
        answer_str = "y=x" + ("+" + str(k) if k > 0 else "-" + str(-k)) if k != 0 else "y=x"
    elif m == -1:
        answer_str = "y=-x" + ("+" + str(k) if k > 0 else "-" + str(-k)) if k != 0 else "y=-x"
    elif m == 0:
        answer_str = f"y={k}"
    else:
        answer_str = f"y={m}x" + ("+" + str(k) if k > 0 else "-" + str(-k)) if k != 0 else f"y={m}x"
    
    return {'question_text': q, 'answer': answer_str, 'mode': 1}
```