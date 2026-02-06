#!/usr/bin/env python3
"""
遷移腳本：在 kumon_math.db 中新增 healer_events 表

特性：
- 記錄每次 Healer 修復事件的詳細信息
- 包含修復前後的代碼片段（限制長度避免 DB 膨脹）
- 追蹤修復耗時（效能分析）
- 支持分階段分析（Pre-Process, Regex_Healer, AST_Healer 等）
"""

import sqlite3
import sys
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'instance' / 'kumon_math.db'

def migrate_healer_events():
    """新增 healer_events 表"""
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        print("=" * 80)
        print("📊 開始遷移 healer_events 表")
        print("=" * 80)
        
        # 創建 healer_events 表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS healer_events (
            event_id VARCHAR(36) PRIMARY KEY,
            run_id VARCHAR(36) NOT NULL,
            
            -- 介入階段與類型
            stage VARCHAR(50) NOT NULL,
            pattern_id VARCHAR(100),
            
            -- 手術前後對比 (Evidence)
            original_snippet TEXT,
            healed_snippet TEXT,
            
            -- 結果與追蹤
            is_success BOOLEAN DEFAULT 1,
            fix_duration_ms INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            -- 外鍵
            FOREIGN KEY (run_id) REFERENCES experiment_runs(run_id)
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("  ✅ healer_events 表建立成功")
        
        # 創建索引
        index_sqls = [
            "CREATE INDEX IF NOT EXISTS idx_healer_run ON healer_events(run_id);",
            "CREATE INDEX IF NOT EXISTS idx_healer_stage ON healer_events(stage);"
        ]
        
        for idx_sql in index_sqls:
            cursor.execute(idx_sql)
        conn.commit()
        print("  ✅ 索引建立成功")
        
        # 驗證表結構
        cursor.execute("PRAGMA table_info(healer_events);")
        columns = cursor.fetchall()
        
        print("\n📋 驗證表結構...")
        print("=" * 80)
        print(f"✅ healer_events 現有欄位數: {len(columns)}")
        print("\n欄位列表:")
        for i, col in enumerate(columns, 1):
            # PRAGMA table_info 返回: (cid, name, type, notnull, dflt_value, pk)
            col_id, col_name, col_type, not_null, default, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            print(f"  {i:2d}. {col_name:25s} {col_type:15s} {nullable}")
        
        # 驗證外鍵
        cursor.execute("PRAGMA foreign_key_list(healer_events);")
        fks = cursor.fetchall()
        if fks:
            print(f"\n✅ 外鍵設定: {len(fks)} 個")
            for fk in fks:
                print(f"  - {fk[3]} -> {fk[2]}.{fk[4]}")
        
        # 驗證索引
        cursor.execute("PRAGMA index_list(healer_events);")
        indexes = cursor.fetchall()
        if indexes:
            print(f"\n✅ 索引設定: {len(indexes)} 個")
            for idx in indexes:
                idx_name = idx[1]
                print(f"  - {idx_name}")
        
        # 檢查資料行數
        cursor.execute("SELECT COUNT(*) FROM healer_events;")
        row_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 80)
        print(f"✅ healer_events 表中的數據行數: {row_count}")
        print("=" * 80)
        
        # 驗證與 experiment_runs 的關係
        print("\n📊 關聯驗證:")
        cursor.execute("SELECT COUNT(*) FROM experiment_runs;")
        exp_count = cursor.fetchone()[0]
        print(f"  - experiment_runs 表: {exp_count} 行")
        print(f"  - healer_events 表: {row_count} 行 (待填充)")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ 遷移完成！healer_events 表已成功建立")
        print("=" * 80)
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ 資料庫錯誤: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未預期的錯誤: {e}")
        return False

if __name__ == '__main__':
    success = migrate_healer_events()
    sys.exit(0 if success else 1)
