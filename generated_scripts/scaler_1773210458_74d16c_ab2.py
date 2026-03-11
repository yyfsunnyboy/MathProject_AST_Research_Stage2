Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** K12 Math Algorithm Engineer / MathProject LiveShow Structure Isomorphic Question Engine (Qwen-8B-VL Dedicated).
    *   **Task:** Generate Python code for a math question generator based on strict isomorphism rules provided in the prompt.
    *   **Input Data:** A specific example problem structure: `$(-8 )×6＋｜(-5 )×10-1｜$`.
    *   **Constraints:**
        1.  Import `random`, `math` (optional), `fractions.Fraction` (if needed). Use injected `IntegerOps.xxx`.
        2.  Strictly follow the isomorphism rules: same number count, operator order/types, bracket levels, absolute value structure.
        3.  Output *only* Python code (no markdown fences like ```python), no explanations, no JSON output in the final response block itself (though the prompt asks for "Python code ONLY", usually this means inside a code block or raw text). The instruction says "只輸出 Python 原始碼" and "不要輸出任何額外文字".
        4.  Specific Example: `$(-8 )×6＋｜(-5 )×10-1｜$`. This is the template to mimic strictly (isomorphic generation, but since it provides specific numbers in the example description under "Dynamic Target Question Type Reference", I need to check if I should randomize or keep them. The prompt says: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" (If the dynamic target question type reference provides a complete computable expression with specific numbers, do not randomize new numbers, do not rewrite as other questions).
        5.  Wait, looking closely at Section D3 and "Dynamic Target Question Type Reference": The prompt says "禁止重新隨機抽數、禁止改寫為其他題目" (Do not re-randomize numbers, do not rewrite as other questions) *IF* the reference provides specific numbers. However, usually in these generation tasks, `generate` implies randomness unless specified otherwise to create a new instance of that type. But Section D3 says "依變數順序與原始常數正負號，給變數取值範圍" (Assign variable ranges based on original constant signs).
        6.  Let's re-read the specific instruction under "【動態目標題型參考】": `$(-8 )×6＋｜(-5 )×10-1｜$`. It says: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" (If the dynamic target question type reference provides a complete computable expression with specific numbers, do not re-randomize numbers...).
        7.  However, looking at Section D3: "依變數順序與原始常數正負號，給變數取值範圍... v1 ... [1, 100] / [-100, -1]". This implies randomization *within* the structure defined by the original numbers' signs.
        8.  Actually, looking at Section G: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" This is a strong constraint in section F/G context (Section D says generate algorithm steps).
        9.  Wait, there's a conflict between "Generate Algorithm Steps" which implies randomization for variety (`IntegerOps.random_nonzero`), and the specific instruction at the end saying if numbers are provided don't re-randomize. Usually, in these prompt engineering tasks, the last section often overrides or specifies the immediate task context. However, `generate(level=1)` usually expects a function that *can* generate questions. If I hardcode `-8` and `-5`, it's not really generating. But if I follow "Do not re-randomize numbers", then the code should probably use those specific numbers as fixed constants or at least ensure the structure matches exactly with randomization only on signs/ranges defined by D3?
        10. Let's look closer: The prompt says "【動態目標題型參考】... $(-8 )×6＋｜(-5 )×10-1｜$". Then under Section F/G it says "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" This suggests I should treat the provided numbers as fixed constants for this specific generation run, OR use them to define the structure and then randomize *within* that structure (e.g. keep signs but change magnitude).
        11. However, Section D3 says "依變數順序與原始常數正負號，給變數取值範圍". This implies I should treat `-8` as `v1`, `6` as `v2`, etc., and generate new numbers based on their signs (e.g. v1 is negative in the example, so range [-100, -1]).
        12. But Section F/G says "Do not re-randomize". This usually means for *this specific output*, use the provided numbers exactly as they are to ensure correctness and strict adherence to the template if it's a test case generation task. However, `generate` functions typically randomize. Let's look at the instruction again: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" This is under Section F/G (Final Output Requirements). It seems to be a constraint for *this specific execution*.
        13. Wait, looking at the code snippet provided in the prompt (`/no(numerator) % abs(denominator)...`), it looks like part of an existing generator logic that I need to complete or adapt? No, the user asks me to output Python code based on these constraints. The input text contains a partial function `generate`.
        14. Actually, looking at the very beginning: `/no(numerator) % abs(denominator)...` This looks like part of an existing snippet provided by the user as context or instruction? No, it's inside the prompt block under "【動態目標題型參考】". Wait, no, that code snippet is likely *part* of the expected output structure I need to follow (the `generate` function logic).
        15. Okay, let's synthesize:
            - Output ONLY Python code. No markdown blocks like ```python. Just raw text or a single block? "不要輸出任何額外文字" + "只輸出 Python 原始碼". Usually means no markdown fences if possible to avoid parsing issues in some systems, but standard practice for LLMs is often ` ```python `. However, the instruction says "Do not output markdown." So I should write raw text that looks like code.
            - Wait, looking at Section G: "不要輸出 markdown". This means no triple backticks. Just plain text starting with imports and functions.
            - The prompt asks for a `generate` function (and optionally `check`).
            - Constraints on the math problem structure based on `$(-8 )×6＋｜(-5 )×10-1｜$`.
                - Operators: `times`, `plus`, `abs(times, minus)`. Wait. The example is $(-8)\times 6 + |(-5)\times 10 - 1|$.
                - Structure inside abs: `A * B - C`. (3 numbers).
                - Outside abs: `-8` and `6` are multiplied? No, the expression is `v1 * v2 + |v3 * v4 - v5|`. Wait. The example text says `$(-8 )×6＋｜(-5 )×10-1｜$`.
                    - Term 1: $(-8) \times 6$. (Numbers: -8, 6). Operator: $\times$.
                    - Plus sign `+` is outside the abs.
                    - Abs content: $| (-5) \times 10 - 1 |$. Numbers inside: -5, 10, 1. Operators inside: $\times$, `-`.
                - Total numbers in example: -8, 6, -5, 10, 1 (Total 5).
                - Operator sequence outside abs: `*`, then `+`? No, the structure is `(A * B) + |C * D - E|`. Wait. The text says `$(-8 )×6＋｜(-5 )×10-1｜$`. This parses as $((-8)\times 6) + (|-5 \times 10 - 1|)$.
                - Operators: `*`, `+` (between terms), inside abs: `*`, `-`. Total operators: `*, *, -, +`. Wait, the prompt says "二元運算子總數必須一致：4". Let's count.
                    1. $\times$ between $(-8)$ and $6$.
                    2. $+$ between term1 and abs_term.
                    3. $\times$ inside abs (between -5 and 10).
                    4. $-$ inside abs (between result of above and 1).
                - Total operators: 4. Correct.