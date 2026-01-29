```python
def generate(level=1, **kwargs):
    import random
    
    # Step 1: Generate necessary variables according to MASTER_SPEC
    a = random.randint(-5, 5)
    while a == 0:
        a = random.randint(-5, 5)
    
    b = random.randint(-5, 5)
    
    c = random.randint(-5, 5)
    while c == 0:
        c = random.randint(-5, 5)
    
    d = random.randint(-5, 5)
    
    n = random.choice([2, 3])
    
    x0 = random.randint(-3, 3)
    while c * x0 + d == 0:
        x0 = random.randint(-3, 3)
    
    # Step 2: Execute calculations according to MASTER_SPEC
    val_g = a * x0 + b
    val_h = c * x0 + d
    
    y0 = val_g * (val_h ** n)
    
    m = a * (val_h ** n) + (val_g) * n * (val_h ** (n-1)) * c
    
    while m == 0:
        # Regenerate variables if the derivative is zero
        a = random.randint(-5, 5)
        while a == 0:
            a = random.randint(-5, 5)
        
        b = random.randint(-5, 5)
    
        c = random.randint(-5, 5)
        while c == 0:
            c = random.randint(-5, 5)
        
        d = random.randint(-5, 5)
        
        n = random.choice([2, 3])
        
        x0 = random.randint(-3, 3)
        while c * x0 + d == 0:
            x0 = random.randint(-3, 3)
    
    y_intercept = y0 - m * x0
    
    # Step 3: Build the question LaTeX
    term1_sign = op_latex['+'] if b > 0 else op_latex['-']
    term1_str = f"{fmt_num(a)}x {term1_sign} {fmt_num(abs(b))}"
    
    term2_sign = op_latex['+'] if d > 0 else op_latex['-']
    term2_str = f"{fmt_num(c)}x {term2_sign} {fmt_num(abs(d))}"
    
    f_x_latex = f"({term1_str})({term2_str})^{{{fmt_num(n)}}}"
    
    point_latex = f"P({fmt_num(x0)}, {fmt_num(y0)})"
    
    q = f"在函數 $f(x) = {f_x_latex}$ 的圖形上，求以點 ${point_latex}$ 為切點的切線方程式。"
    q = clean_latex_output(q)
    
    # Step 4: Format the answer as a pure number
    ans_str = "y="
    
    if m == 1:
        ans_str += "x"
    elif m == -1:
        ans_str += "-x"
    else:
        ans_str += f"{m}x"
    
    if y_intercept > 0:
        ans_str += f"+{y_intercept}"
    elif y_intercept < 0:
        ans_str += f"{y_intercept}"
    
    a = ans_str
    
    # Step 5: Return the standard format
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
```