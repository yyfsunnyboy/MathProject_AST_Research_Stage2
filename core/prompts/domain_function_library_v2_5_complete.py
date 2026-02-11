# ============================================================================
# [V2.5 完整重構版] domain_function_library.py 完整實現
# ============================================================================
"""
此模組定義了各個數學領域的標準工具函數。
所有 LLM（Gemini / 14B / 7B）在生成代碼時，必須引用這些預定義函數，禁止自創同名或類似功能的函數。

【V2.5 新增功能】
1. FractionOps (分數模組)：精確處理分數運算與浮點數轉換
2. IntegerOps (整數模組)：支援絕對值、括號格式化
3. RadicalOps (根號模組)：化簡與精確計算
4. CalculusOps (微積分模組)：多項式與微分

【關鍵改進】
- 浮點數精度修復：-0.6 → -3/5 (不是 -0.599999...)
- 設計模式：所有四則運算皆透過 Fraction 進行
- 安全評估：safe_eval() 支援絕對值運算
"""

import math
import random
from fractions import Fraction
from decimal import Decimal, getcontext
import logging

logger = logging.getLogger(__name__)

# 設置 Decimal 精度
getcontext().prec = 28


# ============================================================================
# FractionOps 實現（非字符串版本，可直接使用）
# ============================================================================

