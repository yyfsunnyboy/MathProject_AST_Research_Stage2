```
def generate(level=1, **kwargs):
    import random
    
    # Step 1: Generate necessary variables according to MASTER_SPEC
    coeff_a = random.randint(-3, -1) if random.random() < 0.5 else random.randint(1, 3)
    coeff_b = random.randint(-5, 5)
    coeff_c = random.randint(-3, -1) if random.random() < 0.5 else random.randint(1, 3)
    coeff_d = random.randint(-5, 5)
    exponent_n = random.choice([2, 3])
    eval_x0 = random.randint(-2, 2)
    
    # Ensure constraints are met
    while (coeff_c * eval_x0 + coeff_d) == 0:
        eval_x0 = random.randint(-2, 2)
    while (coeff_a * eval_x0 + coeff_b) == 0:
        eval_x0 = random.randint(-2, 2)
    
    # Step 2: Execute calculations according to MASTER_SPEC
    u_x = coeff_a * eval_x0 + coeff_b
    v_x = coeff_c * eval_x0 + coeff_d
    
    y0_val = u_x * (v_x ** exponent_n)
    
    term1 = coeff_a * (v_x ** exponent_n)
    term2_inner_chain = exponent_n * (v_x ** (exponent_n - 1)) * coeff_c
    term2 = u_x * term2_inner_chain
    
    slope_m = term1 + term2
    
    y_intercept_k = y0_val - slope_m * eval_x0
    
    # Step 3: Construct question LaTeX using fmt_num and op_latex
    part1_b_str = f"{op_latex['+'] if coeff_b >= 0 else op_latex['-']} {fmt_num(abs(coeff_b))}" if coeff_b != 0 else ""
    part1_str = f"{fmt_num(coeff_a)}x{part1_b_str}"
    if coeff_a == 1: part1_str = f"x{part1_b_str}"
    if coeff_a == -1: part1_str = f"-x{part1_b_str}"
    
    part2_d_str = f"{op_latex['+'] if coeff_d >= 0 else op_latex['-']} {fmt_num(abs(coeff_d))}" if coeff_d != 0 else ""
    part2_base_str = f"{fmt_num(coeff_c)}x{part2_d_str}"
    if coeff_c == 1: part2_base_str = f"x{part2_d_str}"
    if coeff_c == -1: part2_base_str = f"-x{part2_d_str}"
    
    func_latex = f"({part1_str})({part2_base_str})^{fmt_num(exponent_n)}"
    
    q = f"在函數 $f(x) = {func_latex}$ 的圖形上，求以點 $P({fmt_num(eval_x0)}, {fmt_num(y0_val)})$ 為切點的切線方程式。"
    question_output = clean_latex_output(q)
    
    # Step 4: Format the answer according to MASTER_SPEC
    m_str = ""
    if slope_m == 1:
        m_str = "x"
    elif slope_m == -1:
        m_str = "-x"
    else:
        m_str = f"{slope_m}x"
        
    k_str = ""
    if y_intercept_k > 0:
        k_str = f"+{y_intercept_k}"
    elif y_intercept_k < 0:
        k_str = f"{y_intercept_k}" # 負數自帶符號
    
    if m_str == "" and k_str == "": # 針對 y=0 的情況
        answer_output = "y=0"
    elif m_str == "": # 針對 y=k 的情況 (slope_m = 0, 但此題型已排除)
        answer_output = f"y={k_str}"
    else:
        answer_output = f"y={m_str}{k_str}"
    
    return question_output, answer_output