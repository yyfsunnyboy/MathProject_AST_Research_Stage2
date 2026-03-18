# -*- coding: utf-8 -*-
# ==============================================================================
# Domain Libraries (Scaffold)
# ==============================================================================
# 這裡存放各種 Domain Helper Classes 的標準實作。
# Code Generator 會在生成檔案時，自動將相關的 Class 源碼注入到目標檔案中。
# ==============================================================================

import math
from fractions import Fraction

class RadicalOps:
    """根號運算模組 - 化簡與精確計算"""
    
    @staticmethod
    def simplify_term(coeff, radicand):
        """化簡單項根式 c√r -> (new_c, new_r)"""
        from fractions import Fraction
        
        # 由於 Sandbox dynamic reloading，isinstance 容易失靈，改用 __name__
        if type(radicand).__name__ == "Fraction" or isinstance(radicand, Fraction):
            num = radicand.numerator
            den = radicand.denominator
            if den != 1:
                coeff = Fraction(coeff, den)
                radicand = num * den
            else:
                radicand = num
                
        if radicand == 0:
            return (0, 0)
        if radicand == 1:
            return (coeff, 1)
        
        new_coeff = coeff
        new_radicand = radicand
        
        i = 2
        while i * i <= new_radicand:
            if new_radicand % (i * i) == 0:
                new_coeff *= i
                new_radicand //= (i * i)
            else:
                i += 1
        return (new_coeff, new_radicand)

    @staticmethod
    def simplify(coeff, radicand):
        """別名：與 simplify_term 同義；單項化簡 c√r → (new_c, new_r)，例如 radicand=12 → (2, 3)。"""
        return RadicalOps.simplify_term(coeff, radicand)

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
        
        if c2 == 0 or r2 == 0:
            raise ValueError("除數係數或被開方數不能為 0")
        
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
    def format_term(coeff, radicand, is_first=True):
        """格式化單項根式 (LaTeX)"""
        if coeff == 0:
            return ""
        
        from fractions import Fraction
        
        # Handle Fraction and styling
        if type(coeff).__name__ == "Fraction" or isinstance(coeff, Fraction):
            coeff_str = FractionOps.to_latex(coeff, mixed=False)
        else:
            coeff_str = str(coeff)
            
        if coeff == 1:
            coeff_str = ""
        elif coeff == -1:
            coeff_str = "-"
            
        if radicand == 0:
            term_str = "0"
            coeff_str = "0" # Override for 0 radicand
        elif radicand == 1:
            term_str = FractionOps.to_latex(coeff, mixed=False) if (type(coeff).__name__ == "Fraction" or isinstance(coeff, Fraction)) else str(coeff)
        else:
            if (type(radicand).__name__ == "Fraction" or isinstance(radicand, Fraction)):
                if radicand.denominator != 1:
                    term_str = f"{coeff_str}\\sqrt{{{FractionOps.to_latex(radicand, mixed=False)}}}"
                else:
                    term_str = f"{coeff_str}\\sqrt{{{radicand.numerator}}}"
            else:
                term_str = f"{coeff_str}\\sqrt{{{radicand}}}"
        
        if not is_first and coeff > 0:
            return "+" + term_str
        return term_str

    @staticmethod
    def format_term_unsimplified(
        coeff, radicand, is_first=True, wrap_negative_non_leading=False, is_leading=None
    ):
        """
        單項題幹 LaTeX（不化簡被開方數）。禁止 * 號、禁止 sqrt( ) 函數寫法。
        is_first / is_leading（同義，傳 is_leading 時覆寫 is_first）：首項為 True。
        """
        if is_leading is not None:
            is_first = bool(is_leading)
        if coeff == 0:
            return ""
        from fractions import Fraction

        def is_f(x):
            return type(x).__name__ == "Fraction" or isinstance(x, Fraction)

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
        """
        多項根式 (terms_dict: {radicand: coeff})。先化簡合併，再按 radicand 升序輸出以保答案唯一。
        首項係數為負時前綴 '-' 不空格；後續項正係數為 ' + '，負係數為 ' - ' 並取係數絕對值。
        """
        from fractions import Fraction

        def _is_frac(x):
            return type(x).__name__ == "Fraction" or isinstance(x, Fraction)

        if not terms_dict:
            return "0"
        simplified = {}
        for r, c in terms_dict.items():
            if c == 0:
                continue
            nc, nr = RadicalOps.simplify_term(c, r)
            simplified[nr] = simplified.get(nr, 0) + nc
        simplified = {r: c for r, c in simplified.items() if c != 0}
        if not simplified:
            return "0"

        ordered = sorted(simplified.items(), key=lambda kv: kv[0])
        parts = []
        for i, (r, c) in enumerate(ordered):
            if r == 1:
                tex = FractionOps.to_latex(c, mixed=False) if _is_frac(c) else str(c)
                if i == 0:
                    parts.append(tex)
                elif (_is_frac(c) and c > 0) or (not _is_frac(c) and c > 0):
                    parts.append(f" + {tex}")
                else:
                    ac = abs(c)
                    parts.append(f" - {FractionOps.to_latex(ac, mixed=False) if _is_frac(c) else str(ac)}")
                continue
            ac = abs(c)
            if _is_frac(c):
                mag = FractionOps.to_latex(ac, mixed=False)
                body = f"{mag}\\sqrt{{{r}}}" if ac != 1 else f"\\sqrt{{{r}}}"
            elif ac == 1:
                body = f"\\sqrt{{{r}}}"
            else:
                body = f"{ac}\\sqrt{{{r}}}"
            if i == 0:
                if c < 0:
                    parts.append(f"-{body}")
                else:
                    parts.append(body)
            else:
                if c > 0:
                    parts.append(f" + {body}")
                else:
                    parts.append(f" - {body}")
        expr = "".join(parts)
        if denominator != 1:
            return f"\\frac{{{expr}}}{{{denominator}}}"
        return expr

    @staticmethod
    def add_dicts(terms1, terms2):
        """合併兩個同類項字典"""
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
                if c1 == 0 or c2 == 0: continue
                # c1√r1 * c2√r2
                new_c, new_r = RadicalOps.simplify_term(c1 * c2, r1 * r2)
                result[new_r] = result.get(new_r, 0) + new_c
        return {r: c for r, c in result.items() if c != 0}


