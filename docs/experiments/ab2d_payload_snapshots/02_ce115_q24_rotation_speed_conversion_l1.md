# Task Metadata
- task_id: ce115_q24_rotation_speed_conversion_l1
- raw skill_id: rpm_circumference_to_kph
- normalized skill_id: jh_數學1上_FourArithmeticOperationsOfNumbers
- selected skill folder: agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers
- mapping classification: TEMPORARY_FAMILY_MAPPING
- difficulty: 1

# Prompt Sources
- SKILL.md path: agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers/SKILL.md
- prompt_benchmark.md path: agent_skills/jh_數學1上_FourArithmeticOperationsOfNumbers/prompt_benchmark.md
- loader function: agent_tools.benchmark.load_prompt_from_skill(..., ablation_target="Ab3", task_metadata=...)
- whether check() is present: NO

# Injected APIs
- IntegerOps
- FractionOps

# Entry Point Contract
- function name: generate
- parameters: level=1, **kwargs
- return schema: dict with question_text (str), correct_answer (dict), and oracle_payload (dict)

# Final Assembled Payload
```markdown
/no_think

# Fraction Arithmetic Skill Specification

Skill ID: `jh_數學1上_FourArithmeticOperationsOfNumbers`
Stage: Junior High Grade 7, Semester 1
Core topic: fractions, mixed numbers, signed fractions, decimal-fraction mixed arithmetic, reciprocal, and textbook word problems built on fraction invariance.

## Skill Positioning

This skill is best modeled as a hybrid of:
- `Family Catalogue` from polynomial
- `deterministic helper path` from integer
- `strict structural data contract` from radicals for fraction display and answer normalization

In production, this skill should prefer deterministic helper orchestration for textbook-shaped fraction questions. Prompt generation remains a fallback, not the primary source of truth.

## Output Contract

Generated code must define:

```python
def generate(level=1, **kwargs):
    return {
        "question_text": str,
        "answer": "",
        "correct_answer": str,
        "mode": 1,
    }
