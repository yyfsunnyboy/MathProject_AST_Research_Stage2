
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
        """格式化單項根式 (LaTeX)"""
        if coeff == 0: return ""
        c_val, r_val = RadicalOps.simplify_term(coeff, radicand)
        if r_val == 1:
            if is_first: return str(c_val)
            return f" + {c_val}" if c_val > 0 else f" - {-c_val}"
        
        sign = ""
        if not is_first:
            sign = " + " if c_val > 0 else " - "
        elif c_val < 0:
            sign = "-"
            
        abs_c = abs(c_val)
        c_str = "" if abs_c == 1 else str(abs_c)
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
        """格式化多項根式表達式 (terms_dict: {radicand: coeff})"""
        if not terms_dict: return "0"
        
        # 1. 內部化簡合併
        simplified = {}
        for r, c in terms_dict.items():
            if c == 0: continue
            c_s, r_s = RadicalOps.simplify_term(c, r)
            simplified[r_s] = simplified.get(r_s, 0) + c_s
        
        simplified = {r: c for r, c in simplified.items() if c != 0}
        if not simplified: return "0"
        
        # 2. 處理分母約分
        if denominator != 1:
            import math
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

# [Global Aliases for AI Convenience]
simplify_term = RadicalOps.simplify_term
format_term = RadicalOps.format_term
format_term_unsimplified = RadicalOps.format_term_unsimplified
format_expression = RadicalOps.format_expression


# ==============================================================================
# [AUTO-INJECTED RESOURCE] FractionOps
# ==============================================================================
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
        """輸出 LaTeX 格式"""
        if isinstance(val, Fraction):
            if val.denominator == 1:
                return str(val.numerator)
            if mixed and abs(val.numerator) > val.denominator:
                whole = abs(val.numerator) // val.denominator  # [Fix] use abs() to avoid Python floor-division error for negatives
                remainder = abs(val.numerator) % val.denominator
                if remainder == 0:
                    return str(-whole if val < 0 else whole)
                sign = "-" if val < 0 else ""
                return f"{sign}{whole} \\frac{{{remainder}}}{{{val.denominator}}}"
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
        """分數除法"""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

