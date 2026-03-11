Thinking Process:

1.  **Analyze the Request:**
    *   **Role:** K12 Math Algorithm Engineer / MathProject LiveShow Isomorphic Question Engine (Qwen-8B-VL specialized).
    *   **Input:** A specific target question structure provided in `【動態目標題型參考】`: `$(-8 )×6＋｜(-5 )×10-1｜$`.
    *   **Constraints:**
        *   Strictly follow import rules (`random`, `math`, `fractions`), forbid `IntegerOps` redefinition.
        *   Isomorphic structure: Must match the target question's complexity, operator count, bracket levels, absolute value blocks exactly.
        *   Consistency between calculation string and display string (no A vs B mismatch).
        *   Output must be Python code ONLY (no markdown fences, no explanations).
        *   Use `IntegerOps.fmt_num`, `IntegerOps.random_nonzero`, `IntegerOps.safe_eval`.
        *   Handle division carefully (ensure divisibility before returning answer).
        *   Target Question: `$(-8 )×6＋｜(-5 )×10-1｜$`
            *   Operators: `times`, `plus`, `minus` inside absolute value. Wait, looking closely at the target string provided in the prompt's example section vs the "Dynamic Target" section.
            *   Dynamic Target Section says: `$(-8 )×6＋｜(-5 )×10-1｜$`.
            *   Structure Analysis of Target: `(-8) × 6 + | (-5) × 10 - 1 |`
                *   Operators: `*`, `+`, `|...|`, `-`. Inside abs: `*`, `-`. Outside abs before plus: `*`. Wait, let's parse carefully.
                *   Expression: $(-8 ) \times 6 + | (-5) \times 10 - 1 |$
                *   Operators present in target text provided in prompt example section (Step D7): "計算 $" + math_str + "$".
                *   Target Text from Dynamic Section: `$(-8 )×6＋｜(-5 )×10-1｜$`
                *   Let's count operators and numbers based on the specific constraint list at the end.
                *   Constraint 2.1) Operators order must be consistent: times -> plus -> times -> minus (Wait, looking at `$(-8 )×6＋｜(-5 )×10-1｜$`):
                    *   Term 1: `(-8)` [Num] `×` [Op] `6` [Num]. Op: Times.
                    *   Term 2: `+` [Op] (Abs Block). Inside Abs: `(-5)` [Num] `×` [Op] `10` [Num] `-` [Op] `1` [Num]. Ops inside abs: Times, Minus. Op outside: Plus.
                    *   Total Operators in target string provided: `×`, `+`, `|...|`, `×`, `-`. (Note: The prompt says "times -> plus -> times -> minus" as an example constraint for a specific structure).
                *   Constraint 2) Binary operator count must be consistent. Target has 4 binary operators (`*`, `+`, `*`, `-`). Wait, the absolute value bars are not binary operators in Python sense usually, but structural delimiters. The prompt says "Binary Operator Count". Usually means + - * /.
                *   Constraint 3) No new brackets []. (Target uses () and |).
                *   Constraint 4) Must preserve Absolute Value symbols `|`.
                *   Constraint 5) Negative numbers must be in parentheses form `$(-7)$`.
                *   Constraint 6) If Dynamic Target provides complete formula, do NOT randomize. Do not rewrite to other questions. **CRITICAL**: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" (If the dynamic target question reference provides a complete calculable formula with specific numbers, prohibit re-randomizing numbers and prohibiting rewriting to other questions.)
                *   **Wait**, there is a conflict in constraints. Section D says "Step D3: Give variable value ranges...". But Constraint G/6 says "If Dynamic Target Question Reference provides complete formula... prohibit randomization". The prompt ends with `【動態目標題型參考】$(-8 )×6＋｜(-5 )×10-1｜$`. This looks like a specific instance.
                *   However, the function signature is `generate(level=1, **kwargs)`. Usually, this implies generating new questions based on templates or structures. But Constraint G/7 says "Must preserve original question's operation skeleton...". And G/6 says if target provides complete formula with numbers, don't randomize.
                *   Let's look at the instruction: `【動態目標題型參考】$(-8 )×6＋｜(-5 )×10-1｜$`. This is likely a template or an example of what to mimic. But Constraint G/6 says "If... provides complete formula with specific numbers, prohibit re-randomizing".
                *   However, the function `generate` implies generation. If I just return this exact string every time, it's not really generating K12 math problems usually (which want new instances). But strict adherence to Constraint G/6 suggests using these numbers if provided as "Target Reference".
                *   Let's re-read carefully: "【動態目標題型參考】$(-8 )×6＋｜(-5 )×10-1｜$" is listed under `G. 最終輸出要求`. It seems to be the specific target structure I must mimic or use if it counts as a template.
                *   Actually, usually in these prompts, the "Dynamic Target" is the example of what kind of question to generate (structure-wise), OR it's the exact string to output. Given Constraint G/6 ("If... provides complete formula with specific numbers"), I should probably use this structure but maybe replace constants if `generate` implies generation?
                *   Wait, looking at Section D "Step D1: Read {{OCR_RESULT}}". But there is no OCR result provided in the input text. The only math string provided is `$(-8 )×6＋｜(-5 )×10-1｜$`.
                *   If I treat this as a template where numbers are constants to be replaced, Constraint G/6 says "If... provides complete formula with specific numbers". This implies if the input IS that string, don't change it. But `generate` function usually expects new questions.
                *   Let's look at the instruction again: "【動態目標題型參考】$(-8 )×6＋｜(-5 )×10-1｜$" is under `G`. It seems to be a specific constraint for this session.
                *   However, standard behavior for `generate` functions in these contexts (K12 Math) is usually: "Generate new questions based on the structure". But Constraint G/6 says "If... provides complete formula with specific numbers, prohibit re-randomizing". This suggests I should use the provided string as a template where variables might be placeholders? No, it has `-8`, `6`, `-5`, `10`, `1`. These are constants.
                *   If I must not randomize, then the question is fixed. But that makes `generate` useless for testing different numbers.
                *   Let's look at Constraint G/7: "Must preserve original question's operation skeleton...". And D3 says give variable ranges. This implies substitution IS expected in a generation task usually.
                *   Conflict Resolution: The prompt instruction is complex and contradictory (Standard Gen vs Fixed Target). Usually, the specific constraint at the end ("Dynamic Target Question Reference") overrides general "Generate" logic if it explicitly provides numbers to use as reference for structure but maybe allows variation? Or does it mean "Use this EXACT question"?
                *   Let's look at Constraint G/6 again: "若「動態目標題型參考」已提供完整可計算算式（含具體數字），禁止重新隨機抽數、禁止改寫為其他題目。" (If Dynamic Target Question Reference provides complete calculable formula with specific numbers, prohibit re-randomizing numbers...).
                *   This strongly suggests I should use the provided string `$(-8 )×6＋｜(-5 )×10-1｜$` as the basis. But `generate` is called to create questions. If I output this exact question every time, it satisfies "prohibit re-randomizing".
                *   HOWEVER, looking at Section D Step D3: It talks about generating variables v1, v2... This implies generation IS expected.
                *   Maybe the instruction means: Use THIS structure (Abs block + Plus + Times etc), but generate NEW numbers that fit the ranges defined in D3? But G/6 says "If provides complete formula with specific numbers". The text `$(-8 )×6＋｜(-5 )×10-1｜$` has specific numbers.
                *   Okay, let's look at the very first line of constraints: `【程式要求】（必須嚴格遵守）`. And later `【動態目標題型參考】...`.
                *   If I strictly follow G/6, I cannot change the numbers `-8`, `6`, etc. But then why have a