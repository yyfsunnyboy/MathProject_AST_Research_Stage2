Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** Edge AI — 根式四則運算 (Radical Arithmetic).
    *   **Task:** Process a math problem (implied by `{{OCR_RESULT}}` which is empty/placeholder in the prompt, but I need to generate a response based on the constraints).
    *   **Constraints:**
        *   **NO SymPy:** Strictly forbidden.
        *   **RadicalOps:** Must use `RadicalOps` APIs for simplification, formatting, etc.
        *   **Pattern Matching:** Use the provided `Pattern Catalogue` (p0-p7) if applicable.
        *   **Hybrid Mode:**
            *   **Path A (Catalogue Hit):** Output only 3 lines of variables (`pattern_id`, `difficulty`, `term_count`). No code.
            *   **Path B (Coder):** If not in catalogue, output a `def generate(...)` function.
        *   **Formatting:**
            *   LaTeX formatting rules (no `1\sqrt{x}`, handle negative signs correctly).
            *   Python code structure must be inside `def generate(...)`.
            *   No text outside Python blocks (except the 3-line output for Path A).
            *   Specific structure for Path B (imports, variable generation, formatting).
        *   **Specific Warning:** "題目中有 `\times`，代碼就必須用 `\\times`". "禁止直接拼接".
        *   **Input:** `{{OCR_RESULT}}` is empty in the prompt provided. I need to assume a scenario or generate a sample based on the constraints. However, looking at the instruction "【範例題型】{{OCR_RESULT}}", it seems I need to handle the input provided. Since there is no actual OCR result, I should probably generate a *sample* problem that fits the constraints (Path B) or acknowledge the empty input.
        *   **Wait, looking closer at the prompt:** The prompt ends with `=== SKILL_END_PROMPT ===`. This suggests I am the model receiving this system instruction. The user input is likely the `{{OCR_RESULT}}` part which is currently empty or I need to simulate a response based on the *instruction* itself.
        *   **Actually, looking at the very last part:** `【同構零容忍檢查清單】... 5) 必須保留中括號結構 []...`. This looks like a specific constraint for a generated problem.
        *   **Crucial Decision:** Since `{{OCR_RESULT}}` is empty, I cannot match a specific pattern (Path A). I must fall back to **Path B (Coder)** to generate a problem that adheres to the strict structural constraints mentioned in the "【同構零容忍檢查清單】" (Isomorphism Zero Tolerance Check List).
        *   **Wait, re-reading the "Execution Instruction":** "依題型擇一路徑...". Since I don't have a specific OCR result, I should probably generate a *valid* example that follows the Path B rules strictly, as if I were generating a problem for a user.
        *   **However, the prompt says:** `[範例題型] {{OCR_RESULT}}`. Usually, in this context, if the input is empty, I should perhaps ask for input or generate a default. But the instruction says "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】".
        *   **Hypothesis:** The user wants me to act as the system. If there's no OCR result, I might need to generate a *template* or a *sample* that satisfies the "Path B" requirements because I can't match a pattern (Path A).
        *   **BUT**, the prompt ends with specific constraints about "Isomorphism Zero Tolerance Check List" (e.g., exactly 3 numbers, 1 operator, etc.). This looks like a specific test case I need to pass.
        *   **Wait, one more thing:** The prompt says "【範例題型】{{OCR_RESULT}}". If this is a system prompt setup, I should acknowledge the role. But usually, I need to output the result for the *current* input. Since the input is effectively empty/placeholder, I will generate a **Path B** response that creates a valid math problem following the strict structural constraints (3 numbers, 1 operator, etc.) to demonstrate compliance.
        *   **Actually, looking at the very last block:** `【同構零容忍檢查清單】...`. This implies I need to generate a problem that fits this specific structure (e.g., `(-2)×3√5`).
        *   **Decision:** I will generate a Path B response that creates a problem matching the "Isomorphism Zero Tolerance Check List" (3 numbers, 1 operator `×`, 1 bracket structure). I will use `RadicalOps` (simulated logic since I can't import it, but I must write code that *uses* it). Wait, the instruction says "嚴禁 sympy... 必須使用 math, fractions 與 RadicalOps". Since I am an LLM, I cannot actually import `RadicalOps`. I must *simulate* the usage or write the code structure that *would* use it. The instruction says "若進入路徑 B，代碼**必須且只能**包在 `def generate(level=1, **kwargs):` 內".
        *   **Correction:** I am the AI. I need to output the *response*. The response should be the code block for Path B if I can't match a pattern. Since I don't have OCR input, I will generate a sample problem that fits the constraints.
        *   **Wait, the prompt says:** `[Role] MathProject LiveShow — Edge AI...`. This is a system instruction. I need to acknowledge the role and wait for input? Or generate a response based on the empty `{{OCR_RESULT}}`?
        *   **Standard Behavior for System Prompts:** If the user sends a system prompt, I should acknowledge readiness or process the first task. Since there is no task input (`{{OCR_RESULT}}` is empty), I should probably generate a **sample** that proves I understand the constraints, specifically the Path B constraints.
        *   **Wait, looking at the "Execution Instruction":** "依題型擇一路徑...". If I treat the empty input as "No Pattern Match", I go to Path B.
        *   **Constraint Check:**
            *   No SymPy.
            *   Path B: `def generate(...)` only.
            *   No text outside Python block (for Path B).
            *   Structure: 3 numbers, 1 operator (`×`), 1 bracket structure `[]`.
            *   Negative numbers in brackets `(-7)`.
            *   LaTeX formatting `\\times`.
            *   Use `RadicalOps.format_term_unsimplified`.
        *   **Wait, one critical constraint:** "禁止在 Python 區塊外寫任何文字解釋". (No text explanation outside Python block).
        *   **So I must output ONLY the Python code block.**
        *   **Wait, Path A vs Path B:** Since I have no OCR result, I cannot match a pattern (Path A). I must use Path B.
        *   **Wait, the "Isomorphism Zero Tolerance Check List"**:
            1.  3 numbers.
            2.  1 operator.
            3.  Operator order: `times`.
            4.  Bracket structure `[]` (1 bracket).
            5.  Inside bracket: 1 number, 0 operators.
            6.  No `abs()`.
            7.  Negative numbers in `(-7)`.
            8.  No new operators.
        *   **Example:** `(-2)×3√5`.
        *   **My Task:** Generate a problem that fits this.
        *   **Wait, the prompt says:** `[範例題型] {{OCR_RESULT}}`. If this is a test, I should probably output the code for a problem that matches the constraints.
        *   **Wait, I need to check if I should output the 3 lines (Path A) or the Code (Path B).** Since I don't have OCR, I can't match a pattern. So Path B.
        *   **Wait, the instruction says:** "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】".
        *   **Okay, I will generate a Path B response.**
        *   **Wait, I need to make sure I don't violate "No text outside Python block".**
        *   **Wait, I need to check the "RadicalOps" API.** Since I can't actually import it, I will write the code assuming it exists (as per the instruction "必須使用... RadicalOps").
        *   **Wait, the instruction says:** "【🚨 最終約束：禁止 SymPy】... 3. 嚴禁在 Python 區塊外寫任何文字解釋。"
        *   **So I will output ONLY the Python code.**
        *   **Wait, I need to make sure the generated problem matches the "Isomorphism Zero Tolerance Check List" at the end.**
        *   **Checklist:**
            1.  3 numbers.
            2.  1