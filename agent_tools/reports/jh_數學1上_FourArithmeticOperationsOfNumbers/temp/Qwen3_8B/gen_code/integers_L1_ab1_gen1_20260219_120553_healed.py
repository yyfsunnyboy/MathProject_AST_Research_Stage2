def generate(level=1, **kwargs):
    # 生成括号内的表达式
    a, b = generate_numbers(level)
    op1 = random.choice(['+', '-', '*', '÷'])
    if op1 == '÷':
        # 确保a能被b整除
        while a % b != 0:
            a, b = generate_numbers(level)
    bracket_expr = f"({a}{op1}{b})"

但这里可能需要处理负数的情况，比如生成的a和b可能为负数，但运算符是减法或除法。

不过，生成的a和b可能需要在生成时考虑运算符的影响。

或者，生成a和b为随机整数，然后根据运算符选择是否调整它们的值。

这可能比较复杂，但必须确保除法时结果为整数。

接下来，生成除数c和乘数d：

c = generate_non_zero_number(level)
d = generate_number(level)

绝对值内的表达式：

e, f, g = generate_numbers(level)
abs_expr = f"{e}×{f}-{g}"

然后，组合成完整的表达式：

question_text = f"[{bracket_expr}]÷{c}×{d}+|{abs_expr}|"

但需要将运算符替换为÷和×，所以可能需要在生成时使用这些符号。

不过，在生成括号内的表达式时，可能已经使用了÷和×，所以需要确保生成的表达式中的运算符是正确的。

不过，在生成括号内的表达式时，可能需要使用÷和×，但实际在生成时，可能需要使用Python的运算符符号，但用户要求在题目中使用÷和×，所以需要生成时使用这些符号。

这可能需要在生成表达式字符串时，将运算符替换为÷和×。

例如，在生成括号内的表达式时，如果运算符是除法，使用÷，乘法使用×，加减保持不变。

所以，在生成括号内的表达式时，需要将运算符转换为÷和×。

例如，op1的可能值是 '+', '-', '÷', '×'，然后根据运算符生成对应的符号。

这可能需要在生成表达式字符串时，将运算符转换为正确的符号。

例如，如果运算符是除法，使用÷，乘法使用×，加减保持不变。

因此，在生成括号内的表达式时，可能需要将运算符转换为对应的符号。

这可能需要在生成时处理。

例如：

op1 = random.choice(['+', '-', '÷', '×'])

然后，生成括号内的表达式为：

bracket_expr = f"({a}{op1}{b})"

但这样，如果op1是÷或×，则正确显示。

接下来，生成除数c和乘数d，以及绝对值内的表达式。

现在，生成数字的函数可能需要根据level生成不同的范围。例如，level=1时，数字范围较小，level=2时更大。

例如，generate_numbers(level)可能返回两个随机整数，范围根据level调整。

例如：

def generate_numbers(level):
    if level == 1:
        return random.randint(-50, 50), random.randint(-50, 50)
    elif level == 2:
        return random.randint(-100, 100), random.randint(-100, 100)
    # 可以扩展更多level的处理

但需要确保生成的数字在除法时满足条件。

不过，这可能需要更复杂的处理，比如在生成除法时，确保被除数能被除数整除。

现在，回到generate函数的代码。

生成括号内的表达式时，可能需要生成a和b，并确保如果是除法的话，a能被b整除。

例如：

def generate(level=1, **kwargs):
    import random
    import math

    # 生成括号内的表达式
    while True:
        a = random.randint(-50, 50)
        b = random.randint(-50, 50)
        op1 = random.choice(['+', '-', '÷', '×'])
        if op1 == '÷':
            if b == 0:
                continue
            if a % b != 0:
                continue
        break

    bracket_expr = f"({a}{op1}{b})"

    # 生成除数c和乘数d
    while True:
        c = random.randint(-50, 50)
        if c == 0:
            continue
        break
    d = random.randint(-50, 50)

    # 生成绝对值内的表达式
    e = random.randint(-50, 50)
    f = random.randint(-50, 50)
    g = random.randint(-50, 50)
    abs_expr = f"{e}×{f}-{g}"

    # 组合成完整的表达式
    question_text = f"[{bracket_expr}]÷{c}×{d}+|{abs_expr}|"

    # 计算正确答案
    # 替换运算符和绝对值符号
    expr_for_eval = question_text.replace('