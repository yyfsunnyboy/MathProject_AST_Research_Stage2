
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
        *   NO thinking process output.
        *   NO non-code content.
        *   Direct Python code only.
        *   Strict import rules (`random`, `math`, `from fractions import Fraction`).
        *   Use injected APIs: `RadicalOps.simplify_term`, `RadicalOps.format_term_unsimplified`, `RadicalOps.format_expression`, `FractionOps.create` (or just `Fraction()`).
        *   NO parsing LaTeX strings to get values.
        *   Pure integer/fraction operations for logic, formatting only at the end.
        *   Level 1: Single radical simplification (`\sqrt{...}`).
        *   Level 2: Combining like radicals (addition/subtraction).
        *   Structure must match "Homomorphic" requirements if provided in examples (though here specific level logic is defined first, then homomorphism rules apply to the structure of generation based on `level`). The prompt provides a mix of instructions. I need to prioritize the core task definition (`generate` function) while adhering to the strict API usage and formatting constraints.
        *   Specific constraint: "If 'Dynamic Target Problem Type Reference' is provided... prohibit re-randomizing numbers". However, looking at the input, there isn't a specific target image or OCR result provided in this turn that overrides the `level` logic. The prompt says "Level 1 (Easy)... Level 2 (Normal)". I should follow these level definitions primarily but ensure code structure is robust.
        *   Wait, the prompt contains conflicting instructions: One part defines Level 1/2 specific behaviors (`generate(level=1)` vs `generate(level=2)`). Another part talks about "MathProject LiveShow Structure Homomorphic Output Engine" and mentions copying OCR results or matching target problem structures. Since there is no actual image/OCR result provided in this text prompt, I must rely on the explicit Level definitions (Level 1: Simplify single radical, Level 2: Combine like radicals).
        *   However, the "Homomorphic Output Engine" section says: "You are not 'freely generating', you are 'homomorphically imitating'." and "Must copy original example problem's radical structure...". Since there is no `OCR_RESULT` or specific target image provided in this text context (it looks like a system prompt injection scenario), I should focus on the explicit Level 1/2 logic defined at the beginning, while ensuring strict adherence to API usage (`RadicalOps`, `Fraction`).
        *   Actually, looking closely at the end of the prompt: "【動態目標題型參考】... 【硬性一致性約束（必須遵守）】". It seems like a template where I need to fill in or execute based on the provided logic. The instruction says "If 'Dynamic Target Problem Type Reference' is provided complete calculation formula... prohibit re-randomizing numbers". Since no specific target image/OCR is given *in this text*, but rather general level instructions, I will implement the `generate` function according to Level 1 and Level 2 specifications defined in the first part of the prompt.
        *   Wait, there's a conflict: The beginning says "Level 1... Level 2". The middle section talks about Qwen-8B-VL specialized engine with OCR results (which are empty here). I should prioritize the explicit `generate` function requirements for K12 Math Algorithm Engineer role.
        *   Crucial Constraint: **NO markdown fences** around code? "Output must be Python code ONLY". Usually, this means no ```python ... ```. Just raw text starting with imports or def. But standard practice in these strict constraints often allows the code block if it's just code. However, instruction says "Direct output Python code... No extra words". I will output plain text that is valid python script content.
        *   Wait, looking at the very last section: "【E. 最終輸出要求】 - Only output Python raw code. Do not output any extra words. Do not output markdown." -> This means no ```python``` blocks. Just the code string.
        *   Also need to handle `level` parameter logic inside `generate`.

2.  **Logic for Level 1:**
    *   Generate a single radical term like `\sqrt{N}` or `c\sqrt{N}` (though usually simplification implies coefficient is handled). The prompt says "Single unsimplified radical". Example: `\sqrt{12}`.
    *   Logic: Pick a radicand from the list of simplifiable numbers (`[8, 12, ...]`). Coefficient should be 1 for Level 1 based on examples like `\sqrt{12}`, but sometimes `c\sqrt{n}` is allowed if it's just one term. Let's stick to coefficient=1 or simple integer coeff from range -5~5 (non-zero).
    *   Simplify using `RadicalOps.simplify_term`.
    *   Format question: "化簡 $\sqrt{...}$".

3.  **Logic for Level 2:**
    *   Generate multiple terms with same radicand after simplification? No, combine like radicals (e.g., $2\sqrt{12} - \sqrt{27}$).
    *   Logic: Pick a base unsimplified radicand `r`. Create coefficients. Simplify each term individually first to find the common simplified radicand `s`, then sum coefficients. Or generate terms that simplify to same root.
    *   Better approach for Level 2 (Combining Like Radicals): Generate multiple terms like $c_1\sqrt{r} \pm c_2\sqrt{r}$ where they share a base after simplification? No, usually it's $\sqrt{A} + \sqrt{B}$ -> simplify A and B to see if radicands match.
    *   Prompt says: "Level 2 (Normal): Combining Like Radicals... e.g., $2\sqrt{12} - \sqrt{27}$". Note that `12` simplifies to `3`, `27` simplifies to `3`. So they become like terms.
    *   Algorithm: Pick a target simplified radicand (e.g., 3). Generate unsimplified versions of it (e.g., $4 \times 3 = 12$, $9 \times 3 = 27$) and assign random coefficients. Or pick from the `simplifiable` list which all reduce to primes in `simple`.
    *   Actually, simpler logic: Pick a base prime radicand (e.g., 5). Generate terms like $\sqrt{10}$ ($\sqrt{2 \times 5}$), $\sqrt{45}$ ($9 \times 5$) -> $3\sqrt{5}$.
    *   Let's use the provided `simplifiable` list. Pick two numbers from it that simplify to same radicand? Or just pick random coefficients and unsimplified forms, then let `RadicalOps.simplify_term` handle them in calculation logic (though we need to construct terms manually).
    *   To ensure they are "like radicals", I should generate multiple terms where the simplified radicands match.
    *   Example: Target root 3. Unsimplifiable inputs could be $12, 48$. Coefficients random.

4.  **API Usage:**
    *   `RadicalOps.simplify_term(coeff, radicand)` -> returns `(new_coeff, new_radicand)`. Note: coeff can be Fraction? The API description says `coeff` is passed to simplify. Usually simplification handles integer coeffs and radicands. If I use Fractions for coefficients in Level 2 (e.g., $-\frac{1}{3}\sqrt{5}$), the logic needs to handle that.
    *   `RadicalOps.format_term_unsimplified(coeff, radicand, is_first)` -> For question text. Supports Fraction? The prompt says "Supports Fraction".
    *   `RadicalOps.format_expression(terms_dict, denominator=1)` -> For answer key.

5.  **Code Structure:**
    *   Imports: `random`, `math`, `from fractions import Fraction`.
    *   Function definitions: `generate` and `check`.
    *   Inside `generate`: Handle level logic. Return dict.
    *   Ensure no markdown fences around the code block if strictly forbidden ("Do not output markdown"). I will write raw text starting with imports or def. Wait, usually "Python code" implies a script. If I start with `import`, it's fine. But often these prompts want just the function definitions? The prompt says "Directly output Python code". It shows examples including imports at top. So include imports.
    *   Constraint: "If 'Dynamic Target Problem Type Reference' is provided... prohibit re-randomizing numbers". Since no specific target image/OCR text exists in this context (it's a general instruction), I will randomize as per Level 1/2 specs, but ensure the structure matches the level description.
    *   Wait, one constraint says: "If 'Dynamic Target Problem Type Reference' is provided complete calculation formula... prohibit re-randomizing numbers". Since there isn't an OCR result here (it's a text prompt), I assume standard