class IntegerOps:
    @staticmethod
    def fmt_num(n):
        if n >= 0:
            return str(n)
        else:
            return f"({n})"

class FractionOps:
    @staticmethod
    def to_latex(val, mixed=False):
        if val.denominator == 1:
            return str(val.numerator)
        elif mixed:
            whole = val.numerator // val.denominator
            frac = abs(val.numerator) % val.denominator
            if whole < 0:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
            else:
                return f"{whole}\\frac{{{frac}}}{{{val.denominator}}}"
        else:
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"

def generate_problem():
    terms = [
        ("(-2 1/6)", FractionOps.create("-2 1/6")),
        ("1 2/9", FractionOps.create("1 2/9")),
        ("-(-1 1/3)", FractionOps.create("-(-1 1/3)"))
    ]
    
    math_str = " + ".join([term[0] for term in terms])
    return {
        'question_text': f'計算 ${math_str}$ 的值。',
        'answer': '',
        'correct_answer': str(FractionOps.add(
            FractionOps.add(terms[0][1], terms[1][1]), 
            terms[2][1]
        )),
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua = str(user_answer).strip()
        ca = str(correct_answer).strip()
        if ua == ca:
            return {'correct': True, 'result': '正確'}
        if FractionOps.create(ua) == FractionOps.create(ca):
            return {'correct': True, 'result': '正確'}
    except Exception:
        pass
    return {'correct': False, 'result': '錯誤'}