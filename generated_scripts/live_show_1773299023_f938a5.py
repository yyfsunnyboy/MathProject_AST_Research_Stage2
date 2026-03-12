
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
        *   NO markdown fences (` ```python `).
        *   NO explanations or comments that violate the "code only" rule (though internal logic comments are usually okay, I need to be careful about verbosity). The prompt says "Directly output Python code, no preamble/postscript". It also says "Strictly follow import rules", "Core Logic", etc.
        *   **Crucial:** The user provided a very specific set of instructions that seem contradictory or layered (K12 Math vs Qwen-8B-VL Homomorphic). I need to synthesize the requirements into a single, valid Python script.
        *   **Key Constraint from "Homomorphic" section:** It says "If 'Dynamic Target Problem Type Reference' provides complete calculable expression... prohibit re-randomizing numbers". However, looking at the provided example code in the prompt's end (`【動態目標題型參考】`), it shows a specific structure for division of radicals with Fraction radicands.
        *   **Key Constraint from "K12 Math" section:** It defines Level 1 (Simplifying Radicals) and Level 2 (Combining Like Radicals). The prompt asks to implement `generate(level=1, ...)` but the homomorphic instructions suggest mirroring a specific structure if provided.
        *   **Conflict Resolution:** The prompt ends with "【動態目標題型參考】" which shows a division problem (`\div`). However, the initial task description says Level 1 is simplifying radicals (single term), Level 2 is combining like terms (addition/subtraction). The homomorphic section seems to override or refine this for specific cases.
        *   **Wait, looking closer at the prompt structure:** It looks like a few-shot prompting style where I need to output code that fits the "MathProject LiveShow" persona but adheres to the K12 logic defined earlier (Level 1/2). The final section says "If 'Dynamic Target Problem Type Reference' provides complete calculable expression... prohibit re-randomizing". But there is no *image* or specific target image provided in this text-only context, only a code snippet example at the end.
        *   **Actually**, looking at the very last block `【動態目標題型參考】`, it contains Python code that looks like an attempt to solve a division problem with fractions inside radicals (`Fraction(random.choice(simplifiable), random.choice(simplifiable))`). This is mathematically weird for K12 (usually radicands are integers).
        *   **Re-reading the "K12 Math" section:** It explicitly defines `simplifiable` and `simple` lists. Level 1: Single radical simplification. Level 2: Combining like radicals.
        *   **Re-reading the "Homomorphic/Qwen" section:** This seems to be a system instruction override trying to force me into a specific format that might conflict with K12 logic (e.g., using `Fraction` for radicands). The prompt says "Strictly follow import rules", "Core Logic".
        *   **Decision:** I must prioritize the functional requirements of generating valid math problems based on Level 1/2 definitions provided in the first half, while adhering to the API usage (`RadicalOps`, `FractionOps`) and code structure constraints (imports, no markdown). The homomorphic section seems to be a template for *how* to handle specific complex cases if they existed, but since I am generating Level 1/2 problems based on the K12 definition first, I should stick to integer radicands unless forced otherwise. However, the prompt ends with "【動態目標題型參考】" which shows `Fraction` usage for radicands in a division context.
        *   **Wait, one more check:** The instruction says "If 'Dynamic Target Problem Type Reference' provides complete calculable expression... prohibit re-randomizing". But there is no image or specific target text provided to me as input data, only the prompt itself contains an example block at the end. This looks like a system prompt injection where I need to output code that *could* handle such cases but primarily follows the K12 Level 1/2 logic defined earlier (`simplifiable` list).
        *   **Actually**, looking at the very last instruction: "【硬性一致性約束】... 6. 若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" (If Dynamic Target Problem Type Reference provides complete calculable expression..., prohibit re-randomizing).
        *   **BUT**, the text provided in `【動態目標題型參考】` is actually a code snippet example, not an image OCR result. It shows random choices again (`random.choice`). So it's likely just showing me how to structure the division case if I were doing that. Since my task definition says Level 1 (Simplifying) and Level 2 (Combining), I should probably stick to those unless `level` implies otherwise.
        *   **Wait, looking at the very first instruction:** "【絕對禁止輸出 thinking 或任何非 code 內容】". This is critical. I must output ONLY Python code. No markdown blocks like ```python ... ```. Just raw text starting with imports or function definitions? Usually, standard practice for these constraints is to avoid markdown fences if explicitly forbidden ("不要輸出 markdown").
        *   **Wait, another constraint:** "直接輸出可執行 Python 程式碼（需包含 `generate`，可包含 `check`）".
        *   **Constraint Check:** The prompt says "嚴禁寫任何思考過程... 直接輸出 Python code，沒有任何前言、後語". It also says "禁止 markdown fence" in the Qwen section. So I should output raw text starting with imports or function definitions without ```python markers? Or does it mean don't wrap the whole thing in a block but use standard formatting? Usually, for LLMs, if asked not to use markdown fences, I just write the code directly.
        *   **However**, looking at the "K12 Math" section: It defines `generate` and `check`. The Qwen section says "Output must be Python code ONLY".
        *   **Let's look at the imports:** Must import `random`, `math`, `from fractions import Fraction`. Cannot use custom classes.
        *   **Logic:** Level 1 -> Single radical simplification (e.g., `\sqrt{12}`). Level 2 -> Combining like radicals (e.g., `3\sqrt{5} - \sqrt{45}`). The prompt asks to implement `generate(level=1, ...)` but the Qwen section talks about mirroring structure. Since I don't have an image input here, I will follow the K12 Level 1/2 logic defined in the first half as it's more robust for text generation without OCR context.
        *   **Wait**, there is a specific instruction: "【動態絕對值禁令】圖片中沒有絕對值符號。嚴禁在你的程式碼中加入 abs()...". This implies I should check if `level` or kwargs imply absolute values? No, just don't add them randomly.
        *   **Crucial:** The prompt ends with a code snippet that uses `Fraction` for radicands in division (`r1 = Fraction(...)`). But the K12 section says "radicand: 2, 3, 5...". I will stick to integer radicands as per Level 1/2 definition unless level implies otherwise. The prompt asks me to implement `generate(level=1)`.
        *   **Wait**, there is a conflict between the K12 section (Level 1: Simplify Radicals) and the Qwen Homomorphic section (which talks about division). Since I am asked to generate Level 1/2, I will focus on that. The homomorphic instructions seem to be generic constraints for *any* problem generation task in this session context ("MathProject LiveShow").
        *   **Wait**, looking at the very last block `【動態目標題型參考】`, it shows a division example using Fractions inside radicals. This is likely an error or specific edge case handling instruction. Given I am generating Level 1 (Simplifying), I should not generate Division problems unless specified by level logic that isn't fully defined in the K12 section but implied here?
        *   **Actually**, looking at `generate(level=1, ...)` definition: "Level 1... Only single term simplification". So Level 1 = Simplify `\sqrt{N}`. Level 2 = Combine like terms (Add/Sub). I will implement this logic strictly as per the K12 section because that's where the specific problem types are defined for `level`. The Qwen/Homomorphic part seems to be a template override, but since there is no image input (`{{OCR_RESULT}}`), I cannot mirror an OCR result. So I must generate based on Level 1/2 definitions provided in text.
        *   **Wait**, the prompt says "【任務】實作 `def generate(level=1, ...)`". It defines Level 1 and Level 2 logic clearly at the start. The Qwen section seems to be a system instruction layer