import pandas as pd
import os

# 找到最新的 Excel 檔案
reports_dir = 'reports'
files = [f for f in os.listdir(reports_dir) if 'ApplicationsOfDerivatives_14B_Ab3' in f and f.endswith('.xlsx')]
files.sort(reverse=True)
latest_file = os.path.join(reports_dir, files[0])

df = pd.read_excel(latest_file)


print(f'報表: {files[0]}')
print(f'總共 {len(df)} 道題目')
print(f'欄位: {list(df.columns)}')
print('\n前 3 道題目:')
print('='*90)
for i in range(min(3, len(df))):
    print(f'\n【題目 {i+1}】')
    raw_code = df.iloc[i]['Raw LaTeX Code (原始碼)']
    ans = df.iloc[i]['correct_answer']
    print(f'Raw Code: {raw_code}')
    print(f'Answer: {ans}')
