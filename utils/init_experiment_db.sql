-- =============================================================================
-- 檔案名稱 (File Name): init_experiment_db.sql
-- 功能說明 (Description): MCRI V4.2 實驗資料表定義，支援 252 次實驗的結果記錄
-- 版本資訊 (Version): V1.1
-- 更新日期 (Date): 2026-02-02
-- 維護團隊 (Maintainer): Math AI Project Team
-- 更新內容: 新增 ablation_summary 彙總統計表
-- =============================================================================

-- =============================================================================
-- 🌟 最外層彙總表：ablation_summary（統計表，預期 9 筆）
-- 功能：記錄每個技能在不同配置下的統計彙總（跨 5 個 sample）
-- 設計理念：用於論文撰寫的統計推論，包含信賴區間與顯著性檢定
-- =============================================================================

CREATE TABLE IF NOT EXISTS ablation_summary (
    -- ========== 主鍵與識別 ==========
    summary_id TEXT PRIMARY KEY,  -- UUID，唯一識別碼
    skill_name VARCHAR(100) NOT NULL,  -- gh_ApplicationsOfDerivatives
    ablation_id INTEGER NOT NULL CHECK (ablation_id IN (1, 2, 3)),  -- 1=Bare, 2=Eng, 3=Healer
    model_name VARCHAR(50) NOT NULL,  -- qwen2.5-coder:14b
    
    -- ========== 統計數據 ==========
    sample_count INTEGER NOT NULL DEFAULT 5,  -- 樣本數（固定 5）
    total_runs INTEGER NOT NULL DEFAULT 100,  -- 總執行次數（5 sample × 20 rep）
    
    -- ========== MCRI 總分統計 ==========
    mean_mcri_total FLOAT NOT NULL,  -- 5 個 sample 的 avg_mcri_total 平均值
    std_mcri_total FLOAT NOT NULL,  -- 標準差（sample std, ddof=1）
    ci95_lower FLOAT NOT NULL,  -- 95% 信賴區間下界（t 分布）
    ci95_upper FLOAT NOT NULL,  -- 95% 信賴區間上界（t 分布）
    
    -- ========== 關鍵維度統計 ==========
    mean_l3_external FLOAT,  -- L3.2 外在強健性平均（跨 5 sample）
    mean_l4_numeric FLOAT,  -- L4.1 數值友善性平均（跨 5 sample）
    
    -- ========== 顯著性檢定 ==========
    p_value_vs_ab1 FLOAT,  -- 與 Ab1 的 t-test p-value（雙尾檢定）
    notes TEXT  -- 備註（如「Ab3 顯著優於 Ab1, p<0.001」）
);

-- 建立唯一約束（每個技能 × 配置 × 模型只能有一筆）
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_summary 
ON ablation_summary(skill_name, ablation_id, model_name);

-- 建立索引（加速查詢）
CREATE INDEX IF NOT EXISTS idx_summary_skill 
ON ablation_summary(skill_name);

CREATE INDEX IF NOT EXISTS idx_summary_ablation 
ON ablation_summary(ablation_id);

CREATE INDEX IF NOT EXISTS idx_summary_mean_mcri 
ON ablation_summary(mean_mcri_total DESC);

-- =============================================================================
-- 主表：experiment_runs（總結表，預期 135 筆）
-- 功能：記錄每次實驗的執行配置 + L1/L2 固定分數 + L3/L4 平均分
-- 設計理念：一個 run 代表「一個技能 × 一個配置 × 一次完整測試（20次採樣）」
-- =============================================================================

