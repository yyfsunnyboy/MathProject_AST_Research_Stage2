# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: qwen2.5-coder:14b | Strategy: V47.5 Unified-Cleanup + Advanced-Healer
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 12.49s | Tokens: In=453, Out=409
# Created At: 2026-01-31 18:08:55
# Fix Status: [Basic Cleanup] | Fixes: Basic=2, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = PASSED
# ==============================================================================
import random

def generate(level=1, **kwargs):
    # 生成隨機係數和次方
    a = random.randint(1, 5)
    b = random.randint(-5, 5)
    c = random.randint(1, 5)
    d = random.randint(-5, 5)
    
    # 定義函式 f(x) = ax^4 + bx^3 + cx - d
    question_text = f"已知 $f(x) = {a}x^4 + {b}x^3 + {c}x - {d}$，求 $f'(x)$ 與 $f'''(x)$。"
    
    # 計算一階導數 f'(x)
    f_prime = f"{4*a}x^3 + {3*b}x^2 + {c}"
    
    # 計算三階導數 f'''(x)
    f_triple_prime = f"12*{a}x"
    
    # 答案
    answer = f"f'(x) = {f_prime}, f'''(x) = {f_triple_prime}"
    correct_answer = answer
    
    return {
        'question_text': question_text,
        'answer': answer,
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    # 檢查答案是否正確
    if user_answer.strip() == correct_answer.strip():
        return {'correct': True, 'result': '正確'}
    else:
        return {'correct': False, 'result': '錯誤'}

# 範例使用
if __name__ == "__main__":
    question = generate()
    print(question['question_text'])
    user_input = input("請輸入你的答案: ")
    result = check(user_input, question['answer'])
    print(result['result'])