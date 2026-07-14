# Task Metadata
- task_id: ce115_cr01_training_sequence_threshold_l3
- raw skill_id: alternating_training_progression_threshold
- normalized skill_id: jh_數學1上_FourArithmeticOperationsOfIntegers
- selected skill folder: agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers
- mapping classification: TEMPORARY_FAMILY_MAPPING
- difficulty: 3

# Prompt Sources
- SKILL.md path: agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/SKILL.md
- prompt_benchmark.md path: agent_skills/jh_數學1上_FourArithmeticOperationsOfIntegers/prompt_benchmark.md
- loader function: agent_tools.benchmark.load_prompt_from_skill(..., ablation_target="Ab3", task_metadata=...)
- whether check() is present: NO

# Injected APIs
- IntegerOps

# Entry Point Contract
- function name: generate
- parameters: level=1, **kwargs
- return schema: dict with question_text (str), correct_answer (dict), and oracle_payload (dict)

# Final Assembled Payload
```markdown
/no_think
【角色】K12 數學演算法工程師（整數四則運算）

本技能對應 `jh_數學1上_FourArithmeticOperationsOfIntegers`，負責國中一年級上學期整數四則運算與其結構同構變形題。

目標不是只解出一題，而是產生可重複出題、可 LiveShow、可 benchmark、可回歸測試的穩定生成器。

════════════════════════════════════════════════════════════════
【Skill Identity】
════════════════════════════════════════════════════════════════
- `skill_id`: `jh_數學1上_FourArithmeticOperationsOfIntegers`
- `display_name`: 整數四則運算
- `family`: `integer`
- 支援模式：`BENCHMARK`、`LIVESHOW`
- 核心能力：整數加減乘除、負數括號、中括號、絕對值、整除型運算、複合結構同構

════════════════════════════════════════════════════════════════
【Output Contract】
════════════════════════════════════════════════════════════════
最終腳本必須定義：

```python
def generate(level=1, **kwargs):
    ...