CREATE TABLE IF NOT EXISTS experiment_runs (
    -- ========== 主鍵與識別 ==========
    run_id TEXT PRIMARY KEY,  -- UUID，唯一識別碼
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 執行時間
    
    -- ========== 實驗配置 ==========
    model_name VARCHAR(50) NOT NULL,  -- qwen-14b / gemini-flash 等
    skill_name VARCHAR(100) NOT NULL,  -- gh_ApplicationsOfDerivatives
    ablation_id INTEGER NOT NULL CHECK (ablation_id IN (1, 2, 3)),  -- 1=Bare, 2=Eng, 3=Healer
    sample_index INTEGER NOT NULL CHECK (sample_index >= 1 AND sample_index <= 5),  -- 1~5
    
    -- ========== 版本資訊 ==========
    code_commit_hash VARCHAR(40) NOT NULL,  -- git commit hash
    python_version VARCHAR(20) NOT NULL,  -- Python 版本（如 3.9.13）
    mcri_version VARCHAR(20) NOT NULL DEFAULT 'V4.2',  -- MCRI 評估系統版本
    
    -- ========== 生成參數 ==========
    model_temperature FLOAT NOT NULL DEFAULT 0.7,  -- 生成溫度
    
    -- ========== 執行統計 ==========
    repetitions_planned INTEGER NOT NULL DEFAULT 20,  -- 預定測試次數（固定 20）
    repetitions_completed INTEGER NOT NULL,  -- 實際完成次數（可能 < 20 如果 crash）
    fail_count INTEGER NOT NULL DEFAULT 0,  -- 完全失敗次數（syntax error / timeout）
    pass_rate FLOAT CHECK (pass_rate >= 0.0 AND pass_rate <= 1.0),  -- 通過率（0.0~1.0）
    avg_exec_time FLOAT,  -- 平均執行秒數（排除 timeout）
    
    -- ========== L1. 工程基石（20分）- 固定值 ==========
    score_l1_total INTEGER CHECK (score_l1_total >= 0 AND score_l1_total <= 20),
    score_l1_1_syntax INTEGER CHECK (score_l1_1_syntax >= 0 AND score_l1_1_syntax <= 10),  -- 語法安全
    score_l1_2_runtime INTEGER CHECK (score_l1_2_runtime >= 0 AND score_l1_2_runtime <= 10),  -- 執行穩定
    
    -- ========== L2. 資料衛生（20分）- 固定值 ==========
    score_l2_total INTEGER CHECK (score_l2_total >= 0 AND score_l2_total <= 20),
    score_l2_1_contract INTEGER CHECK (score_l2_1_contract >= 0 AND score_l2_1_contract <= 10),  -- 介面契約
    score_l2_2_purity INTEGER CHECK (score_l2_2_purity >= 0 AND score_l2_2_purity <= 10),  -- 格式純淨
    
    -- ========== L3. 評測公平（30分）- 平均值（20次採樣平均）==========
    avg_l3_total FLOAT CHECK (avg_l3_total >= 0.0 AND avg_l3_total <= 30.0),
    avg_l3_1_internal FLOAT CHECK (avg_l3_1_internal >= 0.0 AND avg_l3_1_internal <= 15.0),  -- 內在一致平均
    avg_l3_2_external FLOAT CHECK (avg_l3_2_external >= 0.0 AND avg_l3_2_external <= 15.0),  -- 外在強健平均
    
    -- ========== L4. 教學有效（30分）- 平均值（20次採樣平均）==========
    avg_l4_total FLOAT CHECK (avg_l4_total >= 0.0 AND avg_l4_total <= 30.0),
    avg_l4_1_numeric FLOAT CHECK (avg_l4_1_numeric >= 0.0 AND avg_l4_1_numeric <= 15.0),  -- 數值友善平均
    avg_l4_2_visual FLOAT CHECK (avg_l4_2_visual >= 0.0 AND avg_l4_2_visual <= 15.0),  -- 視覺可讀平均
    
    -- ========== 總分（100分）==========
    avg_mcri_total FLOAT CHECK (avg_mcri_total >= 0.0 AND avg_mcri_total <= 100.0),  -- 平均總分
    
    -- ========== 檔案與備註 ==========
    source_code_path VARCHAR(255) NOT NULL,  -- 原始檔案路徑（如 skills/gh_ApplicationsOfDerivatives_14b_Ab1.py）
    notes TEXT  -- 備註（如「Ab2 Timeout」、「發現 infinite loop」等）
);

-- 建立複合索引（加速查詢）
CREATE INDEX IF NOT EXISTS idx_runs_model_skill_ab 
ON experiment_runs(model_name, skill_name, ablation_id);

