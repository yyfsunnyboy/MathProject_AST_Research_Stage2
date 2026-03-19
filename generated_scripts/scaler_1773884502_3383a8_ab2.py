Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** Edge AI — 根式四則運算 (Radical Arithmetic).
    *   **Task:** Process an input example ({{OCR_RESULT}}) or generate a problem based on specific constraints.
    *   **Constraints:**
        *   **NO SymPy:** Strictly forbidden. Use `math`, `fractions`, and custom `RadicalOps` logic.
        *   **RadicalOps:** Must use specific APIs (`simplify`, `add_term`, `mul_terms`, `div_terms`, `format_term`, `format_expression`).
        *   **Pattern Matching:** Use the provided `Pattern Catalogue` (p0-p7) if applicable.
        *   **Output Format:**
            *   If Pattern Matched (Path A): Output 3 lines (`pattern_id`, `difficulty`, `term_count`).
            *   If No Pattern Match (Path B): Output a Python function `def generate(level=1, **kwargs):` containing the logic.
            *   **Strict Structure:** No code outside `def generate(...)`. No `return` outside.
            *   **LaTeX:** Use `\\times`, `\\sqrt`, etc. No `1\sqrt{x}`.
            *   **Input:** The prompt ends with `{{OCR_RESULT}}`. Since this is a simulation, I need to check if there's an actual OCR result provided. Looking at the prompt, `{{OCR_RESULT}}` is a placeholder. However, the instruction says "【範例題型】{{OCR_RESULT}}". Usually, in this context, I need to generate a problem *or* process a specific input. Since no specific OCR result is provided in the text (it's a template), I should assume the role of generating a problem that fits the constraints, OR if the user expects me to process a specific input that wasn't pasted, I need to handle the "generate" task based on the constraints provided in the prompt itself (which looks like a system instruction for generating problems).
            *   **Wait, looking closer:** The prompt ends with `{{OCR_RESULT}}`. This implies I should treat the *current interaction* as if I am receiving an OCR result. However, since I am an AI text model, I don't have an OCR result attached unless the user provides it.
            *   **Correction:** The prompt structure suggests I am *configuring* the AI or *responding* to a system prompt. But the instruction says "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】". It asks me to choose a path.
            *   **Crucial Decision:** Since there is no actual OCR result provided in the input (it's a placeholder `{{OCR_RESULT}}`), I must assume the task is to **generate a problem** that adheres to the strict constraints (Path B) OR match a pattern if I were given a specific expression.
            *   **However**, looking at the very end: "【同構零容忍檢查清單】... 5) 必須保留中括號結構 []...". This looks like a specific constraint for the *generated code* or the *problem structure*.
            *   **Wait, re-reading the "Input"**: The prompt ends with `{{OCR_RESULT}}`. In a real deployment, this would be replaced. Here, I need to act as the system. If I treat `{{OCR_RESULT}}` as "None" or "Empty", I should probably generate a sample problem that fits the "Path B" (Coder) requirements because there's no specific expression to match against the Catalogue.
            *   **BUT**, the instruction says "【範例題型】{{OCR_RESULT}}". If I am to simulate the response, I should probably generate a valid problem instance that follows the "Path B" rules (since no specific expression is given to match a pattern).
            *   **Actually**, looking at the "【🚨 最終約束：禁止 SymPy】" section, it says "題目中有 `\times`，代碼就必須用 `\\times`".
            *   **Key Constraint:** "【🚀 執行指令：Hybrid 雙軌模式 (AB3 專用)】".
            *   **Decision:** Since I cannot see an OCR result, I will assume the role of generating a problem instance that fits the "Path B" (Coder) requirements, as there is no specific expression to match a pattern. I need to create a `generate` function that creates a problem.
            *   **Wait, one more check:** The prompt says "【範例題型】{{OCR_RESULT}}". If this is a system prompt setup, I should acknowledge the constraints. But usually, when a user sends this, they expect me to *act* as the Edge AI.
            *   **Hypothesis:** The user wants me to generate a problem based on the constraints, OR they expect me to process a specific string if they had provided one. Since `{{OCR_RESULT}}` is a placeholder, I will generate a sample problem using Path B (Coder) to demonstrate compliance with the strict formatting rules (Path B requires `def generate(...)`).
            *   **Wait, looking at the "Path A" vs "Path B"**:
                *   Path A: If pattern matched. Output 3 lines.
                *   Path B: If not matched. Output `def generate(...)`.
            *   Since I don't have an input expression to match, I must default to **Path B** (Coder) to generate a problem.
            *   **Constraint Check:**
                *   No SymPy.
                *   Use `RadicalOps` (I need to define it or assume it exists? The prompt says "RadicalOps（根式拓樸，必須透過此層完成化簡與排版）". I should probably implement the logic inside `generate` or assume the environment has it. The example code shows `RadicalOps.format_term_unsimplified`. I will assume the class exists or mock it minimally within the function if needed, but the prompt implies I should use it. To be safe and self-contained, I will implement the necessary logic inside `generate` or assume the imports are available. The prompt example shows `import random` inside. I should follow that style.)
                *   **Strict Structure:** `def generate(level=1, **kwargs):` wrapper.
                *   **No code outside.**
                *   **LaTeX:** `\\times`, `\\sqrt`.
                *   **Specific Constraint:** "題目中有 `\times`，代碼就必須用 `\\times`".
                *   **Specific Constraint:** "數字總數量必須嚴格一致... 恰好 3 個參與計算的數字".
                *   **Specific Constraint:** "二元運算子總數必須嚴格一致：恰好 1 個運算子".
                *   **Specific Constraint:** "運算子順序必須完全一致：times".
                *   **Specific Constraint:** "必須保留中括號結構 []".
                *   **Specific Constraint:** "第 1 個中括號內：數字=1，運算子=0".
                *   **Specific Constraint:** "禁止新增絕對值符號".
                *   **Specific Constraint:** "負數必須以括號形式表達".
                *   **Specific Constraint:** "禁止新增未出現的運算子".

            *   **Wait, the "OCR_RESULT" is empty.** If I treat this as a "Generate Problem" task, I need to create a problem that fits the "Path B" description.
            *   **However**, the prompt ends with `{{OCR_RESULT}}`. If I am to respond to this prompt, I should probably output the `generate` function that creates a problem.
            *   **Wait, is there a specific input?** No.
            *   **Okay, I will generate a problem instance.**
            *   **Wait, the constraint "題目中有 `\times`，代碼就必須用 `\\times`"**: This implies the *output question text* must use LaTeX `\times`.
            *   **Constraint "數字總數量必須嚴格一致：恰好 3 個參與計算的數字"**: This is very specific. It suggests a structure like `A * B`.
            *   **Constraint "必須保留中括號結構 []"**: This is weird. Usually Python uses `[]` for lists. Does it mean the *question text* must have `[]`? Or the code? "5) 必須保留中括號結構 []，不得改成一般括號或移除。5.1) 中括號區塊數量必須一致：1 5.2) 第 1 個中括號內：數字=1，運算子=0". This sounds like a constraint on the *question text representation* or the *data structure* passed to the renderer.
            *   **Actually**, looking at the example code: `t2 = f"({t2})"`. This uses `()`. The constraint says `[]`. This is a contradiction or a specific requirement for the *output format* of the question string.
            *   **Let's re-read carefully:** "5) 必須保留中括號結構 []，不得改成一般括號或移除。5.1) 中括號區塊數量必須一致：1 5.2) 第 1 個中括號內：數字=1，運算子