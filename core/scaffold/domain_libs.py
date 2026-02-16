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
        
        if radicand == 1:
            term_str = str(coeff)
        elif radicand == 0:
            term_str = "0"
        else:
            if coeff == 1:
                term_str = f"\\sqrt{{{radicand}}}"
            elif coeff == -1:
                term_str = f"-\\sqrt{{{radicand}}}"
            else:
                term_str = f"{coeff}\\sqrt{{{radicand}}}"
        
        if not is_first and coeff > 0:
            return "+" + term_str
        return term_str

    @staticmethod
    def format_term_unsimplified(coeff, radicand, is_first=True):
        """格式化單項根式 (不化簡，用於題目展示)"""
        if coeff == 0:
            return ""
        
        if radicand == 1:
            term_str = str(coeff)
        elif radicand == 0:
            term_str = "0"
        else:
            if coeff == 1:
                term_str = f"\\sqrt{{{radicand}}}"
            elif coeff == -1:
                term_str = f"-\\sqrt{{{radicand}}}"
            else:
                term_str = f"{coeff}\\sqrt{{{radicand}}}"
        
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
    # (預留位置)
    pass


class FractionOps:
    """分數運算工具"""
    # (預留位置)
    pass
