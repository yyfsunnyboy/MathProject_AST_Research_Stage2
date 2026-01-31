import pandas as pd

df = pd.read_excel('reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300.xlsx')

print("=== Ab1 生成的題目樣本 ===\n")

for i in range(min(3, len(df))):
    print(f"樣本 {i+1}:")
    print(df.iloc[i]['Raw LaTeX Code (原始碼)'][:250])
    print("\n" + "="*60 + "\n")
