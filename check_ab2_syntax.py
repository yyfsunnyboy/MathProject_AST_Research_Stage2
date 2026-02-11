import ast
import glob

# 檢查所有 7B Ab2 檔案
files = glob.glob('experiments/results/jh_數學1上_FourArithmeticOperationsOfIntegers/*7b_Ab2*.py')

for f in files:
    try:
        content = open(f, 'r', encoding='utf-8').read()
        ast.parse(content)
        print(f"{f.split('/')[-1]}: ✅ 語法正確")
    except SyntaxError as e:
        print(f"{f.split('/')[-1]}: ❌ 語法錯誤 - {e}")
