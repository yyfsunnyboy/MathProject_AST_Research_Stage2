import sys
sys.path.insert(0, '.')
from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab2 import generate

print('驗證 AB2 逆向工程生成品質...\n')
for i in range(3):
    result = generate()
    q = result['question_text']
    a = result['correct_answer']
    
    print(f'題目 {i+1}:')
    print(f'  {q}')
    print(f'  答案: {a}')
    
    # 檢查結構
    has_left_bracket = r'\left[' in q
    has_right_bracket = r'\right]' in q
    has_left_abs = r'\left|' in q
    has_right_abs = r'\right|' in q
    
    checks = [
        ('$ 符號對', q.count('$') == 2),
        ('[ 括號對', has_left_bracket and has_right_bracket),
        ('| 絕對值對', has_left_abs and has_right_abs),
    ]
    
    all_pass = all(result_check for _, result_check in checks)
    
    for check_name, result_check in checks:
        status = '✅' if result_check else '❌'
        print(f'  {status} {check_name}')
    
    if all_pass:
        print('  ✅ 題目格式完全正確\n')
    else:
        print('  ⚠️ 格式有問題\n')
