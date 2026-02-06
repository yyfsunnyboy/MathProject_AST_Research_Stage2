"""
修復 Ab1 和 Ab2 Excel 文件中的 is_crash 欄位錯誤

舊邏輯（錯誤）: is_crash = 1 表示成功執行
新邏輯（正確）: is_crash = 0 表示成功執行（沒有崩潰）

這個腳本會反轉 Ab1 和 Ab2 的 is_crash 值
"""
import pandas as pd
import os

# 目標文件
files_to_fix = [
    'reports/gh_ApplicationsOfDerivatives_Cloud_Ab1_20260131_1300.xlsx',
    'reports/gh_ApplicationsOfDerivatives_Cloud_Ab2_20260131_1300.xlsx'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"⚠️ 文件不存在: {filepath}")
        continue
    
    print(f"\n處理: {filepath}")
    
    # 讀取 Excel
    df = pd.read_excel(filepath)
    
    # 顯示修改前的統計
    print(f"修改前:")
    print(f"  is_crash=0: {(df['is_crash'] == 0).sum()}")
    print(f"  is_crash=1: {(df['is_crash'] == 1).sum()}")
    
    # 反轉 is_crash 值 (0 -> 1, 1 -> 0)
    df['is_crash'] = 1 - df['is_crash']
    
    # 顯示修改後的統計
    print(f"修改後:")
    print(f"  is_crash=0: {(df['is_crash'] == 0).sum()}")
    print(f"  is_crash=1: {(df['is_crash'] == 1).sum()}")
    
    # 備份原文件
    backup_path = filepath.replace('.xlsx', '_backup.xlsx')
    try:
        # 先保存新文件到臨時位置
        temp_path = filepath.replace('.xlsx', '_fixed.xlsx')
        df.to_excel(temp_path, index=False)
        print(f"  ✓ 已創建修正版文件: {temp_path}")
        print(f"  ⚠️ 請手動關閉 Excel 後，刪除原文件並重命名 _fixed.xlsx")
    except Exception as e:
        print(f"  ❌ 保存失敗: {e}")

print("\n✅ 修復完成！現在所有 Ablation 的 is_crash 語義統一:")
print("   is_crash = 0 → 成功執行（沒有崩潰）")
print("   is_crash = 1 → 執行失敗（發生崩潰）")