```
本 benchmark 不要求實作 check()。

Hard requirements:
- `correct_answer` must never be empty.
- Fraction answers must be reduced.
- Improper fractions are allowed in `correct_answer`; mixed numbers are reserved for display-sensitive family decisions only.
- Equivalent numeric forms are accepted in `check()` when the family is numeric-answer based.
- Comparison families must preserve the full order relation, not just the max/min endpoint.

## Hard Rules

1. The generated problem must stay in the same fraction family as the source.
2. Do not drift from fraction arithmetic into integer-only arithmetic unless the source answer simplifies to an integer.
3. Keep denominator sign normalized: use `-a/b`, never `a/-b`.
4. Mixed numbers must be interpreted structurally:
   `-2 3/4 = -(2 + 3/4)`, not `(-2) + 3/4`.
5. Decimal operands must be converted exactly to `Fraction` during evaluation.
6. Reciprocal families must reject zero.
7. Word problems must preserve the same governing fraction relationship, not just the same answer type.

## Family Catalogue

### F1. Fraction Simplification
Definition:
- judge whether a fraction or mixed number is already in simplest form
- if not, reduce it

Representative forms:
- `45/60`
- `-36/96`
- `16/-81`
- `-2 15/33`

Expected answer type:
- reduced fraction or reduced mixed number

### F2. Equivalent Fraction Fill-Blank
Definition:
- solve blanks in an equivalence chain of fractions

Representative forms:
- `-4/5 = -12/15 = 20/-25 = (_)/-50`
- `-7/3 = -35/15 = 28/(_) = (_)/-45`

Expected answer type:
- comma-separated scalar blanks in left-to-right order

### F3. Preserve-Value Fraction Invariance
Definition:
- one part of a fraction changes by a fixed amount; solve the required corresponding change so value stays the same

Representative form:
- `5/6` denominator plus `18`, numerator should plus how much

Expected answer type:
- integer

### F4. Fraction Comparison
Definition:
- compare two or more fractions or mixed numbers
- includes positive, negative, improper, and mixed-number comparison

Representative forms:
- `2/3, 3/4, 5/6`
- `-3/4, -7/9, -11/12`
- `-1 1/2, -1 2/3, -1 3/4`

Expected answer type:
- ascending order chain, e.g. `-11/12 < -7/9 < -3/4`

### F5. Fraction Add/Subtract
Definition:
- evaluate signed fraction addition/subtraction
- includes same denominator, unlike denominator, nested parentheses, and mixed numbers

Representative forms:
- `(-7/5)+(-9/5)`
- `2/3-(-3/4)+(-1/6)`
- `(-2 3/4)+1 2/7`

Expected answer type:
- reduced fraction or integer

### F6. Fraction Multiply
Definition:
- evaluate signed fraction or mixed-number multiplication
- includes chained products and telescoping products

Representative forms:
- `(-3/2) * 1/4`
- `(-2 1/3) * (-5/21) * (-1 1/5)`
- `(-2/3)(-3/4)(-4/5)...(-99/100)`

Expected answer type:
- reduced fraction or integer

### F7. Fraction Divide
Definition:
- evaluate division by fraction / mixed number / decimal
- may include mixed multiply-divide expressions

Representative forms:
- `5/6 ÷ (-3 1/3)`
- `(-9/8) ÷ (-3/4) ÷ 1/3`
- `3/2 ÷ (-0.6) * (-3/5) - 1/2`

Expected answer type:
- reduced fraction or integer

### F8. Reciprocal
Definition:
- write the reciprocal of a fraction, integer, or mixed number

Representative forms:
- `3 2/5`
- `-4/7`
- `-1`

Expected answer type:
- reduced fraction or integer

### F9. Decimal-Fraction Mixed Evaluation
Definition:
- fraction arithmetic where decimals and integers appear in the same expression

Representative forms:
- `0.3*2/3 - (-7/5) ÷ [5/3 + (-0.5)]`
- `(-1/3)*(3/5+1.5) ÷ (-2 1/5)`

Expected answer type:
- reduced fraction or integer

### F10. Fraction Word Problems
Definition:
- apply fraction relationships to rate, remaining amount, inheritance, or before/after ratio

Representative subfamilies:
- drone remaining pesticide weight
- bottle and juice weight
- remaining milk amount
- inheritance share comparison
- library before/after book count

Expected answer type:
- reduced scalar answer or verbal comparison result

## Sub-skill Graph

```text
Fraction Arithmetic
├─ Fraction Representation
│  ├─ proper / improper fractions
│  ├─ mixed numbers
│  ├─ sign normalization
│  └─ decimal-to-fraction exact conversion
├─ Structural Reasoning
│  ├─ simplest-form reduction
│  ├─ equivalent-fraction scaling
│  ├─ reciprocal transform
│  └─ preserve-value invariance
├─ Order Reasoning
│  ├─ positive fraction comparison
│  ├─ negative fraction comparison
│  └─ mixed-number comparison
├─ Expression Evaluation
│  ├─ add/sub
│  ├─ multiply
│  ├─ divide
│  ├─ nested parentheses
│  ├─ decimal-fraction mixed arithmetic
│  └─ telescoping products
└─ Applied Word Problems
   ├─ remaining amount
   ├─ container weight
   ├─ before/after ratio
   └─ share comparison
