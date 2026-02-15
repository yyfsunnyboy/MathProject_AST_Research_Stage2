# MathProject_AST_Research 資料庫 Table Schema 詳細資料 (2026-01-17)

本文件詳細列出 MathProject_AST_Research 專案目前所有資料庫表格的 Schema、功能說明、Primary Key 及主要關聯程式。

**標頭資訊:**
- **日期**: 2026-01-17
- **版本**: V1.0
- **說明**: 依據 `models.py` (V2.0, 2026-01-13) 產生的最新資料庫結構文件。

---

## 1. users (使用者)
- **功能說明**: 儲存系統所有使用者的基本資料，包含學生、老師與管理員。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `app.py`, `core/routes.py`, `core/session.py`, `manage_roles.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 使用者唯一識別碼 | PK, Auto Increment |
| username | TEXT | 使用者名稱 | Unique, Not Null |
| password_hash | TEXT | 密碼雜湊值 | Not Null |
| email | TEXT | 電子郵件 | |
| role | TEXT | 角色權限 | Default: 'student' (admin, teacher) |
| created_at | DATETIME | 建立時間 | Default: Current Timestamp |

---

## 2. progress (學習進度)
- **功能說明**: 記錄使用者在特定技能 (Skill) 上的練習進度，包含連續答對題數與等級。
- **Primary Key**: `user_id`, `skill_id` (Composite PK)
- **主要使用程式**: `models.py`, `core/routes.py`, `core/exam_routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| user_id | INTEGER | 使用者 ID | FK -> users.id, PK |
| skill_id | TEXT | 技能 ID | PK |
| consecutive_correct | INTEGER | 連續答對次數 | Default: 0 |
| consecutive_wrong | INTEGER | 連續答錯次數 | Default: 0 |
| current_level | INTEGER | 目前等級 | Default: 1 |
| questions_solved | INTEGER | 已解決題數 | Default: 0 |
| last_practiced | DATETIME | 最後練習時間 | Default: Current Timestamp |

---