CREATE INDEX IF NOT EXISTS idx_runs_timestamp 
ON experiment_runs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_runs_mcri_total 
ON experiment_runs(avg_mcri_total DESC);

-- =============================================================================
-- 附表：evaluation_items（明細表，預期 2,700 筆 = 135 runs × 20 repetitions）
-- 功能：記錄每次採樣的 L3/L4 單次分數 + 產出內容
-- 設計理念：保留原始產出與 debug 資訊，用於分析失敗模式
-- =============================================================================

CREATE TABLE IF NOT EXISTS evaluation_items (
    -- ========== 主鍵與關聯 ==========
    item_id TEXT PRIMARY KEY,  -- UUID，明細 ID
    run_id TEXT NOT NULL,  -- 外鍵，關聯 experiment_runs
    repetition_index INTEGER NOT NULL CHECK (repetition_index >= 1 AND repetition_index <= 20),  -- 1~20
    
    -- ========== 產出內容（用於 L2/L4 檢查）==========
    generated_question TEXT,  -- 題目內容（question_text）
    generated_answer TEXT,  -- 系統產生的 answer（通常空白）
    generated_correct_answer TEXT,  -- 系統產生的 correct_answer（用於比對）
    
    -- ========== 執行狀態（用於 L1 判斷）==========
    status VARCHAR(20) NOT NULL CHECK (status IN ('Success', 'Fail', 'Timeout')),
    error_log TEXT,  -- 錯誤訊息（截斷至 1000 字元）
    exec_time_ms FLOAT,  -- 執行時間（毫秒）
    
    -- ========== 統計控制 ==========
    included_in_avg BOOLEAN NOT NULL DEFAULT TRUE,  -- 是否計入平均分（排除 timeout）
    
    -- ========== L3. 評測公平（30分）- 單次分數 ==========
    score_l3_total INTEGER CHECK (score_l3_total >= 0 AND score_l3_total <= 30),
    score_l3_1_internal INTEGER CHECK (score_l3_1_internal >= 0 AND score_l3_1_internal <= 15),  -- 內在一致性
    score_l3_2_external INTEGER CHECK (score_l3_2_external >= 0 AND score_l3_2_external <= 15),  -- 外在強健性
    
    -- ========== L4. 教學有效（30分）- 單次分數 ==========
    score_l4_total INTEGER CHECK (score_l4_total >= 0 AND score_l4_total <= 30),
    score_l4_1_numeric INTEGER CHECK (score_l4_1_numeric >= 0 AND score_l4_1_numeric <= 15),  -- 數值友善
    score_l4_2_visual INTEGER CHECK (score_l4_2_visual >= 0 AND score_l4_2_visual <= 15),  -- 視覺可讀
    
    -- ========== L3.2 外在強健性測試細節 ==========
    student_input_test TEXT,  -- 這次測試用的學生輸入（JSON 格式，如 ["2x", "f'(x)=2x", "2*x"]）
    student_input_result TEXT,  -- 測試結果（JSON 格式，如 [true, true, false]）
    
    -- 外鍵約束
    FOREIGN KEY (run_id) REFERENCES experiment_runs(run_id) ON DELETE CASCADE
);

-- 建立索引（加速查詢）
CREATE INDEX IF NOT EXISTS idx_items_run_id 
ON evaluation_items(run_id);

CREATE INDEX IF NOT EXISTS idx_items_status 
ON evaluation_items(status);

CREATE INDEX IF NOT EXISTS idx_items_included 
ON evaluation_items(included_in_avg);

-- =============================================================================
-- 視圖（View）：快速查詢
-- =============================================================================

-- 視圖 1：每個配置的平均表現
CREATE VIEW IF NOT EXISTS v_avg_by_config AS
SELECT 
    model_name,
    skill_name,
    ablation_id,
    COUNT(*) AS total_runs,
    AVG(avg_mcri_total) AS avg_mcri,
    AVG(pass_rate) AS avg_pass_rate,
    AVG(score_l1_total) AS avg_l1,
    AVG(score_l2_total) AS avg_l2,
    AVG(avg_l3_total) AS avg_l3,
    AVG(avg_l4_total) AS avg_l4
FROM experiment_runs
GROUP BY model_name, skill_name, ablation_id;

-- 視圖 2：失敗模式統計
CREATE VIEW IF NOT EXISTS v_failure_modes AS
SELECT 
    r.run_id,
    r.skill_name,
    r.ablation_id,
    COUNT(CASE WHEN i.status = 'Fail' THEN 1 END) AS syntax_errors,
    COUNT(CASE WHEN i.status = 'Timeout' THEN 1 END) AS timeouts,
    COUNT(CASE WHEN i.status = 'Success' THEN 1 END) AS successes
FROM experiment_runs r
LEFT JOIN evaluation_items i ON r.run_id = i.run_id
GROUP BY r.run_id;

-- =============================================================================
-- 觸發器（Trigger）：自動計算平均分
-- =============================================================================

-- 當插入/更新 evaluation_items 時，自動更新 experiment_runs 的平均分
CREATE TRIGGER IF NOT EXISTS trg_update_avg_scores
AFTER INSERT ON evaluation_items
BEGIN
    UPDATE experiment_runs
    SET 
        avg_l3_total = (
            SELECT AVG(score_l3_total) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_l3_1_internal = (
            SELECT AVG(score_l3_1_internal) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_l3_2_external = (
            SELECT AVG(score_l3_2_external) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_l4_total = (
            SELECT AVG(score_l4_total) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_l4_1_numeric = (
            SELECT AVG(score_l4_1_numeric) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_l4_2_visual = (
            SELECT AVG(score_l4_2_visual) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND included_in_avg = TRUE
        ),
        avg_mcri_total = (
            SELECT 
                score_l1_total + score_l2_total + 
                AVG(CASE WHEN i.included_in_avg THEN i.score_l3_total ELSE NULL END) + 
                AVG(CASE WHEN i.included_in_avg THEN i.score_l4_total ELSE NULL END)
            FROM experiment_runs r
            LEFT JOIN evaluation_items i ON r.run_id = i.run_id
            WHERE r.run_id = NEW.run_id
        ),
        repetitions_completed = (
            SELECT COUNT(*) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id
        ),
        fail_count = (
            SELECT COUNT(*) 
            FROM evaluation_items 
            WHERE run_id = NEW.run_id AND status IN ('Fail', 'Timeout')
        ),
        pass_rate = (
            SELECT 1.0 * COUNT(CASE WHEN status = 'Success' THEN 1 END) / COUNT(*)
            FROM evaluation_items 
            WHERE run_id = NEW.run_id
        )
    WHERE run_id = NEW.run_id;
END;

-- =============================================================================
-- 資料完整性檢查
-- =============================================================================

-- 約束：每個 run 的 sample_index 不能重複
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_run_config 
ON experiment_runs(model_name, skill_name, ablation_id, sample_index);

-- 約束：每個 run 的 repetition_index 不能重複
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_item_repetition 
ON evaluation_items(run_id, repetition_index);

-- =============================================================================
-- 註釋與使用範例
-- =============================================================================

/*
=== 使用範例 ===

1. 插入新實驗：
INSERT INTO experiment_runs (
    run_id, model_name, skill_name, ablation_id, sample_index,
    code_commit_hash, python_version, source_code_path
) VALUES (
    'uuid-1234', 'qwen-14b', 'gh_ApplicationsOfDerivatives', 1, 1,
    'abc123def', '3.9.13', 'skills/gh_ApplicationsOfDerivatives_14b_Ab1.py'
);

2. 插入評估結果（自動觸發平均分計算）：
INSERT INTO evaluation_items (
    item_id, run_id, repetition_index, status,
    score_l3_total, score_l4_total
) VALUES (
    'item-1', 'uuid-1234', 1, 'Success', 25, 28
);

3. 查詢 Ab3 的平均表現：
SELECT * FROM v_avg_by_config WHERE ablation_id = 3;

4. 匯出 CSV：
.mode csv
.headers on
.output experiment_runs.csv
SELECT * FROM experiment_runs;
.output evaluation_items.csv
SELECT * FROM evaluation_items;

5. 匯入 CSV：
.mode csv
.import experiment_runs.csv experiment_runs
.import evaluation_items.csv evaluation_items
*/
