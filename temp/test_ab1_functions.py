import sys
sys.path.insert(0, 'skills')

from gh_ApplicationsOfDerivatives_Cloud_Ab1 import generate, check

# 測試生成
res = generate()
print('✅ 生成成功')
print(f'題目: {res["question_text"]}')
print(f'答案: {res["correct_answer"]}')

# 測試檢查函數
check_res = check(res['correct_answer'], res['correct_answer'])
print(f'\n✅ 檢查函數運作正常: {check_res}')