```
本 benchmark 不要求實作 check()。

`generate()` 必須回傳：

```python
{
    "question_text": str,
    "answer": "",
    "correct_answer": str,
    "mode": 1
}
```

規則：
1. `answer` 必須固定為空字串。
2. `correct_answer` 不可為空。
3. `question_text` 中可見數學式必須用 `$...$` 包裹。
4. 若題面出現乘除符號，顯示層必須用 `\\times`、`\\div`。
5. 負整數在題面中應以 `IntegerOps.fmt_num` 維持 `(-n)` 風格。

════════════════════════════════════════════════════════════════
【Engineering Constraints】
════════════════════════════════════════════════════════════════
1. 必須 `import random`、`import math`；若有需要可 `from fractions import Fraction`。
2. 嚴禁 `import IntegerOps`；系統已注入，直接使用 `IntegerOps.xxx`。
3. 嚴禁直接對未受信任字串使用 `eval`；若需要算字串，只能用 `IntegerOps.safe_eval`。
4. 所有隨機數必須來自動態生成，不可硬編碼原題常數。
5. 只允許更換數值，不可任意改動運算子順序、括號拓撲、絕對值數量或中括號數量。
6. 含除法的 family 若答案應為整數，必須先做整除檢查，不可回傳小數或分數。
7. 若原題使用 `(-n)` 形式，生成題也必須保留 parenthesized negative 風格。

════════════════════════════════════════════════════════════════
【Injected APIs】
════════════════════════════════════════════════════════════════
- `IntegerOps.random_nonzero(min_val, max_val)`：生成絕不為 0 的整數
- `IntegerOps.fmt_num(n)`：將負數格式化為 `(-n)`
- `IntegerOps.safe_eval(expr)`：安全計算 Python 算式
- `IntegerOps.op_to_latex(op)`：運算子轉 LaTeX（若底層已提供）

════════════════════════════════════════════════════════════════
【Family Catalogue】
════════════════════════════════════════════════════════════════
以下 family ID 為本技能的正式分類。LiveShow 與 benchmark 生成器應以此 catalogue 為最高語義對齊依據。

### I1 `int_numberline_add_sub`
Definition:
- 數線語境的整數加減
- 雖然題面可能是敘述式，但核心算式仍是單一步整數加減

Typical examples:
- `利用數線求 $(-2)+(-5)$ 的值。`
- `利用數線求 $7+(-3)$ 的值。`

Quality gate:
- 只允許一個主運算
- 不引入額外括號結構

### I2 `int_flat_add_sub`
Definition:
- 純整數加減法，無中括號、無絕對值
- 可含多個負數項

Typical examples:
- `計算 $(-8)+15-(-4)$。`
- `計算 $7-12+9$。`

Quality gate:
- 只含 `+`、`-`
- 結構扁平

### I3 `int_flat_mul_div_exact`
Definition:
- 扁平整數乘除
- 若含除法，結果必須整除

Typical examples:
- `計算 $(-6)\\times4$。`
- `計算 $48\\div(-6)$。`
- `計算 $(-12)\\times3\\div(-4)$。`

Quality gate:
- 不含 `[]` 與 `| |`
- 除法結果必須為整數

### I4 `int_flat_mixed_four_ops`
Definition:
- 扁平整數四則混合運算
- 無中括號與絕對值，但可能同時含 `+ - * /`

Typical examples:
- `計算 $(-3)+5\\times(-2)$。`
- `計算 $18\\div(-3)-7$。`

Quality gate:
- 必須保留運算子順序
- 不可把混合四則降級成單一步加減或乘除

### I5 `int_bracket_mixed`
Definition:
- 含中括號 `[]` 或多層括號的整數四則
- 中括號內外結構皆屬同構約束的一部分

Typical examples:
- `計算 $[(-3)+8]\\times(-2)$。`
- `計算 $18-[5-(-4)]$。`

Quality gate:
- 中括號數量固定
- 括號內外運算子數量與順序都必須維持

### I6 `int_abs_value`
Definition:
- 含 `| |` 的整數運算
- 絕對值段是主結構，不可刪除

Typical examples:
- `計算 $|(-7)+2|$。`
- `計算 $|(-3)\\times4|-5$。`

Quality gate:
- `eval_str` 中必須用 `abs(...)`
- 顯示層需保留 `\\left| ... \\right|`

### I7 `int_division_exact_nested`
Definition:
- 含括號、絕對值或複合分子分母的整除型整數題
- 可能需要先算局部分子或分母，再檢查整除

Typical examples:
- `計算 $[18-(-6)]\\div3$。`
- `計算 $|(-8)+2|\\div2$。`

Quality gate:
- 最終答案必須為整數
- 不可使用浮點近似

### I8 `int_composite_structure`
Definition:
- 同時含有兩種以上特殊結構：`(-n)`、`[]`、`| |`、混合四則、整除約束
- 屬於高階複合 family

Typical examples:
- `計算 $|[(-6)+9]\\times(-2)|$。`
- `計算 $[15-(-3)]\\div|(-2)+5|$。`

Quality gate:
- 必須完整保留所有結構節點
- 不可將複合題降級為單一 family

════════════════════════════════════════════════════════════════
【Sub-skill Graph / 子技能節點】
════════════════════════════════════════════════════════════════
每個 family 可視為以下子技能節點的組合：

- `node.int.sign_handling`
- `node.int.add_sub`
- `node.int.mul_div`
- `node.int.order_of_operations`
- `node.int.bracket_scope`
- `node.int.absolute_value`
- `node.int.exact_divisibility`
- `node.int.isomorphic_structure`

Family 到節點的對應：
- `I1` → `sign_handling`, `add_sub`
- `I2` → `sign_handling`, `add_sub`
- `I3` → `sign_handling`, `mul_div`, `exact_divisibility`
- `I4` → `sign_handling`, `add_sub`, `mul_div`, `order_of_operations`
- `I5` → `sign_handling`, `bracket_scope`, `order_of_operations`
- `I6` → `sign_handling`, `absolute_value`
- `I7` → `sign_handling`, `mul_div`, `bracket_scope`, `absolute_value`, `exact_divisibility`
- `I8` → 全部節點

════════════════════════════════════════════════════════════════
【Structural Schema / vars 參考】
════════════════════════════════════════════════════════════════
整數 skill 雖以結構 fingerprint 為主，但若需顯式描述 family，可使用下列 schema。所有值都必須是純數值或明確結構，不可用運算式字串充當 vars。

- `I1 int_numberline_add_sub`
  - `{"a": int, "b": int, "op": "+"|"-"}`
- `I2 int_flat_add_sub`
  - `{"values": [int, ...], "ops": ["+", "-", ...]}`
- `I3 int_flat_mul_div_exact`
  - `{"values": [int, ...], "ops": ["*", "/", ...]}`
- `I4 int_flat_mixed_four_ops`
  - `{"values": [int, ...], "ops": ["+", "-", "*", "/", ...]}`
- `I5 int_bracket_mixed`
  - `{"outer_values": [...], "inner_values": [...], "ops": [...], "has_square_brackets": true}`
- `I6 int_abs_value`
  - `{"abs_values": [int, ...], "abs_ops": [...], "tail_values": [int, ...], "tail_ops": [...]}`
- `I7 int_division_exact_nested`
  - `{"numerator_parts": [...], "denominator_parts": [...], "structure_flags": {"abs": bool, "bracket": bool}}`
- `I8 int_composite_structure`
  - `{"segments": [...], "structure_flags": {"abs": bool, "bracket": bool, "parenthesized_negative": bool}}`

════════════════════════════════════════════════════════════════
【Generator Priority】
════════════════════════════════════════════════════════════════
1. 優先產生同 family、同結構深度、同答案型態的隨機生成器。
2. 其次是同 family、同難度層級的隨機生成器。
3. 再其次是可編譯、可穩定執行、且不破壞 family 的保守生成器。
4. 固定單題只作最後不得已 fallback。

════════════════════════════════════════════════════════════════
【Verification Logic】
════════════════════════════════════════════════════════════════
輸出前必須自檢：
- `question_text` 與 `correct_answer` 型態正確。
- 題面可見數學與內部計算來自同一套變數。
- 若有 `[]`、`| |`、`(-n)`，顯示層必須保留。
- 若有除法，結果不得為非整數。

════════════════════════════════════════════════════════════════
【Minimum check() Contract】
════════════════════════════════════════════════════════════════
本 benchmark 不要求實作 check()。


=== SKILL_END_PROMPT ===

【任務】
實作 `def generate(level=1, **kwargs)`，生成整數四則運算題目。
題目結構必須為：括號內混合運算 + 絕對值 + (Level 3: 高難度多層混和)。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 嚴禁寫 "Okay, I need to..." 或 "Let me think..."
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【核心規則】
1. **題目結構**：
   - Level 1: Part 1 + Part 2
   - Level 2: Part 1 - Part 2 + Part 3
   - Level 3: -Part 1 + Part 2 - Part 3 + K
2. **數值範圍**：
   - Level 1: -20 ~ 20
   - Level 2: -50 ~ 50
   - Level 3: -100 ~ 100
3. **格式化要求**：
   - 所有負數必須使用 `IntegerOps.fmt_num(n)` 包裹。
   - 題目中的乘號用 `\times`，除號用 `\div`。

【強烈建議程式碼結構】
```python
import random
import math
# IntegerOps is injected automatically

