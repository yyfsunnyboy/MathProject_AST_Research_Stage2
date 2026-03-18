pattern_id
p2f_int_mult_rad
import random

# ==============================================================================
# [AUTO-INJECTED RESOURCE] RadicalOps
# ==============================================================================
class RadicalOps:
    """根號運算模組 - 化簡與精確計算"""
    
    @staticmethod
    def create(inner):
        """建立根號 sqrt(inner) 並自動化簡"""
        if inner < 0:
            raise ValueError("Cannot take square root of negative number")
        if inner == 0:
            return "0"
        
        i = int(math.sqrt(inner))
        while i > 1:
            if inner % (i * i) == 0:
                sqrt_val = i
                remainder = inner // (i * i)
                if remainder == 1:
                    return str(sqrt_val)
                return f"{sqrt_val}√{remainder}"
            i -= 1
        
        return f"√{inner}"
    
    @staticmethod
    def is_perfect_square(n):
        """檢查 n 是否為完全平方數"""
        if n < 0:
            return False
        sqrt = int(n ** 0.5)
        return sqrt * sqrt == n
    
    @staticmethod
    def to_latex(expr):
        """輸出根號的 LaTeX 格式"""
        return f"\\sqrt{{{expr}}}"

    @staticmethod
    def add_term(terms_dict, coeff, radicand):
        """化簡並將單項根式加入到字典中"""
        new_coeff, new_radicand = RadicalOps.simplify_term(coeff, radicand)
        if new_coeff != 0:
            terms_dict[new_radicand] = terms_dict.get(new_radicand, 0) + new_coeff
        return terms_dict

    @staticmethod
    def mul_terms(c1, r1, c2, r2):
        """兩個單項根式相乘，返回化簡結果 (new_coeff, new_radicand)"""
        return RadicalOps.simplify_term(c1 * c2, r1 * r2)

    @staticmethod
    def div_terms(c1, r1, c2, r2):
        """兩個單項根式相除 c1√r1 ÷ c2√r2，返回化簡與有理化結果 (new_coeff, new_radicand)"""
        from fractions import Fraction
        # 處理分數被開方數
        is_r1_frac = type(r1).__name__ == "Fraction" or isinstance(r1, Fraction)
        is_r2_frac = type(r2).__name__ == "Fraction" or isinstance(r2, Fraction)
        if is_r1_frac or is_r2_frac:
            return RadicalOps.simplify_term(Fraction(c1, c2), Fraction(r1, r2))
        # 整數被開方數
        if r1 % r2 == 0:
            return RadicalOps.simplify_term(Fraction(c1, c2), r1 // r2)
        else:
            return RadicalOps.simplify_term(Fraction(c1, c2 * r2), r1 * r2)

    @staticmethod
    def get_prime_factors(n):
        """質因數分解 (例: 12 -> {2:2, 3:1})"""
        n = abs(int(n))
        factors = {}
        d = 2
        temp = n
        while d * d <= temp:
            while temp % d == 0:
                factors[d] = factors.get(d, 0) + 1
                temp //= d
            d += 1
        if temp > 1:
            factors[temp] = factors.get(temp, 0) + 1
        return factors

    @staticmethod
    def simplify_term(coeff, radicand):
        """化簡單項根式 c√r -> (new_c, new_r)"""
        from fractions import Fraction
        # [Fix] Handle Fraction radicand (e.g. 1/2 -> 2/4 -> 1/2 sqrt(2))
        if isinstance(radicand, Fraction):
            if radicand.denominator != 1:
                coeff = Fraction(coeff, radicand.denominator)
                radicand = radicand.numerator * radicand.denominator
            else:
                radicand = radicand.numerator

        radicand = int(radicand)
        if radicand == 0: return 0, 1
        if radicand == 1: return coeff, 1
        factors = RadicalOps.get_prime_factors(radicand)
        out_factor = 1
        new_radicand = 1
        for p, exp in factors.items():
            out_factor *= p**(exp // 2)
            new_radicand *= p**(exp % 2)
        return coeff * out_factor, new_radicand

    @staticmethod
    def simplify(coeff, radicand):
        """別名：等同 simplify_term；單項化簡 c√r → (new_c, new_r)。"""
        return RadicalOps.simplify_term(coeff, radicand)

    @staticmethod
    def format_term(coeff, radicand, is_first=True):
        """格式化單項根式 (LaTeX)，支援 Fraction 係數"""
        if coeff == 0: return ""
        c_val, r_val = RadicalOps.simplify_term(coeff, radicand)
        from fractions import Fraction as _F
        _is_frac = isinstance(c_val, _F) and c_val.denominator != 1

        if r_val == 1:
            if _is_frac:
                n, d = abs(c_val.numerator), c_val.denominator
                s = f"\\frac{{{n}}}{{{d}}}"
                if not is_first:
                    return f" - {s}" if c_val < 0 else f" + {s}"
                return f"-{s}" if c_val < 0 else s
            if is_first: return str(c_val)
            return f" + {c_val}" if c_val > 0 else f" - {-c_val}"

        sign = ""
        if not is_first:
            sign = " + " if c_val > 0 else " - "
        elif c_val < 0:
            sign = "-"

        abs_c = abs(c_val)
        if _is_frac:
            c_str = f"\\frac{{{abs_c.numerator}}}{{{abs_c.denominator}}}"
        elif abs_c == 1:
            c_str = ""
        else:
            c_str = str(abs_c)
        return f"{sign}{c_str}\\sqrt{{{r_val}}}"

    @staticmethod
    def format_term_unsimplified(
        coeff, radicand, is_first=True, wrap_negative_non_leading=False, is_leading=None
    ):
        """不化簡被開方數；is_leading 與 is_first 同義。"""
        if is_leading is not None:
            is_first = bool(is_leading)
        if coeff == 0:
            return ""
        from fractions import Fraction as _F

        def is_f(x):
            return type(x).__name__ == "Fraction" or isinstance(x, _F)

        if radicand == 0:
            return "0"
        if not is_f(radicand) and int(radicand) == 1:
            return FractionOps.to_latex(coeff, mixed=False) if is_f(coeff) else str(coeff)
        if is_f(radicand):
            rt = (
                FractionOps.to_latex(radicand, mixed=False)
                if radicand.denominator != 1
                else str(radicand.numerator)
            )
            core = f"\\sqrt{{{rt}}}"
        else:
            core = f"\\sqrt{{{radicand}}}"
        if is_f(coeff):
            if wrap_negative_non_leading and coeff < 0 and not is_first:
                return f"\\left({RadicalOps.format_term_unsimplified(coeff, radicand, True, False)}\\right)"
            at = FractionOps.to_latex(abs(coeff), mixed=False)
            mid = f"{at}{core}" if abs(coeff) != 1 else core
            if is_first:
                return f"-{mid}" if coeff < 0 else (mid if coeff > 0 else "0")
            if coeff > 0:
                return f" + {mid}" if coeff != 1 else f" + {core}"
            return f" - {mid}" if abs(coeff) != 1 else f" - {core}"
        c = int(coeff)
        if wrap_negative_non_leading and c < 0 and not is_first:
            return f"\\left({RadicalOps.format_term_unsimplified(c, radicand, True, False)}\\right)"
        if is_first:
            if c == 1:
                return core
            if c == -1:
                return f"-{core}"
            if c < 0:
                return f"-{abs(c)}{core}"
            return f"{c}{core}"
        if c > 0:
            return f" + {core}" if c == 1 else f" + {c}{core}"
        if c == -1:
            return f" - {core}"
        return f" - {abs(c)}{core}"

    @staticmethod
    def format_expression(terms_dict, denominator=1):
        """格式化多項根式表達式 (terms_dict: {radicand: coeff})，支援 Fraction 係數與 denominator 參數"""
        if not terms_dict: return "0"
        import math
        from fractions import Fraction as _F

        # 1. 內部化簡合併
        simplified = {}
        for r, c in terms_dict.items():
            if c == 0: continue
            c_s, r_s = RadicalOps.simplify_term(c, r)
            simplified[r_s] = simplified.get(r_s, 0) + c_s

        simplified = {r: c for r, c in simplified.items() if c != 0}
        if not simplified: return "0"

        # 1.5 若有 Fraction 係數，通分整化
        for r in list(simplified.keys()):
            c = simplified[r]
            if isinstance(c, _F) and c.denominator != 1:
                denominator = denominator * c.denominator
                simplified[r] = c.numerator

        # 2. 處理分母約分
        if denominator != 1:
            all_coeffs = [int(c) for c in simplified.values()]
            common = abs(int(denominator))
            for c in all_coeffs:
                common = math.gcd(common, abs(c))
            if common > 1:
                denominator //= common
                for r in simplified:
                    simplified[r] //= common

        # 3. 按 radicand 升序（答案唯一）
        sorted_rads = sorted(simplified.keys())

        # 4. 標準書寫：首項負號緊貼；後續「 + 」「 - 」與係數絕對值
        parts = []
        for i, r in enumerate(sorted_rads):
            c = simplified[r]
            if c == 0:
                continue
            if r == 1:
                tex = str(c)
                if not parts:
                    parts.append(tex)
                elif c > 0:
                    parts.append(f" + {tex}")
                else:
                    parts.append(f" - {abs(c)}")
            else:
                ac = abs(c)
                body = f"\\sqrt{{{r}}}" if ac == 1 else f"{ac}\\sqrt{{{r}}}"
                if not parts:
                    parts.append(f"-{body}" if c < 0 else body)
                elif c > 0:
                    parts.append(f" + {body}")
                else:
                    parts.append(f" - {body}")

        final_str = "".join(parts)

        if denominator == 1 or not final_str:
            return final_str if final_str else "0"
        return f"\\frac{{{final_str}}}{{{denominator}}}"

    @staticmethod
    def add_dicts(terms1, terms2):
        """合併兩個同類項字典 {radicand: coeff}"""
        merged = dict(terms1)
        for r, c in terms2.items():
            merged[r] = merged.get(r, 0) + c
        return merged

    @staticmethod
    def multiply_dicts(terms1, terms2):
        """展開兩個多項根式的乘積，並自動化簡同類項"""
        result = {}
        for r1, c1 in terms1.items():
            for r2, c2 in terms2.items():
                if c1 == 0 or c2 == 0:
                    continue
                new_c, new_r = RadicalOps.simplify_term(c1 * c2, r1 * r2)
                result[new_r] = result.get(new_r, 0) + new_c
        return {r: c for r, c in result.items() if c != 0}

    @staticmethod
    def simplify_root(radicand):
        """[防護方法] 化簡 √radicand，等同 simplify_term(1, radicand)，返回 (coeff, simplified_radicand)"""
        return RadicalOps.simplify_term(1, int(radicand))

# [Global Aliases for AI Convenience]
simplify_term = RadicalOps.simplify_term
format_term = RadicalOps.format_term
format_term_unsimplified = RadicalOps.format_term_unsimplified
format_expression = RadicalOps.format_expression
add_dicts = RadicalOps.add_dicts
multiply_dicts = RadicalOps.multiply_dicts


c = random.choice([-3, -2, 2, 3])
r = 5
t1 = RadicalOps.format_term_unsimplified(c, r, True)
return {'question_text': f'化簡 ${t1}$', 'correct_answer': RadicalOps.format_expression({r: c}), 'mode': 1}

def check(user_answer, correct_answer):
    try:
        return {'correct': str(user_answer).strip() == str(correct_answer).strip(), 'result': '自動補全比對'}
    except:
        return {'correct': False, 'result': '錯誤'}

def generate(level=1, **kwargs):
    return {'question_text': 'Fallback due to missing generate() wrapper', 'correct_answer': '\\text{Failed}'}