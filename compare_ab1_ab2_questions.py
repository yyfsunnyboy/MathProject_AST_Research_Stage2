import pandas as pd

ab1 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300.xlsx')
ab2 = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab2_20260131_1300.xlsx')

print("=== Ab1 vs Ab2 題目對比 ===\n")

for i in range(min(2, len(ab1))):
    print(f"【樣本 {i+1}】")
    print(f"\nAb1 (Bare Prompt):")
    print(ab1.iloc[i]['Raw LaTeX Code (原始碼)'][:200])
    print(f"\nAb2 (MASTER_SPEC):")
    print(ab2.iloc[i]['Raw LaTeX Code (原始碼)'][:200])
    print("\n" + "="*70 + "\n")
