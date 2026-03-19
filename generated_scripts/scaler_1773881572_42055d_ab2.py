Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** Edge AI — 根式四則運算 (Radical Arithmetic).
    *   **Task:** Generate a math problem based on specific constraints and patterns.
    *   **Input:** `{{OCR_RESULT}}` (which is empty/placeholder in this context, but the prompt provides a specific example structure to follow).
    *   **Constraints:**
        *   **NO SymPy:** Strictly forbidden. Use `math`, `fractions`, and custom `RadicalOps` logic.
        *   **Pattern Matching:** Must match one of the provided patterns (p0-p7, etc.) or use Path B (Coder) if no match.
        *   **Output Format:**
            *   Path A (Catalogue Hit): Output 3 lines (`pattern_id`, `difficulty`, `term_count`). No code.
            *   Path B (Coder): Output a `def generate(level=1, **kwargs):` function.
        *   **Specific Example Constraint:** The prompt ends with a specific example structure: `計算下列各式的值。⑴ $(-2)\\times3\\sqrt{5}$`.
        *   **Hard Constraints on the Example:**
            *   Exactly 4 numbers involved.
            *   Exactly 1 operator (`times`).
            *   Operator order: `times`.
            *   Must keep square brackets `[]` structure (1 bracket block).
            *   Inside the 1st bracket block: 1 number, 0 operators.
            *   Negative numbers must be in parentheses `(-7)`.
            *   No `abs()`.
            *   No extra operators.
        *   **Verification:** The output must match the "Example Structure" provided at the very end of the prompt strictly.
        *   **Input Data:** The prompt says `{{OCR_RESULT}}` but doesn't provide actual OCR text. However, the last section gives a specific target example: `計算下列各式的值。⑴ $(-2)\\times3\\sqrt{5}$`. I need to generate a problem that matches this specific structure/constraints provided in the "Dynamic Target Problem Type Reference" section.
        *   **Wait, looking closer:** The prompt ends with `【題型同構硬性約束】...`. This implies I need to generate a problem that fits the *example* provided in the constraint section, or generate a new one that follows the *rules* defined for that example.
        *   **Actually:** The prompt asks me to act as the Edge AI. The input `{{OCR_RESULT}}` is likely a placeholder. The instruction says "依題型擇一路徑" (Choose a path based on problem type). Since I don't have OCR input, I should probably generate a problem that fits the "Path B" (Coder) requirement if it doesn't match a specific catalogue pattern, OR match the specific example structure given at the end.
        *   **Crucial:** The prompt ends with a specific example: `計算下列各式的值。⑴ $(-2)\\times3\\sqrt{5}$`. And constraints: "數字總數量必須嚴格一致：恰好 4 個參與計算的數字", "二元運算子總數必須嚴格一致：恰好 1 個運算子", "運算子順序必須完全一致：times", "必須保留中括號結構 []", "第 1 個中括號內：數字=1，運算子=0".
        *   **Interpretation:** I need to generate a Python function `generate()` that creates a problem matching the structure of `(-2)×3√5`.
        *   **Wait, one more check:** The prompt says "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】". It asks to choose a path. Since I am generating a problem *now*, and the last section specifies a specific example structure to follow ("【動態目標題型參考】"), I should probably follow the "Path B" (Coder) instructions to generate a problem that matches the constraints listed in the "【題型同構硬性約束】" section.
        *   **However**, the prompt also says "【🚨 最終約束：禁止 SymPy】... 3. 嚴禁在 Python 區塊外寫任何文字解釋。".
        *   **Decision:** I will generate a Python function `generate()` that creates a problem matching the specific constraints of the example `(-2)×3√5` (Path B), ensuring all hard constraints (4 numbers, 1 operator, brackets, etc.) are met.
        *   **Wait, looking at the very last lines:** "【題型同構硬性約束】... 1) 數字總數量必須嚴格一致：恰好 4 個參與計算的數字... 5) 必須保留中括號結構 []...".
        *   **Wait, the example is:** `(-2)×3√5`.
            *   Numbers: -2, 3, 5 (inside sqrt). That's 3 numbers. Wait, constraint says "恰好 4 個參與計算的數字".
            *   Let's count: `(-2)` is one number. `3` is one number. `5` is one number. Where is the 4th? Maybe the coefficient of the root is implicit? Or maybe `3√5` counts as 2 numbers (3 and 5)?
            *   Let's re-read: "恰好 4 個參與計算的數字 (算式中出現幾個數字，你就只能宣告幾個變數)".
            *   Example: `(-2)×3√5`.
                *   Number 1: -2
                *   Number 2: 3
                *   Number 3: 5
                *   Where is the 4th? Maybe the prompt implies I should generate a problem where there are 4 numbers.
                *   Constraint 5: "必須保留中括號結構 []". The example `(-2)×3√5` has `(-2)`. Is that `[]`? No, it's `()`.
                *   Constraint 5.1: "第 1 個中括號內：數字=1，運算子=0".
                *   This implies the structure should look like `(-2)`.
                *   Wait, the constraint says "必須保留中括號結構 []". But the example uses `()`.
                *   Let's look at the constraint text again: "5) 必須保留中括號結構 []，不得改成一般括號或移除。5.1) 第 1 個中括號內：數字=1，運算子=0（+0/-0/×0/÷0）".
                *   This seems contradictory to the example `(-2)`.
                *   However, the instruction says "【題型同構硬性約束】". This usually means "Follow these constraints for the output".
                *   If I must follow the "4 numbers" constraint, I need to construct a problem like `(-2) × 3√5` but ensure there are 4 numbers. Maybe `(-2) × 3√5` is considered 3 numbers. To get 4, maybe `(-2) × 3√5 + 1`? No, that adds an operator.
                *   Maybe the constraint means "Variables declared in code must match numbers in problem".
                *   Let's look at the "Correct Code Structure Example" provided in Path B:
                    ```python
                    def generate(level=1, **kwargs):
                        import random
                        c1 = random.choice([2, 3, 4])
                        c2, r = random.choice([-3, -2, 2, 3]), 5
                        ...
                        return {
                            'question_text': f"計算 ${t1} \\times {t2}$ 的值",
                            'correct_answer': RadicalOps.format_expression({r: c1 * c2}),
                            'mode': 1
                        }
                    ```
                *   This example code generates `c1 * c2 * sqrt(r)`.
                *   The specific constraint at the end says: "【動態目標題型參考】計算下列各式的值。⑴ $(-2)\\times3\\sqrt{5}$".
                *   And "【題型同構硬性約束】".
                *   This implies I need to generate a problem that looks like `(-2)×3√5` but adheres to the "4 numbers" rule.
                *   Wait, `(-2)` is one number. `3` is one number. `5` is one number. That's 3.
                *   Maybe the constraint "4 numbers" applies to a different problem type, but the instruction says "【動態目標題型參考】... ⑴ $(-2)\\times3\\sqrt{5}$".
                *   Okay, I will prioritize the "Path B" code structure and the specific constraints listed at the very end (4 numbers, 1 operator, brackets, etc.).
                *   To satisfy "4 numbers" with `(-2) × 3√5`, I might need to adjust the numbers or interpretation.
                *   Actually, looking at the constraint: "1) 數字總數量必須嚴格一致：恰好 4 個參與