```

## Structural Schema

### Numeric Node Schema

```python
{
    "value": Fraction,
    "kind": "fraction" | "mixed" | "int" | "decimal",
    "label": str,
}
```

### Family Config Schema

```python
{
    "family": str,
    "source_text": str,
    ... family-specific fields ...
}
```

Examples:

```python
{
    "family": "frac_compare_set",
    "numbers": [
        {"value": Fraction(-3, 4), "label": "-3/4"},
        {"value": Fraction(-7, 9), "label": "-7/9"},
    ],
}
```

```python
{
    "family": "frac_equivalent_fill_blank",
    "base_value": Fraction(-4, 5),
    "blank_specs": [{"kind": "num", "den": -50}],
}
```

## Answer-Type Contract

- Simplify / eval / reciprocal / invariant / numeric word problems:
  reduced scalar string such as `-7/3`, `25`, `3/8`
- Comparison:
  ordered chain such as `2/7 < 3/13 < 5/23`
- Fill blank:
  comma-separated answers such as `40,-105`
- Inheritance comparison:
  verbal answer such as `四人分得相同`

## Engineering Path

Primary runtime path:
- `core/fraction_domain_functions.py`
  - `FractionFunctionHelper.build_config`
  - `FractionFunctionHelper.generate_from_config`

LiveShow deterministic route:
- `core/routes/live_show.py`
  - direct helper path when `skill_id` contains `FourArithmeticOperationsOfNumbers`

Support policy:
- `core/skill_policies/fraction.py`

## Phase-1 Scope

Covered:
- textbook-style simplify / compare / fill blank / reciprocal
- signed fraction add/sub/mul/div
- mixed numbers
- decimal-fraction exact arithmetic
- telescoping products
- listed non-image word problems

Excluded in phase 1:
- image-dependent shaded geometry
- OCR cases where the diagram contains unlabeled region partition information not present in text


=== SKILL_END_PROMPT ===

【任務】
實作 `def generate(level=1, **kwargs)`，生成「分數四則運算」題目。
題目結構必須為：中括號混合運算 + 除法 + 絕對值；Level 越高層次越深。
回傳 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

【目標對齊（最高優先）】
1. 必須複製使用者提供題型的結構（同構），只替換數字，不替換運算拓撲。
2. 新題難度必須與原題相近，不可突然放大數值級距。
3. 題目與答案都必須符合七年級初學者可讀、可算、可驗算。

【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【核心規則】
1. **題目結構**：
   - Level 1: `[Part 1] \div Part 2 + |Part 3|`
   - Level 2: `[Part 1 - Part 2] \div Part 3 + |Part 4|`
   - Level 3: `-[Part 1] + |Part 2| - (Part 3) + Part 4`
2. **分數範圍**：
    - Level 1~3: 分子 `-50 ~ 50`、分母 `-10 ~ 10`（分母不可為 0）
    - 題面分母建議避開 `±1`，降低題目退化成整數四則的機率。
    - 所有分子必須額外滿足硬限制：`-50 <= numerator <= 50`
    - 分子與分母的正負號必須隨機抽樣，不可固定某一位置永遠為正或永遠為負。
3. **格式化要求**：
   - 分數顯示必須使用 `FractionOps.to_latex(...)`
   - 乘號必須用 `\times`，除號必須用 `\div`
   - 中括號用 `\left[ ... \right]`
   - 絕對值用 `\left| ... \right|`
4. **答案要求**：
    - ✅ 答案可以是分數，不必為整數。
   - 結果若為整數，`correct_answer` 輸出整數字串
   - 否則輸出 `a/b` 最簡分數字串
5. **七年級友善限制**：
    - 最終答案建議限制為：`|numerator| <= 40` 且 `denominator <= 12`
    - 若超出範圍，應重新抽樣，避免出現過大數字
6. **題面美觀限制（Ab2 必做）**：
    - 題面禁止出現 `\\frac{n}{1}`，分母為 1 必須直接顯示整數。
    - 題面分數必須先約分（禁止 `2/10`、`10/15` 這類未約分表示）。
    - 題面若出現 `|numerator| > denominator` 的分數，必須以「帶分數」顯示（例如 `17/4` 顯示為 `4\frac{1}{4}`，`-13/5` 顯示為 `-2\frac{3}{5}`）。
    - 題面禁止小數表示分數值（例如 `2.5`、`-1.75`）。
    - 題面中任一單一整數建議 `|n| <= 50`，超過就重抽。
    - 題面分母建議 `|denominator| <= 10` 且分母不可為 0。
    - 最終答案若為分數，建議 `|numerator| <= 120` 且 `denominator <= 30`，超過就重抽。

【強烈建議程式碼結構】
```python
import random
import math
from fractions import Fraction


