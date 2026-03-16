def generate():
    import random
    k = random.randint(1, 10)
    r = random.randint(2, 20)
    num = random.randint(1, 10)
    denom = random.randint(1, 10)
    while denom == 0 or denom == 1 or denom == k:
        denom = random.randint(1, 10)
    vars_dict = df.get_safe_vars_for_pattern('p2h_frac_mult_rad', 'easy', term_count=1)
    question_text = df.format_question_LaTeX('p2h_frac_mult_rad', vars_dict)  # [AST Fix: 安全初始化防護]
    correct_answer, steps = df.solve_problem_pattern('p2h_frac_mult_rad', vars_dict, 'easy')
    return f"""\ndef generate():\n    from domain import df\n    import random\n\n    # STEP 1: Pattern Identification\n    # Target: \x0crac{3}{5}\times5\\sqrt{2} → This is a "fraction × root" multiplication\n    # Pattern: p2h_frac_mult_rad (fraction × radical expression)\n    # Difficulty: easy (since it's a simple multiplication of fraction and radical)\n\n    # STEP 2: Generate variables using DomainFunctionHelper\n    # For p2h_frac_mult_rad: {('k', 'r', 'num', 'denom')}\n    # But note: the target is \x0crac{3}{5} \times 5\\sqrt{2} → so k=5, r=2, num=3, denom=5\n    # We'll generate similar structure but randomized\n\n    # Generate random values for k, r, num, denom\n    k = random.randint(1, 10)\n    r = random.randint(2, 20)\n    num = random.randint(1, 10)\n    denom = random.randint(1, 10)\n    while denom == 0 or denom == 1 or denom == k:  # Avoid trivial cases\n        denom = random.randint(1, 10)\n\n    # STEP 3: Use DomainFunctionHelper to get safe variables\n    vars_dict = df.get_safe_vars_for_pattern("p2h_frac_mult_rad", "easy", term_count=1)\n    # But we want to override with our own values for consistency with target structure\n    # Since p2h_frac_mult_rad expects {('k', 'r', 'num', 'denom')} but our target is \x0crac{num}{denom} \times k\\sqrt{r}\n    # We'll use the generated values but ensure they match the structure\n\n    # STEP 4: Format question text using DomainFunctionHelper\n    question_text = df.format_question_LaTeX("p2h_frac_mult_rad", vars_dict)\n\n    # STEP 5: Solve problem using DomainFunctionHelper\n    correct_answer, steps = df.solve_problem_pattern("p2h_frac_mult_rad", vars_dict, "easy")\n\n    # STEP 6: Return as required\n    return f"""  # [AST Fix: 安全初始化防護]

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}