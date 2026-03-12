
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
        *   Structure must match "Homomorphic" requirements if provided in examples (though here specific level logic is defined first, then homomorphism rules apply to the structure of generation based on `level`). The prompt provides a mix of instructions. I need to prioritize the explicit Level 1/2 definitions while adhering to the strict API usage and formatting constraints found in the "Homomorphic" section (e.g., using LaTeX for output).
        *   **Crucial:** The prompt contains conflicting sections ("K12 Math Algorithm Engineer" vs "MathProject LiveShow Structure Homomorphism"). However, the core task is `generate(level=...)`. Level 1 = Simplify Radical. Level 2 = Combine Like Radicals (Add/Sub).
        *   **Strict Constraint:** Do not output markdown fences (```python), do not output explanations. Just raw code or minimal text if absolutely necessary but better to follow "Direct Python Code". Wait, the instruction says "直接輸出 Python code，沒有任何前言、後語" and later "只輸出 Python 原始碼。不要輸出任何額外文字。不要輸出 markdown."
        *   **API Usage:** Must use `RadicalOps.xxx`. Do not define them.
        *   **Logic:** Use `(coeff, radicand)` tuples/lists for state. Avoid parsing LaTeX strings to extract numbers (e.g., don't do `int(term.split(...))`).

2.  **Determine Logic Flow:**
    *   Imports: `import random`, `import math`, `from fractions import Fraction`.
    *   Function `generate(level=1, **kwargs)`:
        *   If level == 1 (Easy): Generate one unsimplified radical term like `\sqrt{N}`. Simplify it internally to get the answer. Format question as "化簡 $\sqrt{...}$". Answer is simplified form.
        *   If level == 2 (Normal): Generate multiple terms with same radicand structure for addition/subtraction. E.g., `3\sqrt{12} - \sqrt{27}`. Simplify each, combine like radicals. Format question as expression string. Answer is combined result.
    *   Function `check(user_answer, correct_answer)`: Simple string comparison.
    *   **Homomorphism Constraint:** The prompt includes a section about "MathProject LiveShow Structure Homomorphic Output Engine" which emphasizes mirroring structure (number of terms, operators). However, the specific task definition says Level 1 = Single term, Level 2 = Add/Sub like radicals. I should follow the `level` parameter logic primarily but ensure the output format matches LaTeX standards using `RadicalOps`.
    *   **Specific Constraint:** "嚴禁寫任何思考過程、解釋、註解". "直接輸出 Python code，沒有任何前言、後語".
    *   **API Check:** The prompt says `Fraction(num, den)` is available (via import). It mentions `FractionOps.create` but standard python `Fraction` works. I should use the injected ones if specified (`RadicalOps.simplify_term`, etc.).
    *   **Randomization:** Use `random.choice` for coefficients and radicands from provided lists to ensure variety, not hardcoding specific numbers unless level dictates a structure (but here we generate random problems). The "Homomorphic" section warns against hardcoding original problem numbers if generating new ones. Since this is generation logic, I must use randomness within the defined ranges.
    *   **Formatting:** Use `RadicalOps.format_term_unsimplified` for question parts and `RadicalOps.format_expression` for final answer.

3.  **Drafting Code (Mental):**
    ```python
    import random
    import math
    from fractions import Fraction

    def generate(level=1, **kwargs):
        # Lists of numbers as per prompt requirements
        simplifiable = [8, 12, 18, 20, 24, 27, 32, 45, 48, 50, 72, 75]
        simple = [2, 3, 5, 7, 11]

        # Logic for Level 1: Single Radical Simplification
        if level == 1:
            radicand = random.choice(simplifiable)
            coeff = Fraction(1, 1) # Implicitly 1 unless specified otherwise in prompt logic? Prompt says "Single term". Usually \sqrt{N}. So coeff=1.
            
            # Question text needs to be formatted. 
            # RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True) -> "\sqrt{...}" or similar
            
            q_part = RadicalOps.format_term_unsimplified(1, radicand, True)
            question_text = f"化簡 $\\sqrt{{{radicand}}}$ 的值。" # Or use the API formatted string directly? 
            # Prompt says: Level 1: Single unsimplified radical. Question text: "Simplify \sqrt{...}"
            
            # Calculate Answer (Internal Logic)
            c, r = RadicalOps.simplify_term(1, radicand)
            final_terms = {r: c}
            correct_answer = RadicalOps.format_expression(final_terms)

        # Logic for Level 2: Combining Like Radicals
        elif level == 2:
            num_terms = random.randint(3, 4) # Prompt says "Level 2 (Normal): ... only addition/subtraction" and example shows multiple terms. 
                                            # Wait, prompt says "同類方根的合併". Usually means same radicand after simplification or similar structure?
                                            # Example: `2\sqrt{12} - \sqrt{27}` -> simplify 12->3*4 (2 sqrt(3)), 27->9*3 (3 sqrt(3)). 
                                            # So we need to generate terms that become like radicals.
            
            # To ensure they are "like" after simplification, pick a base simple radicand and multiply by squares?
            # Or just use the provided 'simplifiable' list which contains multiples of primes in 'simple'.
            # Let's create multiple terms with different unsimplified forms that simplify to same root.
            
            target_simple = random.choice(simple)
            term_data = []
            for i in range(num_terms):
                coeff_sign = random.choice([-1, 1]) * random.randint(1, 5) # Coeff -5~5 non-zero? Prompt says -5 to 5.
                if coeff_sign == 0: continue
                
                # We need radicands that simplify to target_simple (or similar). 
                # To keep it simple for generation logic without complex factorization checks inside random loop:
                # Just pick from simplifiable list, but ensure they are compatible? 
                # Actually, standard K12 problem gen usually picks 'simplifiable' numbers.
                # Let's just generate terms using the provided lists and let RadicalOps handle compatibility or assume user inputs valid ones for Level 2 logic defined in prompt: "同類方根的合併".
                
                r = random.choice(simplifiable) 
                c_val = Fraction(random.randint(-5, 5), 1) # Coeff -5 to 5
                
                term_data.append((c_val, r))

            # Construct Question String manually or via API? Prompt says "Level 2: ... only addition/subtraction".
            # Use RadicalOps.format_term_unsimplified for each part.
            
            terms_dict = {}
            question_parts = []
            
            for i in range(num_terms):
                c, r = term_data[i]
                formatted_part = RadicalOps.format_term_unsimplified(c, r, is_first=(i==0))
                
                # Logic to combine: Simplify each first? 
                # The prompt says "Level 2 ... Combining Like Radicals". 
                # Usually this means the question shows unsimplified forms (e.g. sqrt(12) + sqrt(3)), answer simplifies them and combines.
                # Or it implies terms that are already like radicals after simplification? 
                # Example: `2\sqrt{12} - \sqrt{27}` -> 4\sqrt{3} - 3\sqrt{3} = \sqrt{3}.
                
                # Let's simplify each term to find the 'like' radicand.
                c_s, r_s = RadicalOps.simplify_term(c, r)