def generate(level=1, **kwargs):
    fmt = IntegerOps.fmt_num

    if level == 1:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    elif level == 2:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10
    else:
        n_min, n_max = -50, 50
        d_min, d_max = -10, 10

    def rand_frac():
        num = IntegerOps.random_nonzero(n_min, n_max)
        den = random.randint(d_min, d_max)
        while den == 0 or abs(den) == 1:
            den = random.randint(d_min, d_max)
        return Fraction(num, den)

    def latex_frac_clean(x):
        x = Fraction(x)
        if x.denominator == 1:
            return str(x.numerator)
        return FractionOps.to_latex(x)

    for _ in range(40):
        try:
            a = rand_frac()
            b = rand_frac()
            c = rand_frac()
            d = rand_frac()
            e = rand_frac()
            f = rand_frac()
            g = rand_frac()
            h = rand_frac()

            if c == 0 or f == 0:
                continue

            p1_val = (a + b) * c
            p2_val = d
            p3_val = abs(e * f - g)

            p1_str = f"\\left[{latex_frac_clean(a)} + {latex_frac_clean(b)}\\right] \\times {latex_frac_clean(c)}"
            p2_str = f"\\left({latex_frac_clean(p2_val)}\\right)"
            p3_str = f"\\left|{latex_frac_clean(e)} \\times {latex_frac_clean(f)} - {latex_frac_clean(g)}\\right|"

            if level == 1:
                math_str = f"\\left[{p1_str}\\right] \\div {p2_str} + {p3_str}"
                ans = Fraction(p1_val, 1) / p2_val + p3_val
            elif level == 2:
                p4_val = abs(a - b / c)
                p4_str = f"\\left|{latex_frac_clean(a)} - {latex_frac_clean(b)} \\div {latex_frac_clean(c)}\\right|"
                math_str = f"\\left[{p1_str} - {latex_frac_clean(h)}\\right] \\div {p2_str} + {p4_str}"
                ans = (p1_val - h) / p2_val + p4_val
            else:
                p4_val = h
                p4_str = latex_frac_clean(p4_val)
                math_str = f"-\\left[{p1_str}\\right] + {p3_str} - \\left({latex_frac_clean(d)} \\div {latex_frac_clean(f)}\\right) + {p4_str}"
                ans = -p1_val + p3_val - (d / f) + p4_val

            if ans.denominator == 1:
                correct = str(ans.numerator)
            else:
                correct = f"{ans.numerator}/{ans.denominator}"

            if abs(ans.numerator) > 120 or ans.denominator > 30:
                continue

            if any(abs(x.numerator) > 50 for x in [a, b, c, d, e, f, g, h]):
                continue

            return {
                'question_text': f'計算 $' + math_str + '$ 的值。',
                'answer': '',
                'correct_answer': correct,
                'mode': 1
            }
        except Exception:
            continue

    return {'question_text': 'Error', 'answer': '', 'correct_answer': '0', 'mode': 1}
```

❌ 輸出 Markdown 代碼塊 → 直接寫 code
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think


# Answer Schema Contract
Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "coefficient": str,  # speed coefficient for 1 rpm in the format "p/q" (reduced fraction string, or "n" if denominator is 1)
      "unit": str          # must be exactly "km/h"
  },
  "oracle_payload": dict
}
- Formatting rules: Reduce the fraction completely. Output integer if the denominator is 1.
- Equality: Exact dictionary match. No tolerance.

```

# Contract Audit
- routing correct: YES
- expected skill loaded: YES
- expected APIs injected: YES
- entry point explicit: YES
- output schema explicit: YES
- conflicting instructions: NO
- check() mismatch present: NO
- blocking issue: NONE
