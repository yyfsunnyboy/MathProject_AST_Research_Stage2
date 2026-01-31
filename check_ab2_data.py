import pandas as pd

# 讀取 Ab2 數據
df2 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab2_20260131_1300.xlsx')

print("=== Ab2 詳細數據 ===")
print(f"總樣本數: {len(df2)}")
print(f"\n欄位: {df2.columns.tolist()}")

print(f"\nis_crash 統計:")
print(df2['is_crash'].value_counts())

print(f"\nis_logic_correct 統計:")
print(df2['is_logic_correct'].value_counts())

print(f"\n平均複雜度: {df2['score_complexity'].mean():.2f}")

print("\n前3筆樣本:")
print(df2[['sample_index', 'is_crash', 'is_logic_correct', 'score_complexity']].head(3))

print("\n=== 重要發現 ===")
print(f"is_crash=1 意義: 沒有崩潰（成功執行）")
print(f"Ab2 可執行率: {(df2['is_crash'] == 1).sum()}/{len(df2)} = 100%")