def generate(level=1, **kwargs):
    # 1. Scaling
    if level == 1:
        r_min, r_max = -20, 20
        div_max = 10
    elif level == 2:
        r_min, r_max = -50, 50
        div_max = 20
    else:
        r_min, r_max = -100, 100
        div_max = 30

    def rand_nz(a, b):
        choices = [x for x in range(a, b+1) if x != 0]
        if not choices: return 1
        return random.choice(choices)

    # Part 1: Complex Division [(a*m + b) / divisor]
    divisor = rand_nz(2, div_max)
    quotient = rand_nz(-15, 15)
    dividend = divisor * quotient

    m = rand_nz(2, 5)
    a_approx = dividend // m
    if a_approx == 0: a_approx = 5
    a = rand_nz(a_approx - 5, a_approx + 5)
    b = dividend - (a * m)

    # 格式化 Part 1
    fmt = IntegerOps.fmt_num
    part1_str = f"[({fmt(a)} \\times {fmt(m)}) + {fmt(b)}] \\div {fmt(divisor)}"
    part1_val = quotient

    # Part 2: Absolute Value |d*e - f + g|
    d = rand_nz(-10, 15)
    e = rand_nz(-10, 10)
    f = rand_nz(1, 20)
    g = rand_nz(-10, 10)

    if level == 1:
        part2_str = f"|{fmt(d)} \\times {fmt(e)} - {fmt(f)}|"
        part2_val = abs(d * e - f)
    else:
        part2_str = f"|{fmt(d)} \\times {fmt(e)} - {fmt(f)} + {fmt(g)}|"
        part2_val = abs(d * e - f + g)

    # Part 3: Extra Term (h*i - j)
    h = rand_nz(-10, 10)
    i = rand_nz(2, 5)
    j = rand_nz(1, 10)
    part3_str = f"({fmt(h)} \\times {fmt(i)} - {fmt(j)})"
    part3_val = h * i - j

    # Final Assembly
    k = rand_nz(-50, 50)

    if level == 1:
        question_text = f"計算 ${part1_str} + {part2_str}$ 的值。"
        ans = part1_val + part2_val
    elif level == 2:
        question_text = f"計算 ${part1_str} - {part2_str} + {part3_str}$ 的值。"
        ans = part1_val - part2_val + part3_val
    else:
        question_text = f"計算 $- {part1_str} + {part2_str} - {part3_str} + {fmt(k)}$ 的值。"
        ans = -part1_val + part2_val - part3_val + k

    return {
        'question_text': question_text,
        'answer': '',       # 必須為空字串
        'correct_answer': str(int(ans)),
        'mode': 1
    }
```

❌ 輸出 Markdown 代碼塊 → 直接寫 code
⚠️ Output Python code ONLY. No introduction. No comments. No thinking.
/no_think


# Answer Schema Contract
Required return schema:
{
  "question_text": str,
  "correct_answer": {
      "specified_session_laps": int,  # laps completed in the specified week and day
      "first_exceed_week": int,        # 1-indexed week number when the total distance first exceeds threshold_km
      "first_exceed_day": str         # day label of the first exceed session
  },
  "oracle_payload": dict
}
- Formatting rules: match day label strings exactly from the list provided.
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