def generate(level=1, **kwargs)` to generate radical simplification and arithmetic problems.
    *   **Constraints:**
        *   No thinking process output (`/no_think`).
        *   No markdown fences (```python ... ```).
        *   No explanatory text before or after the code.
        *   Strict adherence to import rules (`import random`, `import math`, `from fractions import Fraction`), no custom imports for ops.
        *   Use injected APIs: `RadicalOps.simplify_term`, `RadicalOps.format_term_unsimplified`, `RadicalOps.format_expression`, `FractionOps.create`.
        *   Logic must be based on integer/fraction operations, not parsing LaTeX strings to get values (except formatting).
        *   Level 1: Single radical simplification.
        *   Level 2: Combining like radicals (addition/subtraction).
        *   Structure Homomorphism: Must mirror the target problem structure if provided (though in this specific prompt, there is a "Dynamic Target Problem Type Reference" section that looks like code snippets to follow or adapt from). However, looking closely at the end of the prompt ("【動態目標題型參考】"), it provides a *specific* example logic for division with fractions.
        *   **Crucial Conflict Resolution:** The prompt contains conflicting instructions between "Level 1/2" definitions and the "Homomorphic Structure" section which seems to demand specific LaTeX formatting (`\times`, `\div`) and Fraction handling even if Level is simple. However, looking at the very last instruction block:
            *   `【動態目標題型參考】` shows a code snippet for division of radicals with fractions.
            *   `【硬性一致性約束（必須遵守）】` says "Strictly mirror target problem type structure...".
            *   BUT, the initial task description defines Level 1 (Simplifying Radicals) and Level 2 (Combining Like Radicals).
            *   The prompt ends with a specific code block example that uses division (`\div`) and Fraction radicands.
            *   **Decision:** I need to follow the core `generate` function definition provided in the "K12 Math Algorithm Engineer" section primarily, but ensure it respects the API usage rules. However, there is a strong instruction at the end: "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". This suggests I should perhaps follow the structure of the reference if possible, OR implement Level 1/2 logic as defined in the beginning which seems more standard for this task.
            *   Wait, looking at the very last block: `【動態目標題型參考】` contains a specific code snippet that looks like it was generated by an AI or is part of the prompt's example to be followed closely ("Strictly mirror target problem type structure"). But there isn't actually an image OCR result provided (`{{OCR_RESULT}}`).
            *   The instruction says: "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". Since I don't have a specific fixed template to copy (no `OCR_RESULT`), I must generate random problems based on the Level definitions.
            *   However, there is a strong constraint at the end: "Strictly mirror target problem type structure... Do not add operations not in original title." This implies if I choose Level 1/2 as defined earlier, I should stick to that (Add/Sub for Lvl 2). The reference code snippet shows division.
            *   **Resolution:** I will implement the `generate` function based on the initial task definition (Level 1: Simplify single radical, Level 2: Combine like radicals) because there is no specific "Target Problem" image provided to mirror exactly. The instruction about mirroring seems to be a template for when OCR results are present. Since I am generating from scratch (`level=1` or `**kwargs`), I will follow the initial task definition (Level 1/2 logic).
            *   **Wait, re-reading carefully:** The prompt ends with "【動態目標題型參考】" which shows a specific code block for division. But it also says "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". Since I am generating new problems (Level 1/2), I should randomize within the constraints of Level 1 or 2.
            *   **BUT**, there is a specific constraint: `【絕對禁止輸出 thinking 或任何非 code 內容】`. This means I must output ONLY Python code, no markdown fences.
            *   There is also a conflict about "Do not add operations...". Level 1 has only simplification (no + -). Level 2 has addition/subtraction. The reference snippet shows division. Since the user prompt asks for `def generate(level=1...)`, I should implement logic that handles level 1 and potentially level 2 if passed, but primarily focus on making it work correctly with the provided APIs (`RadicalOps`).
            *   **Key Constraint:** "Directly output Python code... No markdown". This is critical. The system instruction says `/no_think` at the very top. I must not use ```python ... ```. Just raw text starting with `import`.

2.  **Drafting the Code:**
    *   Imports: `random`, `math`, `from fractions import Fraction`.
    *   Functions: `generate(level=1, **kwargs)`, `check(user_answer, correct_answer)`.
    *   Logic for Level 1 (Simplifying Radicals): Generate a radicand from the "simplifiable" list. Coefficient usually 1 or -1 unless specified otherwise? The prompt says coeff range -5 to 5. For simplification tasks, often just `\sqrt{...}` is expected, but `coeff` can be part of it (e.g., `-2\sqrt{8}`). Let's stick to the definition: "Single term needing simplification".
    *   Logic for Level 2 (Combining Like Radicals): Generate multiple terms with same radicand after simplification. Add/Sub coefficients.
    *   API Usage: `RadicalOps.simplify_term`, `RadicalOps.format_expression`.
    *   Formatting: Use `format_term_unsimplified` for the question text, `format_expression` for the answer key.

3.  **Refining Logic based on "Homomorphic" constraints:**
    The prompt ends with a very specific block about mirroring structure and using `\times`, `\div`. However, Level 1/2 definitions say: Lvl 1 (Simplifying), Lvl 2 (Combining). I will implement these. If `level=3` or similar isn't defined in the initial task but implied by "Homomorphic", I should stick to the explicit definition of Level 1 and 2 provided at the start ("Level 1... Level 2...").
    Actually, looking at the very last instruction block: "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". Since there is no OCR result or specific fixed template image data here (it's text), I must generate random ones. The reference code snippet provided in the prompt *is* a target structure example, but it uses division (`\div`). Level 1/2 definitions do not mention multiplication/division explicitly as primary tasks for those levels (Lvl 1: Simplify single term; Lvl 2: Combine like radicals). I will stick to Add/Sub or Single Term logic unless `level` implies otherwise.
    Wait, the prompt says "Level 1... Level 2". It does not define Level 3+. So I should handle level=1 and level=2 specifically as described in the first paragraph of the task description. The later sections about `\times`, `\div` seem to be part of a template for handling OCR results which aren't present here.
    **Correction:** The prompt is extremely cluttered with conflicting instructions (K12 Engineer vs MathProject LiveShow). I need to prioritize the *Task* section at the beginning ("Level 1... Level 2") while adhering to the *API Usage* and *Import Rules*.
    
    However, there's a specific instruction: "【動態絕對值禁令】圖片中沒有絕對值符號。嚴禁在你的程式碼中加入 abs()". This is relevant if I were generating absolute value problems. Since Level 1/2 don't use them, this is fine.
    
    **Critical Constraint:** "Directly output Python code... No markdown fences". The system instruction `/no_think` and the prompt's top line `【絕對禁止輸出 thinking 或任何非 code 內容】` combined with `- 直接輸出 Python code，沒有任何前言、後語`. I must not wrap it in ```python.

    **Wait, one more check:** "嚴禁寫 'Okay, I need to...'".
    
    Okay, let's write the code based on Level 1 and Level 2 logic using `RadicalOps` APIs provided in the prompt description (even though they are injected).
    
    *   Imports.
    *   Define lists for simplifiable radicands (`[8, 12, ...]`) and simple ones (`[2, 3, ...]`).
    *   Function `generate`: