# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): scripts/upgrade_db.py
功能說明 (Description): 資料庫科研規格升級腳本 (Database Upgrade Script)，負責擴充 
                       experiment_log 欄位、初始化消融實驗設定，並建立題目採樣 
                       execution_samples 表格。
執行語法 (Usage): 
    python scripts/upgrade_db.py
版本資訊 (Version): V1.1 (Full Research Schema Integration)
更新日期 (Date): 2026-01-18
維護團隊 (Maintainer): Math AI Project Team (Shih-Wei & Gemini)
=============================================================================
"""
import sqlite3
import os

def upgrade():
    # 確保資料庫目錄存在
    db_path = 'instance/kumon_math.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 連接到你的資料庫檔案
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 開始資料庫科研規格升級 (Total Phases: 5)...")

    # --------------------------------------------------------------------------
    # Phase 1: 擴充 experiment_log 欄位 (紀錄生成歷程用)
    # --------------------------------------------------------------------------
    try:
        # 1. 增加 'mode' 欄位 (紀錄 1-6 題型)
        cursor.execute("ALTER TABLE experiment_log ADD COLUMN mode INTEGER DEFAULT 0")
        print("✅ [Phase 1.1] 已新增 'mode' 欄位至 experiment_log")
    except sqlite3.OperationalError:
        print("⚠️ [Phase 1.1] 'mode' 欄位可能已存在，跳過。")

    try:
        # 2. 增加 'example_id' 欄位 (連結來源例題)
        cursor.execute("ALTER TABLE experiment_log ADD COLUMN example_id INTEGER")
        print("✅ [Phase 1.2] 已新增 'example_id' 欄位至 experiment_log")
    except sqlite3.OperationalError:
        print("⚠️ [Phase 1.2] 'example_id' 欄位可能已存在，跳過。")

    # --------------------------------------------------------------------------
    # Phase 2: 建立 ablation_settings 表格 (管理消融實驗變因)
    # --------------------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ablation_settings (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        use_regex BOOLEAN DEFAULT 0,
        use_ast BOOLEAN DEFAULT 0,
        description TEXT
    )
    """)
    print("✅ [Phase 2] 已建立 'ablation_settings' 表格")

    # --------------------------------------------------------------------------
    # Phase 3: 寫入實驗組對照數據
    # --------------------------------------------------------------------------
    ablation_data = [
        (1, 'Bare', 0, 0, '對照組：無任何修復機制 (Baseline)'),
        (2, 'Regex_Only', 1, 0, '實驗組 A：僅開啟正規表達式修復'),
        (3, 'Full_Healing', 1, 1, '實驗組 B：開啟 Regex + AST 完整自癒機制')
    ]
    # 使用 REPLACE 確保數據可重複執行而不出錯
    cursor.executemany("REPLACE INTO ablation_settings VALUES (?, ?, ?, ?, ?)", ablation_data)
    print("✅ [Phase 3] 已初始化實驗組設定數據")

    # --------------------------------------------------------------------------
    # Phase 4: 建立 execution_samples 表格 (採集題目數據用)
    # --------------------------------------------------------------------------
    # [說明]: 這是為了存放 research_runner 產出的 20 道題目與其圖片
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_id TEXT NOT NULL,
        mode INTEGER,                  -- 模式 (1-6)
        sample_index INTEGER,          -- 採樣序號 (1-20)
        question_text TEXT,            -- 題目文字
        correct_answer TEXT,           -- 正確答案
        image_base64 TEXT,             -- 圖片編碼
        is_crash INTEGER DEFAULT 0,    -- 程式是否崩潰
        is_logic_correct INTEGER DEFAULT 0, -- 閱卷自檢是否通過
        score_complexity INTEGER DEFAULT 0, -- 題目難度分數
        duration_seconds REAL,         -- 生成耗時
        ablation_id INTEGER,           -- 消融組別 ID
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✅ [Phase 4] 已建立 'execution_samples' 表格 (科研採樣專用)")

    # --------------------------------------------------------------------------
    # Phase 5: 存檔與關閉
    # --------------------------------------------------------------------------
    conn.commit()
    conn.close()
    print("🎉 資料庫科研規格升級完成！")

if __name__ == "__main__":
    upgrade()