Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** Edge AI — 根式四則運算 (Radical Arithmetic).
    *   **Task:** Process an input (implied from `{{OCR_RESULT}}`, but currently empty/placeholder) or generate a problem based on specific constraints.
    *   **Constraints:**
        *   **NO SymPy:** Strictly forbidden. Use `math`, `fractions`, and custom `RadicalOps` logic.
        *   **RadicalOps:** Must use specific APIs (`simplify`, `add_term`, `mul_terms`, `div_terms`, `format_term`, `format_expression`).
        *   **Pattern Matching:** Use the provided `Pattern Catalogue` (p0-p7) if applicable.
        *   **Output Format:**
            *   If Pattern Matched (Path A): Output 3 lines (`pattern_id`, `difficulty`, `term_count`).
            *   If No Pattern Match (Path B): Output a `def generate(...)` function block with specific structure.
        *   **LaTeX Formatting:** Strict rules (no `1\sqrt{x}`, handle negative signs correctly, etc.).
        *   **Structure Constraints:**
            *   Exactly 3 numbers involved in calculation (for the example provided in the prompt).
            *   Exactly 1 operator.
            *   Operator must be `times` (×).
            *   Must use `[]` brackets for negative numbers.
            *   No `abs()`.
            *   No extra operators.
    *   **Input:** The prompt ends with `{{OCR_RESULT}}` which is empty in this context. However, the instruction says "【範例題型】{{OCR_RESULT}}". Since there is no actual OCR result provided, I need to check if I should generate a *new* problem based on the constraints (Path B) or if I should simulate a response based on the "Example Problem Type" structure provided in the prompt's constraints.
    *   **Wait, looking closer at the prompt:** The prompt ends with `{{OCR_RESULT}}`. Usually, in a chat interface, this means I need to wait for input or generate a sample based on the constraints provided in the "Dynamic Target Problem Type Reference" section.
    *   **Specific Constraint:** "【同構零容忍檢查清單】... 1) 數字總數量必須嚴格一致：恰好 3 個參與計算的數字... 2) 二元運算子總數必須嚴格一致：恰好 1 個運算子 3) 運算子順序必須完全一致：times...".
    *   **Example:** `$(-2)\\times3\\sqrt{5}$`.
    *   **Goal:** Since there is no OCR input, I must assume the role of generating a problem that fits the strict constraints provided in the "Dynamic Target Problem Type Reference" section, specifically the example `$(-2)\\times3\\sqrt{5}$`.
    *   **However**, the prompt says "【範例題型】{{OCR_RESULT}}". If `{{OCR_RESULT}}` is empty, I should probably generate a sample problem that adheres to the "Path B" (Coder) requirements because there's no specific pattern to match from OCR.
    *   **BUT**, the instruction also says "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】".
    *   **Decision:** Since I cannot see the OCR result, I will generate a problem that fits the strict structural constraints mentioned in the "Dynamic Target Problem Type Reference" (3 numbers, 1 operator, times, brackets for negatives) as a demonstration of Path B, OR I should acknowledge the missing OCR.
    *   **Correction:** In many RLHF/Agent contexts, if the input is `{{OCR_RESULT}}`, it implies I should process that. Since it's empty, I should probably generate a *valid* example that follows the rules to show I understand the constraints, or ask for input. However, the system instruction implies I am the AI. I will generate a problem based on the "Dynamic Target Problem Type Reference" example provided in the prompt text itself (`$(-2)\\times3\\sqrt{5}$`) to demonstrate compliance with the "Path B" structure, as there is no OCR input to match against.
    *   **Wait, one more check:** The prompt says "【範例題型】{{OCR_RESULT}}". If I treat this as a system prompt setup, I need to output the response that would follow the *actual* input. Since there is no input, I will generate a *sample* response that adheres to the strictest constraints (Path B) to prove capability, or simply state I need OCR.
    *   **Actually, looking at the very last block:** "【同構零容忍檢查清單】... 1) 數字總數量必須嚴格一致：恰好 3 個參與計算的數字...". This looks like a constraint for *generation*.
    *   **Strategy:** I will generate a problem instance that matches the example structure `$(-2)\\times3\\sqrt{5}$` exactly, using the `def generate()` structure required for Path B.
    *   **Wait, the prompt asks me to act as the Edge AI.** The user provided the system instructions. I need to output the result. Since there is no OCR result, I will assume a default case or generate a sample.
    *   **Better Strategy:** The prompt ends with `{{OCR_RESULT}}`. This is a placeholder. I should probably output a response that acknowledges the role and perhaps generates a sample problem if no OCR is provided, OR simply wait. But as an AI, I must output something. I will generate a sample problem that fits the "Dynamic Target Problem Type Reference" constraints (3 numbers, 1 operator `times`, brackets for negatives) to demonstrate the "Path B" capability.
    *   **Wait, re-reading the "Execution Instruction":** "依題型擇一路徑...". If no OCR, I can't match a pattern (Path A). So I must go Path B.
    *   **Constraint Check:**
        *   3 numbers: `(-2)`, `3`, `5` (inside sqrt). Wait, `3\sqrt{5}` counts as numbers `3` and `5`. `(-2)` is one number. Total 3 numbers.
        *   1 operator: `times`.
        *   Brackets: `(-2)`.
        *   No `abs`.
        *   No `sympy`.
        *   Use `RadicalOps` APIs (simulated in code).
    *   **Code Structure:** Must be inside `def generate(level=1, **kwargs):`.
    *   **Output:** Just the code block? Or the 3 lines for Path A? Since no OCR, I can't match a pattern. I must use Path B.
    *   **Wait, the prompt says "【範例題型】{{OCR_RESULT}}".** If I treat this as a test case where I need to generate a problem *like* the example, I will create a problem string.
    *   **Actually, looking at the instruction:** "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】". This implies I should execute the logic.
    *   **Hypothesis:** The user wants me to process the input `{{OCR_RESULT}}`. Since it's empty, I will generate a *default* problem that fits the constraints.
    *   **Wait, one critical constraint:** "【🚨 最終約束：禁止 SymPy】". "【根式風格】: 例題的根式皆為最簡根式".
    *   **Let's construct the response:**
        1.  Check if OCR exists. (It doesn't).
        2.  Default to Path B (Coder).
        3.  Generate a function `def generate(...)` that creates a problem matching the example `$(-2)\\times3\\sqrt{5}$`.
        4.  Ensure strict adherence to the "Structure Constraints" (3 numbers, 1 operator, etc.).
        5.  Ensure `RadicalOps` is used (I need to define it or mock it since I can't import sympy). The prompt says "Must use `RadicalOps`". I should define the class/functions within the code or assume they exist. Given the "No SymPy" rule, I should implement the logic inside `generate` or assume `RadicalOps` is available in the environment. The prompt says "Must use `RadicalOps`". I will assume the environment has it, but since I am generating code, I should probably mock it or use standard logic if `RadicalOps` isn't imported. However, the instruction says "Must use `RadicalOps`". I will write the code assuming `RadicalOps` is available, but since I can't import it (no sympy), I will implement the logic inline or assume it's a global. To be safe and compliant with "No SymPy", I will implement the logic using `math` and `fractions` inside the function, but name the variables/functions to match `RadicalOps` expectations if possible, or just use the provided API names if they are expected to exist.
        *   *Correction:* The prompt says "Must use `RadicalOps`". It implies the library exists. I will