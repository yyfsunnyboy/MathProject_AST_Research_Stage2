import sqlite3
import os
import sys

# 資料庫路徑配置
DB_PATH = os.path.join('instance', 'kumon_math.db')

# 定義要新增的欄位結構 (Table -> List of (ColumnName, Type))
SCHEMA_UPDATES = {
    'experiment_runs': [
        ('score_program_total', 'FLOAT'),    # 程式價值總分 (Max 50)
        ('score_math_total', 'FLOAT'),       # 數學價值總分 (Max 50)
        ('score_l5_architecture', 'FLOAT'),  # L5 架構分 (Max 20)
        ('avg_l4_4_mqi', 'FLOAT')            # L4.4 數學品質指標 (Max 10)
    ],
    'evaluation_items': [
        ('score_l4_4_mqi', 'REAL'),          # MQI 單題分數
        ('score_math_total', 'REAL'),        # 單題數學總分
        ('score_math_quality', 'REAL'),      # 單題品質分
        ('score_math_difficulty', 'REAL')    # 單題難度分
    ],
    'ablation_summary': [
        ('mean_program_total', 'FLOAT'),     # 平均程式價值
        ('mean_math_total', 'FLOAT'),        # 平均數學價值
        ('mean_l5_architecture', 'FLOAT'),   # 平均 L5 分數
        ('mean_l4_mqi', 'FLOAT')             # 平均 MQI 分數
    ]
}

def migrate():
    print("="*70)
    print("🛠️  MCRI V6.0 資料庫遷移腳本 (Database Migrator)")
    print(f"📂 目標資料庫: {os.path.abspath(DB_PATH)}")
    print("="*70)
    print("🛑 [警告] 請確保您已經備份了 experiment_results.db！")
    print("   若尚未備份，請立即中止程式 (Ctrl+C)，備份後再重新執行。")
    print("="*70)
    
    # 簡單確認檔案存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 錯誤: 在當前目錄下找不到 '{DB_PATH}'。")
        print("   請確認您在正確的目錄 (e:\\Python\\MathProject_AST_Research) 執行腳本。")
        return

    try:
        # 連接資料庫
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        added_count = 0
        total_checks = 0
        
        for table, columns in SCHEMA_UPDATES.items():
            print(f"\n🔍 正在掃描表格 [{table}]...")
            
            # 1. 檢查表格是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                print(f"   ⚠️  表格 '{table}' 不存在，跳過。")
                continue

            # 2. 獲取現有欄位清單
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            # 3. 逐一檢查並新增欄位
            for col_name, col_type in columns:
                total_checks += 1
                if col_name not in existing_cols:
                    try:
                        alter_query = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                        cursor.execute(alter_query)
                        print(f"   ✅ 新增欄位: {col_name:<25} ({col_type})")
                        added_count += 1
                    except sqlite3.Error as e:
                        print(f"   ❌ 新增欄位失敗 {col_name}: {e}")
                else:
                    print(f"   ⚪ 已存在:   {col_name}")

        # 提交變更
        conn.commit()
        conn.close()
        
        print("\n" + "="*70)
        print("🎉 遷移作業完成！")
        if added_count > 0:
            print(f"📊 統計: 成功新增 {added_count} 個欄位 / 共檢查 {total_checks} 個項目。")
            print("🚀 資料庫已準備好支援 MCRI V6.0 評分系統。")
        else:
            print("✨ 資料庫結構已經是最新版本 (MCRI V6.0)，無需變更。")
        print("="*70)

    except sqlite3.Error as e:
        print(f"\n❌ SQLite 錯誤: {e}")
    except Exception as e:
        import traceback
        print(f"\n❌ 未預期的錯誤: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    migrate()
