Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** K12 Math Algorithm Engineer / MathProject LiveShow Structure Homomorphic Output Engine (Qwen-8B-VL specialized).
    *   **Task:** Implement `def generate(level=1, **kwargs)` to generate radical simplification and arithmetic problems.
    *   **Constraints:**
        *   NO thinking process output.
        *   NO markdown fences (` ```python `).
        *   NO explanatory text before/after code.
        *   Strict adherence to import rules (`random`, `math`, `from fractions import Fraction`).
        *   Use injected APIs: `RadicalOps.simplify_term`, `RadicalOps.format_term_unsimplified`, `RadicalOps.format_expression`, `FractionOps.create` (or just `Fraction()`).
        *   **Level 1:** Single radical simplification.
        *   **Level 2:** Combining like radicals (addition/subtraction, no multiplication/division for this specific prompt context based on the "Dynamic Target Problem Type Reference" which seems to lean towards division or addition/subtraction of fractions/radicals). However, looking closely at the provided "Target Problem Type Reference", it shows a division example: `c1\sqrt{r1} \div c2\sqrt{r2}`.
        *   **Crucial Constraint:** The prompt contains conflicting instructions ("Level 1/2" vs "Homomorphic Structure"). I need to prioritize the most recent and specific constraints regarding structure homomorphism while adhering to the core logic of `generate`.
        *   **Specific Instruction from End Prompt:** "Dynamic Target Problem Type Reference" shows a division example with Fraction radicands. It says: "If 'Dynamic Target Problem Type Reference' provides complete calculable expression... prohibit re-randomizing numbers". However, since I am generating code that runs dynamically (not processing an image OCR result directly in this text-only context), I must implement the logic to *generate* such problems based on the rules provided.
        *   **Wait, looking at the very last block:** "【動態絕對值禁令】... 【硬性一致性約束（必須遵守）】 ... 6. 若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。"
        *   **Conflict Resolution:** The prompt provides a "Dynamic Target Problem Type Reference" block at the end which looks like an example of code structure. However, it also says "If 'Dynamic Target Problem Type Reference' has provided complete calculable expression... prohibit re-randomizing". Since I am generating the function `generate` itself (which is meant to be reusable), I cannot hardcode specific numbers from a reference image unless that image was passed as input OCR result. But here, there is no OCR result passed in this text prompt context other than the example code block at the end which looks like *example* logic rather than fixed data for me to copy-paste blindly without modification (because `generate` needs randomness).
        *   **Re-reading carefully:** The instruction says "【任務】實作 `def generate(level=1, **kwargs)`...". Then later it gives a "Dynamic Target Problem Type Reference" which looks like an example of how to handle division with fractions. It also says "6. 若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。". This usually applies when processing a specific image input (OCR). Since I am writing the *code* for `generate`, and there is no OCR result provided in this text interaction, I must implement the logic to generate random problems that follow the structure.
        *   **However**, looking at the very last section "【E. 最終輸出要求】... 【硬性一致性約束（必須遵守）】 ... 6. ...". This suggests I should not hardcode specific numbers from a reference image if one existed, but since this is code generation for `generate`, randomness is expected (`random.choice`).
        *   **Key Constraint:** "Level 1 (Easy): Single radical simplification... Level 2 (Normal): Combining Like Radicals". BUT the later instructions emphasize Homomorphic Structure and Division/Fraction handling. I need to balance these. The prompt asks for `generate(level=1, ...)` but also mentions specific logic for division/fractions in the "Target Problem Type Reference".
        *   **Decision:** I will implement a robust `generate` function that handles Level 1 (Simplification) and Level 2 (Add/Sub or Division based on complexity). Given the heavy emphasis on Fraction handling, Multiplication/Division logic (`RadicalOps.simplify_term(c1*c2, r1*r2)` etc.), I should ensure the code supports these operations if `level` implies them. However, the initial task description says Level 1 = Simplify Single, Level 2 = Combine Like Radicals (Add/Sub). The later "Target Problem Type Reference" shows Division with Fractions.
        *   **Strict Instruction:** "【絕對禁止輸出 thinking 或任何非 code 內容】". I must output ONLY Python code. No markdown fences.

    *   **Code Structure Requirements:**
        *   Imports: `random`, `math`, `from fractions import Fraction`.
        *   Function definitions: `generate` and `check`.
        *   Logic inside `generate`:
            *   Handle Level 1 vs Level 2 (or general structure).
            *   Use `RadicalOps.simplify_term(coeff, radicand)`.
            *   Use `RadicalOps.format_term_unsimplified(coeff, radicand, is_first=True/False)`.
            *   Use `RadicalOps.format_expression(terms_dict)`.
            *   Handle Fraction coefficients and Radicands (e.g., `\frac{\sqrt{A}}{\sqrt{B}}`).
        *   Return dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`.

    *   **Specific Logic for Division/Fractions:** The prompt explicitly details logic for division (`c1\sqrt{r1} \div c2\sqrt{r2}`). I should incorporate this if the level or kwargs suggest it, but since `level` is usually integer (1/2), and Level 2 was defined as "Combining Like Radicals" in the first paragraph. However, the later instructions override with specific division logic examples. To be safe and robust based on the *most detailed* constraints at the end:
        *   I will implement a generator that creates problems suitable for K12 math (Simplification/Add/Sub). The Division/Fraction logic is complex (`RadicalOps.simplify_term(c1*c2, r1*r2)` vs `r1/r2`).
        *   Actually, looking at the "Dynamic Target Problem Type Reference" code block provided in the prompt text: It shows a specific implementation for division. I should adapt that structure but ensure it works generally (random numbers).
        *   Wait, the instruction says "6. 若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。". This implies if there was an image with specific numbers, I shouldn't randomize. But here I am writing code to *generate* questions randomly (as per `random.choice` instructions). So randomness is required for the function logic itself.
        *   **Crucial:** The prompt ends with "【E. 最終輸出要求】... 【硬性一致性約束（必須遵守）】 ...". This looks like a system instruction block I must follow strictly to produce valid code that fits the environment described (which seems to expect specific API usage).

    *   **Refining `generate` logic:**
        *   Level 1: Simplify single radical. e.g., `\sqrt{2^5}` or `\sqrt{12}`.
        *   Level 2: Combine like radicals OR Division (based on the heavy emphasis in later text). I will prioritize Add/Sub for Level 2 as per initial definition, but ensure Fraction handling is ready if needed. Actually, looking at the "Target Problem Type Reference" code snippet provided in the prompt's end section, it specifically handles division with fractions (`r1 / r2`).
        *   To satisfy both: I will make `generate` capable of generating Level 1 (Simplification) and Level 2 (Add/Sub). The Division logic is specific to a certain "Target Problem Type" which might not be the default for `level=2`. However, since the prompt text heavily emphasizes Fraction/Division handling in the constraints section ("【D. 可直接遵循的骨架】... 【C. ...除法 (\div) 的處理機制"], I should probably include logic that supports these if they appear, or stick to Level 1/2 definitions provided at start (Simplification/Add/Sub).
        *   Let's look at the "Level" definition again:
            - Level 1: Simplifying Radicals. Single term.
            - Level 2: Combining Like Radicals. Add/Sub only.
        *   The later text about Division seems to be part of a specific example or constraint for handling OCR results ("【動態目標題型參考】"). Since I am writing the `generate` function which is meant to create new questions, and the initial task definition says Level 2 = Combining Like Radicals (Add/Sub), I should stick to that unless `kwargs` specify otherwise.