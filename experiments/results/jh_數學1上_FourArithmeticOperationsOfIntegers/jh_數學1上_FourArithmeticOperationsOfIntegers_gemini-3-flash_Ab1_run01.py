# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-3-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 54.78s | Tokens: In=0, Out=0
# Created At: 2026-02-13 23:05:38
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random

def generate(level=1, **kwargs):
    def fmt(n, bracket=True):
        if n < 0 and bracket:
            return f"({n})"
        return str(n)

    # 隨機生成除法部分的參數,確保能整除
    c = random.choice([i for i in range(-10, 11) if i != 0])
    res_div = random.randint(-10, 10)
    sum_ab = c * res_div
    a = random.randint(-30, 30)
    b = sum_ab - a
    d = random.randint(-10, 10)
    
    # 隨機生成絕對值部分的參數
    e = random.randint(-10, 10)
    f = random.randint(-10, 10)
    g = random.randint(-30, 30)
    
    # 隨機決定中間的運算符號 (+ 或 -)
    op_choice = random.choice(['+', '-'])
    
    # 計算正確答案
    val1 = int((a + b) / c) * d
    val2 = abs(e * f + g)
    
    if op_choice == '+':
        ans = val1 + val2
    else:
        ans = val1 - val2
        
    # 組合題目字串,模仿課本格式
    part1 = f"[{fmt(a)}+{fmt(b)}]÷{fmt(c)}×{fmt(d)}"
    op_g = "+" if g >= 0 else "-"
    part2 = f"|{fmt(e, False)}×{fmt(f)}{op_g}{abs(g)}|"
    
    question = f"計算 {part1}{op_choice}{part2}的值。"
    
    return {
        'question_text': question,
        'answer': '',
        'correct_answer': str(ans),
        'mode': 1
    }

def check(user_answer, correct_answer):
    ua = str(user_answer).strip()
    ca = str(correct_answer).strip()
    is_correct = (ua == ca)
    return {
        'correct': is_correct,
        'result': '正確' if is_correct else '錯誤'
}