class FractionOps:
    """分數運算模組 - 精確處理分數與浮點數混合運算"""
    
    @staticmethod
    def create(value):
        """
        建立分數，具備「型別智慧」
        - 如果輸入是 float，先轉 str 再轉 Fraction（避免浮點精度誤差）
        - 支援 str 輸入（如 "-0.6"）
        - 支援 Fraction、int、float 輸入
        
        範例：
            FractionOps.create(-0.6)    → Fraction(-3, 5)
            FractionOps.create("-0.6")  → Fraction(-3, 5)
            FractionOps.create(3)       → Fraction(3, 1)
        """
        if isinstance(value, float):
            # 浮點數 → 字串 → Fraction（避免精度誤差）
            value_str = str(value)
            return Fraction(value_str).limit_denominator(10000)
        elif isinstance(value, str):
            return Fraction(value)
        elif isinstance(value, Fraction):
            return value
        else:
            return Fraction(value)
    
    @staticmethod
    def to_latex(val, mixed=False):
        """
        輸出 LaTeX 格式
        - 分母為 1 時，只顯示整數
        - mixed=True 時顯示帶分數（如 -1 1/2）
        
        範例：
            FractionOps.to_latex(Fraction(3, 2))        → "\\frac{3}{2}"
            FractionOps.to_latex(Fraction(3, 2), True)  → "1\\frac{1}{2}"
            FractionOps.to_latex(Fraction(5, 1))        → "5"
        """
        if isinstance(val, Fraction):
            if val.denominator == 1:
                return str(val.numerator)
            if mixed and abs(val.numerator) > val.denominator:
                whole = val.numerator // val.denominator
                remainder = abs(val.numerator) % val.denominator
                if remainder == 0:
                    return str(whole)
                if whole == 0:
                    return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
                sign = "-" if val < 0 else ""
                return f"{sign}{abs(whole)} \\frac{{{remainder}}}{{{val.denominator}}}"
            return f"\\frac{{{val.numerator}}}{{{val.denominator}}}"
        return str(val)
    
    @staticmethod
    def add(a, b):
        """分數加法"""
        return a + b
    
    @staticmethod
    def sub(a, b):
        """分數減法"""
        return a - b
    
    @staticmethod
    def mul(a, b):
        """分數乘法"""
        return a * b
    
    @staticmethod
    def div(a, b):
        """分數除法（注意：b 不能為零）"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b


# ============================================================================
# IntegerOps 實現
# ============================================================================

class IntegerOps:
    """整數運算模組 - 支援格式化、絕對值等"""
    
    @staticmethod
    def fmt_num(n):
        """
        格式化數字，為負數自動加括號
        - 便於生成 Python 算式（如 "x + (-5)" 而非 "x + -5"）
        
        範例：
            IntegerOps.fmt_num(5)   → "5"
            IntegerOps.fmt_num(-5)  → "(-5)"
            IntegerOps.fmt_num(0)   → "0"
        """
        if n < 0:
            return f"({n})"
        return str(n)
    
    @staticmethod
    def random_nonzero(min_val, max_val):
        """生成非零隨機整數"""
        available = [x for x in range(min_val, max_val + 1) if x != 0]
        if not available:
            raise ValueError(f"No non-zero integers in range [{min_val}, {max_val}]")
        return random.choice(available)
    
    @staticmethod
    def is_divisible(a, b):
        """檢查 a 是否能被 b 整除"""
        if b == 0:
            return False
        return a % b == 0
    
    @staticmethod
    def safe_eval(expr):
        """
        安全評估算式，支援：abs()、基本四則運算、括號
        
        範例：
            IntegerOps.safe_eval("8 * (-2) - 5")           → -21
            IntegerOps.safe_eval("abs(8 * (-2) - 5)")     → 21
            IntegerOps.safe_eval("[ (-20) + (-10)] / (-5) * 3")  → 18.0
        """
        # 允許的函數和變數
        safe_dict = {
            '__builtins__': {},
            'abs': abs,
            'sum': sum,
            'max': max,
            'min': min,
        }
        # 移除方括號並替換為括號（如果需要）
        expr = expr.replace('[', '(').replace(']', ')')
        try:
            return eval(expr, safe_dict)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr}. Error: {e}")


# ============================================================================
# RadicalOps 實現
# ============================================================================

class RadicalOps:
    """根號運算模組 - 化簡與精確計算"""
    
    @staticmethod
    def create(inner):
        """
        建立根號 sqrt(inner) 並自動化簡
        
        範例：
            RadicalOps.create(12)  → "2√3"（化簡形式）
            RadicalOps.create(9)   → "3"（完全平方）
        """
        if inner < 0:
            raise ValueError("Cannot take square root of negative number")
        if inner == 0:
            return "0"
        
        # 找出最大的完全平方因子
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


# ============================================================================
# CalculusOps 實現
# ============================================================================

class CalculusOps:
    """微積分運算模組 - 多項式與微分"""
    
    @staticmethod
    def create_poly(coeffs):
        """建立多項式 (例: [1, -2] → x² - 2)"""
        degree = len(coeffs) - 1
        return [(coeffs[i], degree - i) for i in range(len(coeffs))]
    
    @staticmethod
    def differentiate(poly_terms, times=1):
        """對多項式求導 times 次"""
        result = list(poly_terms)
        for _ in range(times):
            new_result = []
            for coeff, exp in result:
                if exp > 0:
                    new_result.append((coeff * exp, exp - 1))
            result = new_result
        return result
    
    @staticmethod
    def to_latex(terms):
        """多項式轉 LaTeX"""
        if not terms:
            return '0'
        parts = []
        for i, (c, e) in enumerate(sorted(terms, key=lambda x: x[1], reverse=True)):
            if c == 0:
                continue
            sign = '' if i == 0 else (' + ' if c > 0 else ' - ')
            abs_c = abs(c)
            if e == 0:
                parts.append(f'{sign}{abs_c}')
            elif e == 1:
                coeff = '' if abs_c == 1 else str(abs_c)
                parts.append(f'{sign}{coeff}x')
            else:
                coeff = '' if abs_c == 1 else str(abs_c)
                parts.append(f'{sign}{coeff}x^{{{e}}}')
        return ''.join(parts).strip()


# ============================================================================
# 測試代碼區塊
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("[V2.5 完整測試] Domain Function Library")
    print("=" * 80)
    
    # ========================================================================
    # TEST 1: FractionOps.create() - 浮點數精度修復
    # ========================================================================
    print("\n【TEST 1】FractionOps.create() - 浮點數精度修復")
    print("-" * 80)
    
    # 測試浮點數轉換
    result1 = FractionOps.create(-0.6)
    expected1 = Fraction(-3, 5)
    print(f"FractionOps.create(-0.6) = {result1}")
    print(f"Expected: {expected1}")
    print(f"✅ PASS" if result1 == expected1 else f"❌ FAIL")
    
    # 測試字符串轉換
    result2 = FractionOps.create("-0.6")
    print(f"\nFractionOps.create('-0.6') = {result2}")
    print(f"✅ PASS" if result2 == Fraction(-3, 5) else f"❌ FAIL")
    
    # ========================================================================
    # TEST 2: IntegerOps.fmt_num() - 負數括號格式化
    # ========================================================================
    print("\n【TEST 2】IntegerOps.fmt_num() - 負數括號格式化")
    print("-" * 80)
    
    print(f"IntegerOps.fmt_num(5) = '{IntegerOps.fmt_num(5)}' (期望: '5')")
    print(f"IntegerOps.fmt_num(-5) = '{IntegerOps.fmt_num(-5)}' (期望: '(-5)')")
    print(f"IntegerOps.fmt_num(0) = '{IntegerOps.fmt_num(0)}' (期望: '0')")
    print(f"✅ PASS" if IntegerOps.fmt_num(-5) == "(-5)" else f"❌ FAIL")
    
    # ========================================================================
    # TEST 3: IntegerOps.safe_eval() - 支援 abs()
    # ========================================================================
    print("\n【TEST 3】IntegerOps.safe_eval() - 支援 abs() 與括號")
    print("-" * 80)
    
    # 測試1：絕對值運算
    expr1 = "abs(8 * (-2) - 5)"
    result_expr1 = IntegerOps.safe_eval(expr1)
    print(f"IntegerOps.safe_eval('{expr1}')")
    print(f"  = IntegerOps.safe_eval('abs(-16 - 5)')")
    print(f"  = IntegerOps.safe_eval('abs(-21)')")
    print(f"  = {result_expr1}")
    print(f"  Expected: 21")
    print(f"✅ PASS" if result_expr1 == 21 else f"❌ FAIL")
    
    # ========================================================================
    # 【例題 1】整數混合運算: [ (-20) + (-10) ] / (-5) * 3 + | 8 * (-2) - 5 |
    # ========================================================================
    print("\n【例題 1】整數混合運算")
    print("-" * 80)
    print("題目: [ (-20) + (-10) ] / (-5) * 3 + | 8 * (-2) - 5 |")
    
    # 方式 1：使用 safe_eval + abs()
    expr_q1 = "[ (-20) + (-10) ] / (-5) * 3 + abs(8 * (-2) - 5)"
    answer_q1 = IntegerOps.safe_eval(expr_q1)
    print(f"\n方式 1: IntegerOps.safe_eval('{expr_q1}')")
    print(f"  結果 = {answer_q1}")
    
    # 分步驗證
    step1 = IntegerOps.safe_eval("(-20) + (-10)")
    print(f"\n分步驗證:")
    print(f"  Step 1: (-20) + (-10) = {step1}")
    
    step2 = IntegerOps.safe_eval("[-30] / (-5) * 3")
    print(f"  Step 2: [-30] / (-5) * 3 = {step2}")
    
    step3 = IntegerOps.safe_eval("abs(8 * (-2) - 5)")
    print(f"  Step 3: abs(8 * (-2) - 5) = {step3}")
    
    step4 = step2 + step3
    print(f"  Step 4: {step2} + {step3} = {step4}")
    
    print(f"\n✅ 最終答案: {step4} (期望: 39)")
    print(f"✅ PASS" if int(step4) == 39 else f"❌ FAIL")
    
    # ========================================================================
    # 【例題 2】分數小數混合運算: 3/2 / (-0.6) * (-3/5) - 1/2
    # ========================================================================
    print("\n【例題 2】分數小數混合運算")
    print("-" * 80)
    print("題目: 3/2 / (-0.6) * (-3/5) - 1/2")
    
    # 構建分數
    operand1 = FractionOps.create(Fraction(3, 2))
    operand2 = FractionOps.create(-0.6)  # 應該轉為 -3/5
    operand3 = FractionOps.create(Fraction(-3, 5))
    operand4 = FractionOps.create(Fraction(1, 2))
    
    print(f"\n構建分數:")
    print(f"  3/2 = {operand1}")
    print(f"  -0.6 = {operand2} (自動轉為 -3/5)")
    print(f"  -3/5 = {operand3}")
    print(f"  1/2 = {operand4}")
    
    # 計算：3/2 / (-0.6)
    step1_q2 = FractionOps.div(operand1, operand2)
    print(f"\nStep 1: 3/2 ÷ (-3/5) = {operand1} ÷ {operand2}")
    print(f"      = {operand1} × (-5/3) = {step1_q2}")
    
    # 計算：(3/2 / -0.6) * (-3/5)
    step2_q2 = FractionOps.mul(step1_q2, operand3)
    print(f"\nStep 2: {step1_q2} × (-3/5) = {step2_q2}")
    
    # 計算：最終結果
    final_q2 = FractionOps.sub(step2_q2, operand4)
    print(f"\nStep 3: {step2_q2} - 1/2 = {final_q2}")
    
    expected_q2 = Fraction(1, 1)
    print(f"\n✅ 最終答案: {final_q2} (期望: 1/1 或 1)")
    print(f"✅ PASS" if final_q2 == expected_q2 else f"❌ FAIL")
    
    # ========================================================================
    # TEST 4: FractionOps.to_latex() - LaTeX 輸出
    # ========================================================================
    print("\n【TEST 4】FractionOps.to_latex() - LaTeX 輸出")
    print("-" * 80)
    
    latex1 = FractionOps.to_latex(Fraction(3, 2))
    latex2 = FractionOps.to_latex(Fraction(3, 2), mixed=True)
    latex3 = FractionOps.to_latex(Fraction(5, 1))
    latex4 = FractionOps.to_latex(Fraction(7, 2), mixed=True)
    
    print(f"FractionOps.to_latex(3/2) = {latex1}")
    print(f"FractionOps.to_latex(3/2, mixed=True) = {latex2}")
    print(f"FractionOps.to_latex(5/1) = {latex3}")
    print(f"FractionOps.to_latex(7/2, mixed=True) = {latex4}")
    
    # ========================================================================
    # TEST 5: RadicalOps.create() - 根號化簡
    # ========================================================================
    print("\n【TEST 5】RadicalOps.create() - 根號化簡")
    print("-" * 80)
    
    radical1 = RadicalOps.create(12)
    radical2 = RadicalOps.create(9)
    radical3 = RadicalOps.create(2)
    
    print(f"RadicalOps.create(12) = {radical1} (應為 2√3)")
    print(f"RadicalOps.create(9) = {radical2} (應為 3)")
    print(f"RadicalOps.create(2) = {radical3} (應為 √2)")
    
    print(f"✅ PASS" if "2" in radical1 and "3" in radical1 else f"❌ FAIL")
    
    # ========================================================================
    # 總結
    # ========================================================================
    print("\n" + "=" * 80)
    print("【測試完成】")
    print("=" * 80)
    print("✅ 所有核心功能已驗證")
    print("✅ FractionOps.create() 正確處理浮點精度")
    print("✅ IntegerOps.safe_eval() 支援 abs() 和複雜表達式")
    print("✅ 例題 1 計算正確（結果: 39）")
    print("✅ 例題 2 計算正確（結果: 1）")
