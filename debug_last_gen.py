import random

def generate(level=1):
    # 隨機產生數字，確保計算過程多為整數且符合例題風格
    a = random.randint(2, 12)
    b = random.randint(-10, -2)
    c = random.randint(-20, 20)
    
    # 計算絕對值內的值：a * b + c
    inner_value = a * b + c
    abs_value = abs(inner_value)
    
    # 尋找能整除 abs_value 的除數 d，確保題目漂亮
    divisors = [i for i in range(2, 13) if abs_value % i == 0]
    if not divisors:
        d = 1
    else:
        d = random.choice(divisors)
        
    e = random.randint(-9, 9)
    if e == 0: e = 1
    
    # 計算最終結果：|a*b+c| ÷ d * e
    # 依照運算順序，先算絕對值，再由左至右計算乘除
    correct_answer = (abs_value // d) * e
    
    # 格式化字串
    b_str = f"({b})" if b < 0 else str(b)
    c_str = f"{c}" if c < 0 else f"+{c}"
    e_str = f"({e})" if e < 0 else str(e)
    
    question_text = f"計算 | {a}×{b_str}{c_str} | ÷ {d}×{e_str} 的值。"
    
    return {
        "question_text": question_text,
        "correct_answer": str(correct_answer)
    }

# 範例呼叫
if __name__ == "__main__":
    print(generate(level=1))