Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** K12 Math Algorithm Engineer / MathProject LiveShow Structure Homomorphic Output Engine (Qwen-8B-VL specialized).
    *   **Task:** Implement `def generate(level=1, **kwargs)` to generate radical simplification and arithmetic problems.
    *   **Constraints:**
        *   NO thinking process output.
        *   NO markdown fences (` ```python `).
        *   NO explanations or comments that violate the "no non-code content" rule (though internal code comments are usually okay, I need to be careful about the prompt's strictness on "directly output Python code"). The prompt says "Directly output Python code, no preamble/postscript". It also says "Strictly follow import rules", "Core Logic", etc.
        *   **Imports:** `import random`, `import math`, `from fractions import Fraction`. Do NOT use custom imports like `RadicalOps` (it's injected). Wait, the prompt says "System has automatically injected... directly call RadicalOps.xxx". So I must assume they exist in scope but not imported.
        *   **Logic:** Use integer operations for coefficients and radicands until formatting. Parse LaTeX is forbidden.
        *   **Level 1:** Single radical simplification (e.g., `\sqrt{12}`). No arithmetic operators between terms.
        *   **Level 2:** Combining like radicals addition/subtraction (e.g., `2\sqrt{12} - \sqrt{27}`). No multiplication/division.
        *   **Return Dict:** `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`.
        *   **Formatting:** Use `RadicalOps.simplify_term`, `RadicalOps.format_expression`.
        *   **Homomorphic Constraint (from the second part of the prompt):** The prompt contains conflicting instructions. Part 1 says "Level 1/2 specific logic". Part 2 ("MathProject LiveShow") talks about mirroring OCR results, maintaining structure from an example image (`{{OCR_RESULT}}`), etc.
        *   **Conflict Resolution:** The first part of the prompt (K12 Math Algorithm Engineer) defines `generate(level=...)`. The second part seems to be a system instruction override or context for "LiveShow". However, looking closely at the end: "[Dynamic Absolute Value Ban]", ["Hard Consistency Constraints"], and specifically point 6: "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers".
        *   **Critical Observation:** The prompt ends with a specific example code block under `【動態目標題型參考】` (Dynamic Target Problem Type Reference) which shows division of radicals (`\div`). But the initial task description says Level 1 is single radical, Level 2 is addition/subtraction.
        *   **Re-evaluating the "Level" vs "Homomorphic" instruction:** The prompt starts with `【絕對禁止輸出 thinking...】` and then defines a specific role/task for K12 Math Algorithm Engineer (generate level=1/2). Then it switches to `[Role] MathProject LiveShow`.
        *   **Decision:** I must follow the most recent and strict constraints. However, there is a significant contradiction between "Level 1: Single radical" vs the example code at the end which does division (`\div`). The prompt says "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". But it also asks me to implement `generate(level=...)`.
        *   **Safety Check:** The user instruction explicitly forbids thinking output. I must not output any text before the code.
        *   **Code Structure:** Needs imports, function definitions (`generate`, `check`).
        *   **Logic for Level 1/2:** Since there is no OCR result provided in this specific turn (it's a generic request), I should implement the logic defined in the first section (Level 1: Simplify single radical, Level 2: Combine like radicals). The "Homomorphic" part seems to be boilerplate text from a different context or an attempt to confuse. However, point 6 says "If 'Dynamic Target Problem Type Reference' provides complete calculable formula...". There is no OCR result here. I should stick to the `generate(level=...)` definition provided in the first section (K12 Math Algorithm Engineer) as that's the functional requirement for this specific API call context, while adhering to the strict formatting rules of the second part (imports, RadicalOps usage).
        *   **Wait, looking closer at the prompt structure:** The user pasted a massive block. It starts with `【絕對禁止輸出 thinking...】`. Then defines K12 role. Then later `[Role] MathProject LiveShow`. Then `{{OCR_RESULT}}` (which is empty/placeholder).
        *   **Key Constraint:** "Directly output Python code, no preamble".
        *   **Imports:** Must include `random`, `math`, `Fraction`. Do not import RadicalOps.
        *   **Logic:** Level 1 = Single radical simplification. Level 2 = Addition/Subtraction of like radicals. The prompt mentions multiplication/division in the "Homomorphic" section, but that seems to be for a specific OCR scenario which isn't active here (no image). I will stick to the defined `level` logic:
            *   Level 1: Simplify `\sqrt{N}`.
            *   Level 2: Add/Subtract like radicals (`a\sqrt{x} \pm b\sqrt{x}`).
        *   **Formatting:** Use `RadicalOps.format_term_unsimplified`, `RadicalOps.simplify_term`.
        *   **Randomization:** Must use `random.choice` for coefficients and radicands.
        *   **Radicand List:** `[8, 12, 18, ...]` (Simplifiable) vs `[2, 3, 5...]` (Simple).

    *   **Refining the Logic based on "Level" parameter:**
        *   If `level == 1`: Generate one term. Simplify it internally to get answer. Display unsimplified for question.
        *   If `level == 2`: Generate multiple terms with same radicand (after simplification). Add/Subtract coefficients.

    *   **Handling the "Homomorphic" vs "Level" conflict:** The prompt asks me to implement `def generate(level=1, ...)` based on Level definitions in section 1. Section 2 talks about mirroring OCR which isn't present. I will prioritize the functional definition of `generate` (Section 1) but use the strict coding standards from Section 3/4 (Imports, RadicalOps usage).
    *   **Wait, one more check:** The prompt ends with "【動態目標題型參考】" showing a division example. But it also says "If 'Dynamic Target Problem Type Reference' provides complete calculable formula... prohibit re-randomizing numbers". Since there is no actual OCR result provided in the input (it's just text), I cannot mirror an image that doesn't exist. I must generate new problems based on `level`.
    *   **Wait, actually:** The prompt says "【任務】實作 `def generate(level=1, **kwargs)`... 依照 level 選擇難度". This is the primary instruction. The later text about OCR seems to be context from a different session or template that got appended. I should follow the explicit task: Level 1 (Simplify), Level 2 (Combine).
    *   **Wait, looking at the very end:** "【硬性一致性約束】... 6) ...禁止重新隨機抽數、禁止改寫為其他題目。" This contradicts `random.choice`. However, since there is no OCR result to mirror, I must generate. The instruction says "If 'Dynamic Target Problem Type Reference' provides complete calculable formula". It doesn't provide one here (it's a placeholder). So I will randomize as per the Level definition.
    *   **Wait, actually:** There is a specific constraint: `question_text` for Level 1 should be `\sqrt{...}` simplified? No, "題目顯示：化簡 $\sqrt{...}$". The answer is the simplified form.
    *   **Level 2:** Multiple terms like radicals addition/subtraction.

    *   **Code Plan:**
        1. Imports: `random`, `math`, `Fraction`. (Do not import RadicalOps).
        2. Define lists for radicands (`simplifiable` and `simple`).
        3. Implement `generate`:
            - Check level.
            - If Level 1: Pick one simplifiable number, coeff=1 usually or random small int? Prompt says "Level 1... only single term". Let's make it simple `\sqrt{N}` where N is from list. Answer = simplified form.
            - If Level 2: Generate multiple terms with same radicand (after simplification). Sum coefficients. Display unsimplified sum/subtract expression.
        4. Implement `check`.
        5. Ensure no markdown fences around the code block if possible, but usually Python output is expected in a code block for readability unless strictly "raw text". The prompt says "Directly output Python code... No preamble/postscript". Usually this means raw text or inside a fence? Standard practice for these constraints is often just the code. I will use standard markdown fencing ` ```python ` because otherwise it's hard to read, but wait: "禁止 markdown fence"