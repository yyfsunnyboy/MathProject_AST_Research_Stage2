#!/usr/bin/env python
import pandas as pd
import glob

# 找最新的 Excel 檔案
files = glob.glob('reports/*.xlsx')
if files:
    latest = max(files, key=lambda x: x)
    print(f'檔案: {latest}')
    df = pd.read_excel(latest)
    print(f'\n欄位: {list(df.columns)}')
    print(f'\n前 3 列資料:')
    for i in range(min(3, len(df))):
        print(f'\n--- Row {i+1} ---')
        q_col = 'Raw LaTeX Code (原始碼)'
        print(f'question_text: {df.iloc[i][q_col][:50]}...')
        print(f'correct_answer: {df.iloc[i]["correct_answer"]}')
else:
    print('no excel files')
