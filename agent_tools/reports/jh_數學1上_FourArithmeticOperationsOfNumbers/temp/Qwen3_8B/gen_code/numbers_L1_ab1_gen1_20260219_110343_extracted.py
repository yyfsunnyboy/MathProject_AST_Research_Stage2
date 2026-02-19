def simplify(numerator, denominator):
    # 约分
    gcd = math.gcd(abs(numerator), abs(denominator))
    return numerator // gcd, denominator // gcd

def add_fraction(a_num, a_den, b_num, b_den):
    # 分数相加
    new_num = a_num * b_den + b_num * a_den
    new_den = a_den * b_den
    return simplify(new_num, new_den)

def subtract_fraction(a_num, a_den, b_num, b_den):
    # 分数相减
    new_num = a_num * b_den - b_num * a_den
    new_den = a_den * b_den
    return simplify(new_num, new_den)

def multiply_fraction(a_num, a_den, b_num, b_den):
    # 分数相乘
    new_num = a_num * b_num
    new_den = a_den * b_den
    return simplify(new_num, new_den)

def divide_fraction(a_num, a_den, b_num, b_den):
    # 分数相除
    # 除以b等于乘以倒数
    return multiply_fraction(a_num, a_den, b_num, b_den)

def abs_fraction(numerator, denominator):
    # 绝对值
    return abs(numerator), denominator

然后，在generate函数中，随机选择结构，生成分数，并构造题目字符串，计算正确答案。

例如，结构1的生成：

生成a, b, c, d, e, f, g的分数。

构造字符串：[(a + b) × c] ÷ d + |e × f - g|

计算步骤：

1. a + b → add_fraction(a_num, a_den, b_num, b_den)
2. 乘以c → multiply_fraction(步骤1的分子，分母，c_num, c_den)
3. 除以d → divide_fraction(步骤2的分子，分母，d_num, d_den)
4. e × f → multiply_fraction(e_num, e_den, f_num, f_den)
5. 减去g → subtract_fraction(步骤4的分子，分母，g_num, g_den)
6. 绝对值 → abs_fraction(步骤5的分子，分母)
7. 步骤3 + 步骤6 → add_fraction(步骤3的分子，分母，步骤6的分子，分母)

然后，将结果转换为字符串形式。

例如，如果结果是分子和分母，如果分母为1，则显示为整数，否则显示为分数。

例如，分子是6，分母是1 → "6"；分子是3，分母是5 → "3/5"。

现在，编写generate函数：

