def add_fraction(a_num, a_den, b_num, b_den):

    # 通分，分母为a_den * b_den

    numerator = a_num * b_den + b_num * a_den

    denominator = a_den * b_den

    # 约分

    gcd_val = math.gcd(abs(numerator), abs(denominator))

    return (numerator // gcd_val, denominator // gcd_val)

类似地，乘法函数：

def multiply_fraction(a_num, a_den, b_num, b_den):

    numerator = a_num * b_num

    denominator = a_den * b_den

    gcd_val = math.gcd(abs(numerator), abs(denominator))

    return (numerator // gcd_val, denominator // gcd_val)

除法函数：

def divide_fraction(a_num, a_den, b_num, b_den):

    # 除以一个分数等于乘以它的倒数

    numerator = a_num * b_den

    denominator = a_den * b_num

    gcd_val = math.gcd(abs(numerator), abs(denominator))

    return (numerator // gcd_val, denominator // gcd_val)

减法函数：

def subtract_fraction(a_num, a_den, b_num, b_den):

    # a - b = a + (-b)

    return add_fraction(a_num, a_den, -b_num, b_den)

绝对值函数：

def abs_fraction(num, den):

    if num < 0:

        return (-num, den)

    else:

        return (num, den)

然后，整个表达式的计算步骤：

假设括号内的部分是a + b，其中a和b是生成的分数，那么sum_ab = add_fraction(a_num, a_den, b_num, b_den)

然后，乘以c，得到product_abc = multiply_fraction(sum_ab_num, sum_ab_den, c_num, c_den)

然后，除以d，得到division_result = divide_fraction(product_abc_num, product_abc_den, d_num, d_den)

绝对值部分：e * f - g → product_ef = multiply_fraction(e_num, e_den, f_num, f_den)，然后 subtraction_result = subtract_fraction(product_ef_num, product_ef_den, g_num, g_den)，然后abs_result = abs_fraction(subtraction_result_num, subtraction_result_den)

最后，总结果是 division_result + abs_result → add_fraction(division_result_num, division_result_den, abs_result_num, abs_result_den)

然后，将总结果的分子和分母转换为字符串形式，如"分子/分母"，如果分母为1，则只显示分子。

例如，如果结果是5/1，则显示"5"，如果是3/5则显示"3/5"。

现在，将这些步骤整合到generate函数中。

generate函数需要生成各个部分的分数，并构造题目字符串，同时计算正确答案。

然后，返回的字典包含question_text, answer（空字符串），correct_answer（正确答案的字符串），mode=1。

接下来，生成题目字符串的结构：

例如，参考例题的结构是：[(-2+5)×1/3]÷(-5/2) + |8×(-1/4)-5|

所以，可能的结构是：

[括号部分] ÷ 分数 + |绝对值部分|

括号部分可能包含两个分数的加减，如(-2 +5)，然后乘以一个分数，如1/3，再除以另一个分数，如-5/2，然后加上绝对值部分。

绝对值部分可能包含两个分数相乘，再减去另一个分数，如8×(-1/4)-5。

所以，生成括号部分的字符串，如"(a + b)"，其中a和b是生成的分数字符串。

然后，乘以一个分数c，用×符号，如"×c"。

然后，除以分数d，用÷符号，如"÷d"。

绝对值部分的字符串是"|e×f - g|"，其中e、f、g是生成的分数字符串。

将这些部分组合成整个表达式。

现在，如何生成这些部分？

例如，生成括号内的部分：

生成两个分数a和b，随机选择加法或减法运算符。

生成分数a和b的字符串形式，如"1/3"或"-5/2"。

然后，括号内的部分字符串为"(a + b)"或"(a - b)"。

然后，生成分数c，用×符号，如"×c"。

生成分数d，用÷符号，如"÷d"。

绝对值部分：生成分数e、f、g，运算符为×和-，所以字符串为"|e×f - g|"。

将这些部分组合成整个表达式字符串。

例如，整个表达式字符串为"[括号部分]÷d + |绝对值部分|"。

不过，参考例题中的括号部分是[(-2+5)×1/3]，所以可能需要将括号内的部分和乘以的分数c组合在一起，用括号括起来。

所以，整个结构可能是：[括号部分×c] ÷ d + |绝对值部分|

或者，可能括号部分已经包含乘法，如括号内的部分是(-2+5)，然后乘以c，所以整个括号部分用方括号括起来。

所以，生成的字符串结构可能需要更复杂的处理。

可能需要生成括号内的表达式，然后乘以一个分数，再用方括号括起来。

例如，生成括号内的表达式为"(a + b)"，然后乘以c，得到"(a + b) × c"，然后用方括号括起来，变成"[ (a + b) × c ]"。

然后，除以d，得到"[ (a + b) × c ] ÷ d"。

加上绝对值部分，得到"[ (