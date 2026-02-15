# 📑 專案文檔總索引

**最後更新**: 2026-02-15  
**涵蓋範圍**: 專案管理、科研報告、技術文檔、部署歸檔

---

## 🆕 最新更新（2026-02-15）

### 🚀 系統架構現代化 (Modernization)
1.  **Thinking Models Integration**: 正式引入 Qwen 3 14B 模型，具備長鏈推理能力。
2.  **Stub Injection Technology**: 創新的「Prompt 瘦身 + 執行期注入」架構。
3.  **根目錄清理**: 完成大規模清理，專案結構達到競賽級標準。

### 📋 關鍵報告歸檔
所有歷史部署報告已移動至 `docs/reports/`，保持根目錄清爽：
- **[docs/reports/](docs/reports/)**: 包含所有 V4.x, V2.x 的部署歷史與技術驗證報告。

---

## 📂 核心文檔清單

### 🎯 快速入門與核心文件

| 文檔 | 用途 | 推薦對象 | 閱讀時間 |
|------|------|---------|---------|
| **[README.md](README.md)** | 專案首頁 | 所有人 | 5 分鐘 |
| **[DOCUMENT_INDEX.md](DOCUMENT_INDEX.md)** | 本索引 | 所有人 | 3 分鐘 |
| **[docs/競賽文件/00_核心報告/MathProject_Final_Integration_Report.md](docs/競賽文件/00_核心報告/MathProject_Final_Integration_Report.md)** | **總結成果報告** (Executive Summary) | 評審/大眾 | 10 分鐘 |
| **[docs/競賽文件/EXPERIMENT_JOURNAL.md](docs/競賽文件/EXPERIMENT_JOURNAL.md)** | **實驗流水日誌** (Development Log) | 研究員 | 15 分鐘 |

---

### 🔬 實驗設計與科研成果

#### 🧬 [MathProject_Experiment_Design_and_Analysis.md](docs/競賽文件/03_實驗過程/MathProject_Experiment_Design_and_Analysis.md)
*   **整合報告**: 涵蓋 3x3 實驗設計、MCRI 評測標準、Ab1/2/3 比較。
*   **關鍵發現**: 包含了 Prompt 層級衝突與 Healer 必要性的完整論證。
*   *(原 `3x3實驗設計...md` 與 `evaluate_mcri...md` 已整合於此)*

---

### 💻 技術架構白皮書

#### 📚 [MathProject_Technical_Architecture.md](docs/競賽文件/02_技術細節/MathProject_Technical_Architecture.md)
*   **整合報告**: 涵蓋系統架構、資料庫 Schema、CodeGen Pipeline、Healer 機制。
*   **最新技術**: 包含 **Stub Injection** (V47.16) 詳細說明。
*   *(原 `系統架構.md`, `Schema`, `code_generator...md` 已整合於此)*

---

### 🗄️ 歷史歸檔 (docs/競賽文件/99_歷史歸檔/)

所有原始的開發筆記與詳細技術文檔已歸檔至此，僅供查閱細節：
*   `📚evaluate_mcri_MCRI評估系統進展報告.md`
*   `系統架構.md`, `資料庫Table_Schema_20260117.md`
*   `📚code_generator代碼生成與修復技術詳解.md`
*   `專案速查.md`, `🧬3x3實驗設計詳解與過程.md`
*   `📋ROOT_DIRECTORY_CLEANUP_REPORT.md`

---

### 🗄️ 歷史歸檔 (docs/reports/ & 99_歷史歸檔/)

以下文件已歸檔，僅供歷史參考：
*   **[docs/競賽文件/99_歷史歸檔/📋ROOT_DIRECTORY_CLEANUP_REPORT.md](docs/競賽文件/99_歷史歸檔/📋ROOT_DIRECTORY_CLEANUP_REPORT.md)**
*   `GOLD_MEDAL_QUICK_REFERENCE.md` (in docs/reports/)
*   `QUICK_REFERENCE_TWO_LAYER_DEFENSE.md` (in docs/reports/)

---

## ✅ 系統操作指南

### 生成 Golden Prompt (Mode 4)
```bash
python scripts/sync_skills_files.py
# 選擇 [4] Save Golden Prompt
```

### 生成技能代碼 (Mode 2)
```bash
python scripts/sync_skills_files.py
# 選擇 [2] Golden Prompt -> 選擇 [2] Ab2 (Engineered)
```

### 執行 MCRI 評測
```bash
python scripts/evaluate_mcri.py --skill_id [SKILL_ID]
```

---

*Built for Science Fair 2026*
