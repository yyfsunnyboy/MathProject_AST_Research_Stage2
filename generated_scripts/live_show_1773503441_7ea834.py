import random
import math
from fractions import Fraction

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
    def format_term_unsimplified(coeff, radicand, is_first=True):
        """格式化單項根式 (不化簡，用於題目展示)"""
        if coeff == 0: return ""

        sign = ""
        if not is_first:
            sign = " + " if coeff > 0 else " - "
        elif coeff < 0:
            sign = "-"

        abs_c = abs(coeff)
        c_str = "" if abs_c == 1 else str(abs_c)
        return f"{sign}{c_str}\\sqrt{{{radicand}}}"

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

        # 3. 排序 (整數項 radicand=1 排最前，其他從小到大)
        sorted_rads = sorted(simplified.keys())
        if 1 in sorted_rads:
            sorted_rads.remove(1)
            sorted_rads.insert(0, 1)

        # 4. 生成字串
        parts = []
        is_first = True
        for r in sorted_rads:
            term_str = RadicalOps.format_term(simplified[r], r, is_first)
            if term_str:
                parts.append(term_str)
                is_first = False

        final_str = "".join(parts).lstrip()

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



def generate(level=1, **kwargs):
    simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
    simple = [2, 3, 5, 7, 11]
    for _ in range(50):
        try:
            r1 = random.choice(simple)
            r2 = random.choice(simple)
            question_text = f'化簡 $\\frac{{3}}{{\\sqrt{{{r1}}}}}$。'  # [AST Fix: 安全初始化防護]
            correct_answer = RadicalOps.format_expression({})
            if correct_answer and correct_answer != '0':
                return {'question_text': question_text, 'answer': '', 'correct_answer': correct_answer, 'mode': 1, '_o1_healed': False}
        except Exception:
            continue
    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}

def check(user_answer, correct_answer):
    correct = str(user_answer).strip() == str(correct_answer).strip()
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}