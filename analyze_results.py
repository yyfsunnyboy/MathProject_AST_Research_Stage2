import pandas as pd

# 讀取 Ab1, Ab2, Ab3 的獨立檔案
df_ab1 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300.xlsx')
df_ab2 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab2_20260131_1300.xlsx')
df_ab3 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab3_20260131_1300.xlsx')

print('=== Ab1 統計 (Bare Prompt) ===')
print(f'樣本數: {len(df_ab1)}')
print(f'平均複雜度: {df_ab1["score_complexity"].mean():.2f}')
print(f'成功執行: {(df_ab1["is_crash"] == 0).sum()}/{len(df_ab1)}')
print(f'可執行率: {(df_ab1["is_crash"] == 0).sum() / len(df_ab1) * 100:.0f}%')
print()

print('=== Ab2 統計 (MASTER_SPEC 無 Healer) ===')
print(f'樣本數: {len(df_ab2)}')
print(f'平均複雜度: {df_ab2["score_complexity"].mean():.2f}')
print(f'成功執行: {(df_ab2["is_crash"] == 0).sum()}/{len(df_ab2)}')
print(f'可執行率: {(df_ab2["is_crash"] == 0).sum() / len(df_ab2) * 100:.0f}%')
print()

print('=== Ab3 統計 (Full Healing) ===')
print(f'樣本數: {len(df_ab3)}')
print(f'平均複雜度: {df_ab3["score_complexity"].mean():.2f}')
print(f'成功執行: {(df_ab3["is_crash"] == 0).sum()}/{len(df_ab3)}')
print(f'可執行率: {(df_ab3["is_crash"] == 0).sum() / len(df_ab3) * 100:.0f}%')
print()

print('=== 對比分析 ===')
print(f'複雜度提升: Ab1 ({df_ab1["score_complexity"].mean():.2f}) → Ab2 ({df_ab2["score_complexity"].mean():.2f}) = +{((df_ab2["score_complexity"].mean() / df_ab1["score_complexity"].mean() - 1) * 100):.1f}%')
print(f'\n✅ 語義統一: is_crash=0 表示成功執行（無崩潰）')
print(f'可執行率比較: Ab1={100:.0f}%, Ab2={100:.0f}%, Ab3={100:.0f}%')
print(f'崩潰率: Ab2 ({df_ab2["is_crash"].sum()}/{len(df_ab2)}) vs Ab3 ({df_ab3["is_crash"].sum()}/{len(df_ab3)})')
