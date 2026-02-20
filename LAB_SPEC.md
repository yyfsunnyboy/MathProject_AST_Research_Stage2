# Math-Master 實驗專案規範 (Teacher Yeh's Lab)

## 1. 核心實驗架構 (Ablation Groups)
- **Ab1 (Native)**: 裸生成，不提供任何提示詞引導。用於測試模型的原生數學與程式能力。
- **Ab2 (Scaffold)**: 鷹架引導。注入「逆向生成算法」Golden Prompt，規範生成的變數命名與邏輯結構。
- **Ab3 (Healed)**: 自癒模式。在 Ab2 基礎上開啟 Active Healer 監控，自動修復 LaTeX 與語法微疵。

## 2. 數據指標 (Metrics)
- **MCRI Score**: 總分 (100)，由 Program (50) + Math (50) 組成。
- **難度等級**: L1 (基礎), L2 (進階), L3 (複雜混合運算)。

## 3. 出題技術規範
- 統一使用 `pandas` 處理實驗數據。
- 繪圖色系：Gemini(藍)、Qwen-14B(黃)、Qwen-8B(綠)。
- 程式碼產出必須符合：LaTeX 數學式正確性、SymPy 可驗證性。