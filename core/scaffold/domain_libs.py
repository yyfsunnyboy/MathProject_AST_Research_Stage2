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
    def format_term_unsimplified(coeff, radicand, is_first=True):
        """格式化單項根式 (不化簡，用於題目展示)"""
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
    def format_expression(terms_dict, denominator=1):
        """格式化多項根式表達式 (terms_dict: {radicand: coeff})"""
        if not terms_dict:
            return "0"
        
        sorted_radicands = sorted(terms_dict.keys())
        
        parts = []
        is_first_term = True
        for rad in sorted_radicands:
            coeff = terms_dict[rad]
            if coeff == 0:
                continue
            
            part_str = RadicalOps.format_term(coeff, rad, is_first=is_first_term)
            if part_str:
                parts.append(part_str)
                is_first_term = False
        
        if not parts:
            return "0"
        
        expr = "".join(parts)
        
        if denominator != 1:
            return f"\\frac{{{expr}}}{{{denominator}}}"
        return expr


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

