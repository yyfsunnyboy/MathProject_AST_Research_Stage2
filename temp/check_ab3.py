import pandas as pd

df = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab3_20260131_1300.xlsx')

print("=== Ab3 is_crash 詳細檢查 ===")
print(f"數值分布:")
print(df['is_crash'].value_counts())
print(f"\nis_crash == 1: {(df['is_crash'] == 1).sum()}")
print(f"is_crash == 0: {(df['is_crash'] == 0).sum()}")
print(f"\n前5筆樣本:")
print(df[['sample_index', 'is_crash', 'score_complexity']].head())
