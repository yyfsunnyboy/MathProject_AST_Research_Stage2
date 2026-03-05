# 导入必要的模块
import random
import math
from fractions import Fraction

class IntegerOps:
    @staticmethod
    def fmt_num(n):
        if n < 0:
            return f"({n})"
        return str(n)

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        if mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator) % val.denominator
            if val.numerator < 0:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
            else:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def generate():
    while True:
        try:
            a = Fraction(random.randint(-5, 5), random.randint(1, 5))
            b = Fraction(random.randint(-5, 5), random.randint(1, 5))
            c = Fraction(random.randint(-5, 5), random.randint(1, 5))
            d = Fraction(random.randint(-5, 5), random.randint(1, 5))
            e = Fraction(random.randint(-5, 5), random.randint(1, 5))
            f = Fraction(random.randint(-5, 5), random.randint(1, 5))
            
            # 确保分母不为零且分数已约分
            if a.denominator == 1 or b.denominator == 1 or c.denominator == 1:
                continue
            
            # 构建题目字符串
            part1 = f"\\left({FractionOps.to_latex(a)}\\right)"
            part2 = FractionOps.to_latex(b)
            part3 = FractionOps.to_latex(c)
            
            if random.choice([True, False]):
                part4 = f"\\left({FractionOps.to_latex(d)}\\right)"
                part5 = FractionOps.to_latex(e)
                part6 = FractionOps.to_latex(f)
                
                math_str = f"-{part1} + {part3} - \\left({part4} \\div {part5}\\right) + {part6}"
                ans = -a + c - (d / e) + f
            else:
                part4 = FractionOps.to_latex(d)
                math_str = f"-{part1} + {part3} - ({part4} \\div {part5}) + {part6}"
                ans = -a + c - (d / e) + f
            
            # 检查答案是否符合格式要求
            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"
            
            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue
            
            # 检查所有分数是否符合范围要求
            if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f]):
                continue
            
            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
            continue

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if Fraction(ua) == Fraction(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}