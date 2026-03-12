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