class IntegerOps:
    """整數運算工具"""
    
    @staticmethod
    def op_to_latex(op_str):
        """將基礎運算符號轉成國中課本 LaTeX 顯示"""
        if op_str == '*': 
            return '\\times'
        if op_str == '/': 
            return '\\div'
        return op_str
    
    @staticmethod
    def fmt_num(n):
        """格式化數字（負數加括號）"""
        if n < 0:
            return f"({n})"
        return str(n)
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        """產生非零隨機整數"""
        import random
        choices = [x for x in range(min_val, max_val + 1) if x != 0]
        if not choices:
            return 1  # 如果範圍內沒有非零數，返回 1
        return random.choice(choices)
    
    @staticmethod
    def safe_eval(expr_str):
        """安全計算表達式（支援四則、括號、abs()）"""
        try:
            # 移除空格
            expr_str = expr_str.strip()
            # 先將 LaTeX 符號與括號清理乾淨，轉為純 Python 計算式
            clean_expr = str(expr_str).replace('\\div', '/').replace('\\times', '*')
            clean_expr = clean_expr.replace('\\', '') # 移除殘留的反斜線
            
            # 使用 eval，但只允許安全的數學運算
            result = eval(clean_expr, {"__builtins__": {"abs": abs, "Fraction": Fraction, "round": round, "int": int}}, {})
            return result
        except Exception as e:
            raise ValueError(f"無法計算表達式: {expr_str}, 錯誤: {e}")


class FractionOps:
    """分數運算工具"""
    
    @staticmethod
    def create(value):
        """建立分數（支援 int/float/str/Fraction 輸入）"""
        if isinstance(value, Fraction):
            return value
        return Fraction(value)
    
    @staticmethod
    def to_latex(frac, mixed=False):
        """轉成 LaTeX 分數（mixed=True 顯示帶分數）"""
        if isinstance(frac, (int, float)):
            frac = Fraction(frac)
        
        if not isinstance(frac, Fraction):
            return str(frac)
        
        # 如果是整數
        if frac.denominator == 1:
            return str(frac.numerator)
        
        # 如果是帶分數格式
        if mixed and abs(frac.numerator) > frac.denominator:
            # 正確處理負分數的帶分數：截斷而非向下取整
            whole = int(frac.numerator / frac.denominator)
            remainder = abs(frac.numerator - whole * frac.denominator)
            if remainder == 0:
                return str(whole)
            return f"{whole}\\frac{{{remainder}}}{{{frac.denominator}}}"
        
        # 一般分數
        if frac.numerator < 0:
            return f"-\\frac{{{abs(frac.numerator)}}}{{{frac.denominator}}}"
        return f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}"
    
    @staticmethod
    def add(a, b):
        """分數加法"""
        return FractionOps.create(a) + FractionOps.create(b)
    
    @staticmethod
    def sub(a, b):
        """分數減法"""
        return FractionOps.create(a) - FractionOps.create(b)
    
    @staticmethod
    def mul(a, b):
        """分數乘法"""
        return FractionOps.create(a) * FractionOps.create(b)
    
    @staticmethod
    def div(a, b):
        """分數除法"""
        if b == 0 or (isinstance(b, Fraction) and b.numerator == 0):
            raise ValueError("除數不能為 0")
        return FractionOps.create(a) / FractionOps.create(b)
