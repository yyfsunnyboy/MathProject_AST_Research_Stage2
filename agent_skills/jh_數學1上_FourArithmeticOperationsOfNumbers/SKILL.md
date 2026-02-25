# Skill: jh_數學1上_FourArithmeticOperationsOfNumbers

## [DOMAIN_API]
- `to_latex(num)`: 轉成 LaTeX 分數格式，支援 `Fraction` 和整數自動化簡套用。
- `fmt_num(num)`: 格式化數字（自動加括號）。**警告：此函數回傳字串，絕對禁止將此字串進行加減乘除計算。**
- `Fraction(n, d)`: Python 內建的分數運算類別（從 `fractions` import）。

## [NUMERICAL_SPEC]
- 必須 import `random` 和 `from fractions import Fraction`。
- **嚴禁定義任何類（class）**！只寫 `generate()` 和 `check()` 兩個函數。
- **絕對禁止**將 `question_text` 丟入 `eval` 或 `safe_eval`，必須用 `Fraction` 物件算出真正數值。
- 所有分數乘除計算必須透過 `Fraction` 運算確保精確，最後再轉字串： `result.numerator` / `result.denominator`。
- 教學安全：分數除法必須確保分母不為 0。
- LaTeX 格式化規範：
  - 乘法用 `\times`，除法用 `\div`。
  - 絕對值必須使用 `\left| ... \right|`，中括號用 `\left[ ... \right]`。
  - LaTeX 算式整體需用雙錢號包覆：`$$ ... $$`。
  - 負分數：`\left(-\frac{5}{2}\right)` 或 `-\frac{5}{2}`。
- **Python f-string 反斜線雙寫**：必須寫成 `\\times`, `\\div`, `\\frac{{a}}{{b}}`, `\\left|`，嚴禁單一 `\` 造成 SyntaxError。

## [LEGACY_CODE_DNA]
```python
import random
from fractions import Fraction

def generate(level=1, **kwargs):
    if level == 1:
        int_range = (-5, 5)
        frac_range = (1, 6)
    elif level == 2:
        int_range = (-20, 20)
        frac_range = (1, 12)
    else:  # level 3
        int_range = (-100, 100)
        frac_range = (1, 20)
    
    # Part 1: Bracket with fractions
    a = random.randint(*int_range)
    b = random.randint(1, int_range[1])
    num1 = random.randint(1, frac_range[1])
    den1 = random.randint(2, frac_range[1])
    frac1 = Fraction(num1, den1)
    
    part1_str = f"\\left[({a}+{b}) \\times {to_latex(frac1)}\\right]"
    
    # Part 2: Division by fraction
    num2 = random.randint(-frac_range[1], -1)
    den2 = random.randint(2, frac_range[1])
    frac2 = Fraction(num2, den2)
    part2_str = f"\\left({to_latex(frac2)}\\right)"
    
    # Part 3: Absolute value with fraction
    c = random.randint(int_range[0]//2, int_range[1]//2)
    num3 = random.randint(-frac_range[1], -1)
    den3 = random.randint(2, frac_range[1])
    frac3 = Fraction(num3, den3)
    d = random.randint(1, frac_range[1])
    
    part3_str = f"\\left|{c} \\times {to_latex(frac3)} - {d}\\right|"
    
    question_text = f"計算 $$ {part1_str} \\div {part2_str} + {part3_str} $$ 的值。"
    
    val1 = (a + b) * frac1
    val2 = frac2
    val3 = abs((c * frac3) - d)
    
    result = (val1 / val2) + val3
    
    if result.denominator == 1:
        correct_answer = str(result.numerator)
    else:
        correct_answer = f"{result.numerator}/{result.denominator}"
    
    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    try:
        ua_str = str(user_answer).strip()
        ca_str = str(correct_answer).strip()
        if ua_str == ca_str:
            return {'correct': True, 'result': '正確'}
        ua = float(Fraction(ua_str))
        ca = float(Fraction(ca_str))
        if abs(ua - ca) < 1e-9:
             return {'correct': True, 'result': '正確'}
        return {'correct': False, 'result': '錯誤'}
    except:
        return {'correct': False, 'result': '錯誤'}
```