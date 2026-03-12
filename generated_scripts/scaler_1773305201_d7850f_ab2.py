Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** K12 Math Algorithm Engineer / MathProject LiveShow Structure Homomorphic Output Engine (Qwen-8B-VL specialized).
    *   **Task:** Implement `def generate(level=1, **kwargs)` to generate radical simplification and arithmetic problems.
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