## 3. skills_info (技能資訊)
- **功能說明**: 定義所有數學技能的元數據，包含名稱、描述、分類及 AI 生成提示詞 (Prompt)。
- **Primary Key**: `skill_id`
- **主要使用程式**: `models.py`, `core/routes.py`, `core/data_importer.py`, `core/code_generator.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| skill_id | TEXT | 技能唯一識別碼 | PK (e.g., 'jh_Math1_...') |
| skill_en_name | TEXT | 英文名稱 | Not Null |
| skill_ch_name | TEXT | 中文名稱 | Not Null |
| category | TEXT | 分類 | |
| description | TEXT | 技能描述 | Not Null |
| input_type | TEXT | 輸入類型 | Default: 'text' |
| gemini_prompt | TEXT | Gemini Prompt | Not Null |
| consecutive_correct_required | INTEGER | 晉級所需連對數 | Default: 10 |
| is_active | BOOLEAN | 是否啟用 | Default: True |
| order_index | INTEGER | 排序索引 | Default: 0 |
| suggested_prompt_1 | TEXT | 推薦提問 1 | |
| suggested_prompt_2 | TEXT | 推薦提問 2 | |
| suggested_prompt_3 | TEXT | 推薦提問 3 | |

---

## 4. skill_gencode_prompt (技能生成代碼提示詞)
- **功能說明**: [v9.0 新增] 管理用於生成技能程式碼 (Code Generation) 的 Prompt 版本與策略，支援多版本與 A/B Test。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/code_generator.py`, `core/prompt_architect.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| skill_id | TEXT | 技能 ID | FK -> skills_info.skill_id |
| architect_model | TEXT | 設計者模型 | Default: 'human' |
| model_tag | TEXT | 模型標籤 | Default: 'default' |
| prompt_type | TEXT | 提示類型 | Default: 'standard' |
| prompt_strategy | TEXT | 提示策略 | Default: 'standard' |
| system_prompt | TEXT | 系統角色設定 | |
| user_prompt_template | TEXT | 使用者指令模板 | |
| prompt_content | TEXT | [MASTER_SPEC] 完整內容 | |
| creation_prompt_tokens | INTEGER | 建立時 Prompt Tokens | Cost Tracking |
| creation_completion_tokens | INTEGER | 建立時 Completion Tokens | Cost Tracking |
| creation_total_tokens | INTEGER | 建立時 Total Tokens | Cost Tracking |
| version | INTEGER | 版本號 | Default: 1 |
| is_active | BOOLEAN | 是否啟用 | Default: True |
| created_at | DATETIME | 建立時間 | Default: Current Timestamp |
| success_rate | FLOAT | 成功率 | Default: 0.0 |

---

## 5. skill_curriculum (技能課綱對照)
- **功能說明**: 建立技能與課綱 (年級、冊、章、節) 的多對多對照關係。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/data_importer.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| skill_id | TEXT | 技能 ID | FK -> skills_info.skill_id |
| curriculum | TEXT | 課綱 | Not Null |
| grade | INTEGER | 年級 | Not Null |
| volume | TEXT | 冊別 | Not Null |
| chapter | TEXT | 章節 | Not Null |
| section | TEXT | 小節 | Not Null |
| paragraph | TEXT | 段落 | |
| display_order | INTEGER | 顯示順序 | Default: 0 |
| difficulty_level | INTEGER | 難度等級 | Default: 1 |

---

## 6. skill_prerequisites (技能前置關係)
- **功能說明**: 定義技能之間的依賴關係 (前置技能 -> 後續技能)。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`, `scripts/auto_build_prerequisites.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| skill_id | TEXT | 技能 ID | FK -> skills_info.skill_id |
| prerequisite_id | TEXT | 前置技能 ID | FK -> skills_info.skill_id |

---

## 7. classes (班級)
- **功能說明**: 老師建立的班級，用於管理學生與指派任務。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 班級 ID | PK, Auto Increment |
| name | TEXT | 班級名稱 | Not Null |
| teacher_id | INTEGER | 導師 ID | FK -> users.id |
| class_code | TEXT | 班級邀請碼 | Unique, Not Null |
| created_at | DATETIME | 建立時間 | Default: Current Timestamp |

---

## 8. class_students (班級學生關聯)
- **功能說明**: 記錄學生加入班級的關聯表 (多對多)。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| class_id | INTEGER | 班級 ID | FK -> classes.id |
| student_id | INTEGER | 學生 ID | FK -> users.id |
| joined_at | DATETIME | 加入時間 | Default: Current Timestamp |

---

## 9. mistake_logs (錯誤日誌)
- **功能說明**: 詳細記錄使用者在練習過程中的錯誤，包含錯誤類型與 AI 建議。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| user_id | INTEGER | 使用者 ID | FK -> users.id |
| skill_id | TEXT | 技能 ID | |
| question_content | TEXT | 題目內容 | Not Null |
| user_answer | TEXT | 使用者答案 | Not Null |
| correct_answer | TEXT | 正確答案 | Not Null |
| error_type | TEXT | 錯誤類型 | |
| error_description | TEXT | 錯誤描述 | |
| improvement_suggestion | TEXT | 改進建議 | |
| created_at | DATETIME | 發生時間 | Default: Current Timestamp |

---

## 10. exam_analysis (測驗分析)
- **功能說明**: 記錄測驗 (如上傳考卷) 的分析結果，包含 OCR 與 AI 批改資訊。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/exam_analyzer.py`, `core/exam_routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| user_id | INTEGER | 使用者 ID | FK -> users.id |
| skill_id | TEXT | 技能 ID | FK -> skills_info.skill_id |
| curriculum | TEXT | 課綱 | |
| grade | INTEGER | 年級 | |
| volume | TEXT | 冊別 | |
| chapter | TEXT | 章節 | |
| section | TEXT | 小節 | |
| is_correct | BOOLEAN | 是否正確 | Not Null |
| error_type | TEXT | 錯誤類型 | |
| confidence | FLOAT | AI 信心分數 | |
| student_answer_latex | TEXT | 學生答案 LaTeX | |
| feedback | TEXT | 回饋與評語 | |
| image_path | TEXT | 題目圖片路徑 | Not Null |
| created_at | DATETIME | 分析時間 | Default: Current Timestamp |

---

## 11. mistake_notebook_entries (錯題本)
- **功能說明**: 學生個人的錯題本，儲存錯題照片、筆記與關聯技能。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| student_id | INTEGER | 學生 ID | FK -> users.id |
| exam_image_path | TEXT | 錯題圖片路徑 | |
| question_data | JSON | 題目資料 | |
| notes | TEXT | 個人筆記 | |
| skill_id | TEXT | 關聯技能 ID | FK -> skills_info.skill_id |
| created_at | DATETIME | 建立時間 | Default: Current Timestamp |

---

## 12. textbook_examples (課本例題)
- **功能說明**: 儲存從教科書導入的例題與詳解，作為 RAG (Retrieval-Augmented Generation) 的知識庫。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/textbook_processor.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| skill_id | TEXT | 關聯技能 ID | FK -> skills_info.skill_id |
| source_curriculum | TEXT | 來源課綱 | Not Null |
| source_volume | TEXT | 來源冊別 | Not Null |
| source_chapter | TEXT | 來源章節 | Not Null |
| source_section | TEXT | 來源小節 | Not Null |
| source_description | TEXT | 來源描述 | Not Null |
| source_paragraph | TEXT | 來源段落 | |
| problem_text | TEXT | 題目文字 | Not Null |
| problem_type | TEXT | 題目類型 | |
| correct_answer | TEXT | 正確答案 | |
| detailed_solution | TEXT | 詳細詳解 | |
| difficulty_level | INTEGER | 難度 | Default: 1 |

---

## 13. learning_diagnosis (學習診斷)
- **功能說明**: 儲存對學生學習狀況的綜合診斷報告 (雷達圖資料、AI 評語)。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/diagnosis_analyzer.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| student_id | INTEGER | 學生 ID | FK -> users.id |
| radar_chart_data | TEXT | 雷達圖資料 (JSON) | Not Null |
| ai_comment | TEXT | AI 評語 | |
| recommended_unit | TEXT | 推薦加強單元 | |
| created_at | DATETIME | 診斷時間 | Default: Current Timestamp |

---

## 14. system_settings (系統設定)
- **功能說明**: 儲存全域系統設定值 (Key-Value 對)。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`, `app.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| key | TEXT | 設定鍵值 | Unique, Not Null |
| value | TEXT | 設定內容 | Not Null |
| description | TEXT | 設定說明 | |
| updated_at | DATETIME | 更新時間 | Default: Current Timestamp |

---

## 15. experiment_log (實驗日誌)
- **功能說明**: [v9.0 新增] 用於科展或開發測試，詳細記錄程式碼生成的效能指標、Token 消耗與修復過程。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/code_generator.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| timestamp | DATETIME | 實驗時間 | Default: Current Timestamp |
| skill_id | TEXT | 測試技能 | Not Null |
| ai_provider | TEXT | AI 提供者 | |
| model_name | TEXT | 模型名稱 | |
| duration_seconds | FLOAT | 生成耗時 (秒) | |
| input_length | INTEGER | Prompt 字數 | Source Metric |
| output_length | INTEGER | 代碼字數 | Source Metric |
| is_success | BOOLEAN | 是否成功 | Default: 0 |
| syntax_error_initial | TEXT | 原始錯誤訊息 | |
| ast_repair_triggered | BOOLEAN | 是否觸發修復 | Default: 0 |
| cpu_usage | FLOAT | CPU 使用率 | System Metric |
| ram_usage | FLOAT | RAM 使用率 | System Metric |
| experiment_batch | TEXT | 實驗批次 | |
| prompt_strategy | TEXT | 提示策略 | |
| prompt_version | INTEGER | Prompt 版本 ID | |
| error_category | TEXT | 錯誤分類 | |
| regex_fix_count | INTEGER | Regex 修復次數 | Default: 0 |
| logic_fix_count | INTEGER | 邏輯修復次數 | Default: 0 |
| ast_repair_count | INTEGER | AST 修復次數 | Default: 0 |
| prompt_tokens | INTEGER | 輸入 Tokens | Default: 0 |
| completion_tokens | INTEGER | 輸出 Tokens | Default: 0 |
| total_tokens | INTEGER | 總 Tokens | Default: 0 |
| code_complexity | INTEGER | 程式碼複雜度 | Default: 0 |
| model_size_class | TEXT | 模型大小分類 | '7B', '14B', 'Cloud' |
| prompt_level | TEXT | 提示等級 | 'Bare', 'Engineered', 'Self-Healing' |
| raw_response | TEXT | LLM 原始輸出 | |
| final_code | TEXT | 最終修復代碼 | |
| score_syntax | FLOAT | 語法分 | Default: 0.0 |
| score_math | FLOAT | 邏輯分 | Default: 0.0 |
| score_visual | FLOAT | 視覺分 | Default: 0.0 |
| healing_duration | FLOAT | 自癒耗時 | |
| is_executable | BOOLEAN | 是否可執行成功 | |
| ablation_id | INTEGER | 對應實驗組 ID | |
| missing_imports_fixed | TEXT | 紀錄補上的庫 | |
| resource_cleanup_flag | BOOLEAN | 資源釋放標記 | |

---

## 16. questions (題目庫)
- **功能說明**: 儲存系統內建或生成的題目內容。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/data_importer.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 題目 ID | PK, Auto Increment |
| skill_id | TEXT | 技能 ID | Not Null |
| content | JSON | 題目內容 | Not Null (含選項、答案) |
| difficulty_level | INTEGER | 難度 | Default: 1 |
| created_at | DATETIME | 建立時間 | Default: Current Timestamp |

---

## 17. quiz_attempts (作答紀錄)
- **功能說明**: 記錄使用者對特定題目的作答嘗試結果。
- **Primary Key**: `id`
- **主要使用程式**: `models.py`, `core/routes.py`
- **Schema**:

| 欄位名稱 | 資料類型 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | 流水號 | PK, Auto Increment |
| user_id | INTEGER | 使用者 ID | FK -> users.id |
| question_id | INTEGER | 題目 ID | FK -> questions.id |
| user_answer | TEXT | 使用者答案 | |
| is_correct | BOOLEAN | 是否正確 | Default: False |
| duration_seconds | FLOAT | 作答耗時 (秒) | |
| timestamp | DATETIME | 作答時間 | Default: Current Timestamp |
