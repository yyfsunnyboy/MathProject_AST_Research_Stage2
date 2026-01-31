import pandas as pd

# 只修復 Ab1
df = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300.xlsx')

print(f"修改前 Ab1:")
print(f"  is_crash=0: {(df['is_crash'] == 0).sum()}")
print(f"  is_crash=1: {(df['is_crash'] == 1).sum()}")

# 反轉
df['is_crash'] = 1 - df['is_crash']

print(f"\n修改後 Ab1:")
print(f"  is_crash=0: {(df['is_crash'] == 0).sum()}")
print(f"  is_crash=1: {(df['is_crash'] == 1).sum()}")

# 保存
df.to_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300_corrected.xlsx', index=False)
print("\n✓ 已保存到 _corrected.xlsx")
