# 🎭 Math-Master Live Show 劇本邏輯 (SHOWREEL_LOGIC.md)

**核心宗旨**: 展示透過工程干預（Engineering Intervention）如何讓小型在地模型在嚴苛的教育任務中達到 100% 穩定度。

---

## 1. 技術管線視覺化 (The Technical Pipeline)

### **第一幕：感知層 (Multimodal Input - Gemini Cloud)**
- **動作**: 演示 Gemini 辨識手寫照片或螢幕截圖，並由 Gemini 鎖定相關技能。
- **視覺亮點**: 
    - 右上角 `🧬 Skill DNA Identification` 區塊即時跳動。
    - 顯示 `DNA Sequence` (Gemini 辨識過程) 與最後鎖定的 `Target Skill`。

### **第二幕：基因注入層 (Prompt Scaffold Injection)**
- **動作**: 展示系統如何自動檢索 `@SKILL.md` 並將「教學約束」注入 Prompt。
- **核心敘事**: 強調這不是在「問 AI 問題」，而是在對 AI 進行「邏輯導引」。

### **第三幕：原始推論層 (Raw Inference - Ab1)**
- **動作**: 實時串流顯示 Qwen 3 8B 在無導引下的思考與代碼產出。
- **視覺亮點**: 刻意展示原生代碼中可能的 LaTeX 瑕疵或邏輯風險（如分母可能為 0 或渲染符號重複）。

### **第四幕：自癒與驗證層 (Active Healer & MCRI - Ab3)**
- **動作**: 
    - **Diff View**: 左右並列顯示 Raw vs Healed Code。
    - **修復軌跡**: 橘色高亮顯示被 Active Healer 自動修正的 LaTeX 符號與語法錯誤。
- **評分展示**: 實時計算並顯示 `MCRI Score` (語法正確性、數學邏輯、渲染美學三位一體)。

### **第五幕：脫鉤執行層 (Decoupled Execution)**
- **動作**: 展示 GPU 完成推論後進入 Standby，由本地 CPU 秒速執行 Python 代碼。
- **性能對照**: 透過儀表板對比「雲端 API 網路延遲」與「本地 $O(1)$ 生成」的速度落差。

---

## 2. 消融實驗實時對決 (Real-time Ablation Study)

- **Ab1 (Native Mode)**: 
    - **目的**: 暴露大模型的「隨機性錯誤」與「不穩定度」。
    - **效果**: 讓評審看到，即便模型強大，沒有工程干預仍無法用於正式教學與精確出題。

- **Ab3 (Full Engine Mode)**: 
    - **目的**: 展示 100% 的「結果確定性」。
    - **效果**: 證明透過 Scaffold 與 Healer，小模型也能具備極致的可靠性與專業感。

---

## 3. 關鍵解說詞 (Key Talk Tracks)

1. **「我們不依賴模型規模的暴力破解，我們依賴工程架構的精準干預。」**
2. **「這不是一個會猜答案的聊天機器人，這是一個具備自我診斷與修復能力的教育引擎。」**
3. **「透過算力脫鉤，我們在 0.5 秒內完成了一次從『視覺感知』到『邏輯檢核』的完整運算循環。」**

---

## 4. UI 視覺回饋規範

- **正常輸出**: 綠色漸層 (#0F9D58)
- **Healer 介入**: 橘色閃爍 (#FF6D00)
- **錯誤偵測**: 紅色高亮 (#D93025)
- **背景格點**: 實驗室精密網格背景。