def generate(level=1, **kwargs):
    # 生成题目
    # 随机选择结构
    structures = [
        "[(%s + %s) × %s] ÷ (%s) + |%s × %s - %s|",
        "|%s ÷ %s + %s| × (%s - %s) + %s",
        "(%s × %s - %s) ÷ (%s + %s) + |%s - %s|"
    ]
    structure = random.choice(structures)
    
    # 生成分数
    # 生成分数的函数
    def generate_fraction():
        numerator = random.randint(-10, 10)
        denominator = random.randint(1, 10)
        if denominator == 0:
            denominator = 1
        # 确保分母不为零
        # 约分
        num, den = simplify(numerator, denominator)
        return num, den
    
    # 根据结构生成各部分
    if structure == structures[0]:
        a_num, a_den = generate_fraction()
        b_num, b_den = generate_fraction()
        c_num, c_den = generate_fraction()
        d_num, d_den = generate_fraction()
        e_num, e_den = generate_fraction()
        f_num, f_den = generate_fraction()
        g_num, g_den = generate_fraction()
        
        # 构造字符串
        question_text = structure % (
            f"{a_num}/{a_den}" if a_den != 1 else f"{a_num}",
            f"{b_num}/{b_den}" if b_den != 1 else f"{b_num}",
            f"{c_num}/{c_den}" if c_den != 1 else f"{c_num}",
            f"{d_num}/{d_den}" if d_den != 1 else f"{d_num}",
            f"{e_num}/{e_den}" if e_den != 1 else f"{e_num}",
            f"{f_num}/{f_den}" if f_den != 1 else f"{f_num}",
            f"{g_num}/{g_den}" if g_den != 1 else f"{g_num}"
        )
        
        # 计算正确答案
        # 步骤1: a + b
        step1_num, step1_den = add_fraction(a_num, a_den, b_num, b_den)
        # 步骤2: 乘以c
        step2_num, step2_den = multiply_fraction(step1_num, step1_den, c_num, c_den)
        # 步骤3: 除以d
        step3_num, step3_den = divide_fraction(step2_num, step2_den, d_num, d_den)
        # 步骤4: e × f
        step4_num, step4_den = multiply_fraction(e_num, e_den, f_num, f_den)
        # 步骤5: 减去g
        step5_num, step5_den = subtract_fraction(step4_num, step4_den, g_num, g_den)
        # 步骤6: 绝对值
        step6_num, step6_den = abs_fraction(step5_num, step5_den)
        # 步骤7: 步骤3 + 步骤6
        final_num, final_den = add_fraction(step3_num, step3_den, step6_num, step6_den)
        
        # 转换为字符串
        if final_den == 1:
            correct_answer = f"{final_num}"
        else:
            correct_answer = f"{final_num}/{final_den}"
    
    elif structure == structures[1]:
        # 类似处理其他结构
        # 生成各部分分数
        a_num, a_den = generate_fraction()
        b_num, b_den = generate_fraction()
        c_num, c_den = generate_fraction()
        d_num, d_den = generate_fraction()
        e_num, e_den = generate分数()
        f_num, f_den = generate_fraction()
        
        # 构造字符串
        question_text = structure % (
            f"{a_num}/{a_den}" if a_den != 1 else f"{a_num}",
            f"{b_num}/{b_den}" if b_den != 1 else f"{b_num}",
            f"{c_num}/{c_den}" if c_den != 1 else f"{c_num}",
            f"{d_num}/{d_den}" if d_den != 1 else f"{d_num}",
            f"{e_num}/{e_den}" if e_den != 1 else f"{e_num}",
            f"{f_num}/{f_den}" if f_den != 1 else f"{f_num}"
        )
        
        # 计算正确答案
        # 步骤1: a ÷ b
        step1_num, step1_den = divide_fraction(a_num, a_den, b_num, b_den)
        # 步骤2: 加c
        step2_num, step2_den = add_fraction(step1_num, step1_den, c_num, c_den)
        # 步骤3: 绝对值
        step3_num, step3_den = abs_fraction(step2_num, step2_den)
        # 步骤4: d - e
        step4_num, step4_den = subtract_fraction(d_num, d_den, e_num, e_den)
        # 步骤5: 步骤3 × 步骤4
        step5_num, step5_den = multiply_fraction(step3_num, step3_den, step4_num, step4_den)
        # 步骤6: 加f
        final_num, final_den = add_fraction(step5_num, step5_den, f_num, f_den)
        
        # 转换为字符串
        if final_den == 1:
            correct_answer = f"{final_num}"
        else:
            correct_answer = f"{final_num}/{final_den}"
    
    else:
        # 第三种结构
        a_num, a_den = generate_fraction()
        b_num, b_den = generate_fraction()
        c_num, c_den = generate_fraction()
        d_num, d_den = generate_fraction()
        e_num, e_den = generate_fraction()
        f_num, f_den = generate_fraction()
        g_num, g_den = generate_fraction()
        
        # 构造字符串
        question_text = structure % (
            f"{a_num}/{a_den}" if a_den != 1 else f"{a_num}",
            f"{b_num}/{b_den}" if b_den != 1 else f"{b_num}",
            f"{c_num}/{c_den}" if c_den != 1 else f"{c_num}",
            f"{d_num}/{d_den}" if d_den != 1 else f"{d_num}",
            f"{e_num}/{e_den}" if e_den != 1 else f"{e_num}",