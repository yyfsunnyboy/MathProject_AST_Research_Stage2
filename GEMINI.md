# Math-Master 實驗室指令集

## 專案核心 (Ivan's Lab)
- **領域**: K12 數學出題 (整數、分數、根式)。
- **消融組別**: Ab1 (Native), Ab2 (Scaffold), Ab3 (Healed)。
- **指標**: MCRI Score = Program(50) + Math(50)。

## Agent 指令規範
- `@codebase`: 分析數據時必須對照我的 CSV 檔案。
- `色系規範`: Gemini (藍), Qwen-14B (黃), Qwen-8B (綠)。
- `Healer 邏輯`: 如果程式碼報錯，優先檢查 LaTeX 語法。