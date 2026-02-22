# 🧬 Math-Master: Small but Precise (GEMINI.md)

**Project Title:** `Small but Precise: Outperforming Large Models through Engineered Self-Healing`

---

## 1. 核心實驗架構 (Experimental Framework)

### **Ab1 (Native)**
- **定義**: 原生 8B 模式。
- **邏輯**: 不提供 `@SKILL.md` 導引，測試模型的原生隨機性與錯誤率。

### **Ab2 (Scaffold)**
- **定義**: 鷹架引導模式。
- **邏輯**: 注入 `@SKILL.md` 規範，鎖定變數命名與 LaTeX 結構，測試語義對齊。

### **Ab3 (Healed)**
- **定義**: 完整自癒模式。
- **邏輯**: 開啟 **Active Healer** 監控與 **MCRI** 驗證，達成 100% 確定性。

---

## 2. 展示敘事邏輯 (The Live Show Narrative)

- **核心論點**: 證明小型在地化模型 (8B/14B) 透過工程干預 (Scaffold + Healer)，在特定任務上能超越雲端大模型。

- **視覺流程**:
    1. **捕捉輸入**: Handwriting (手寫) / Capture (截圖) / Text (文字).
    2. **基因辨識**: `🧬 Skill DNA Identification` (於右上角白框即時顯示).
    3. **平行對決**: Ab1 vs Ab3 實時生成對比，展示「自癒」過程。

- **算力展示**:
    - 展現 $O(\text{Inference})$ (雲端 API 網路延遲) 與 $O(1)$ (本地 CPU 高速執行) 的脫鉤優勢。

---

## 3. Agent 執行規範 (Strict Guidelines)

- **Codebase 感知**:
    - 生成任何程式碼前必須檢索 `@SKILL.md`，嚴格遵守 `is_first` 邏輯與渲染規範。

- **命名空間**:
    - 嚴格對照 `engine.py` 定義之 `RadicalOps`, `IntegerOps` 等封裝工具類別。禁止隨意自創函式名稱。

- **UI 色系規範 (Visual Identity)**:
    - 🟦 **Gemini (Cloud)**: `#4285F4`
    - 🟨 **Qwen-14B (Local)**: `#F4B400`
    - 🟩 **Qwen-8B (Local)**: `#0F9D58`
    - 🟧 **Active Healer**: `#FF6D00` (用於高亮修復歷史與警報)。

---

## 4. 安全與診斷攔截 (Safety & Diagnostics)

- **教學安全 (Math Safety)**:
    - **禁止** 分母為 0。
    - **禁止** 根號內出現負數。
    - **確保** 整數除法結果符合 K12 教學規範。

- **LaTeX 渲染安全**:
    - 強制使用 `\left(` 與 `\right)` 處理括號。
    - 確保所有數學符號通過渲染檢核，避免破圖。

- **數據回傳要求**:
    - 每次生成必須包含 `debug_meta` 物件，內含：`latency_ms` (延遲)、`healer_fix_count` (修復次數) 與 `MCRI_score` (可靠性評分)。