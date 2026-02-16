# 🔴 Ab3 Loop Breaker 失敗案例記錄

**案例 ID**: Ab3-LoopBreaker-Failure-001  
**技能**: gh_ApplicationsOfDerivatives  
**模型**: qwen2.5-coder:14b  
**日期**: 2026-02-01 21:35:26  
**狀態**: **語法錯誤 - 已記錄為學術案例**

---

## 📋 錯誤資訊

### **原始錯誤訊息**

```
[Validation Failed] Execution error: SyntaxError: 'continue' not properly in loop (<string>, line 708)
```

### **檔案資訊**

- **檔案**: `skills/gh_ApplicationsOfDerivatives_14b_Ab3.py`
- **生成時間**: 2026-02-01 21:35:26
- **檔案大小**: 24,800 bytes
- **總行數**: 726 行

### **Pipeline 執行摘要**

```
┌─ Step 0: AI Code Generation ──────────────────────────────┐
│ Model: qwen2.5-coder:14b
│ ○ Prompt Length                  15083 tokens
│ ○ Response Tokens                774 tokens
│ ○ Generation Time                21.18s
│
│ 📊 結果: 0 項修復 | AI 生成完成 (21.18s, 774 tokens)
└──────────────────────────────────────────────────────────┘

┌─ Step 1: Basic Cleanup (All Ablations) ───────────────────┐
│ [進階修復啟動] Markdown + Trimming...
│ ✅ [1/4] 檢查 ```python 標記          → ✓ 發現 1 處
│ ○ [2/4] 檢查 ``` 標記                → ○ 無需修復
│ ○ [3/4] 檢查結尾標記                   → ○ 無需修復
│ ✅ [4/4] 清理前後空白                   → ✓ 完成
│
│ 📊 結果: 1 項修復 | 代碼長度: 2503 → 2489 字符
└──────────────────────────────────────────────────────────┘

┌─ Step 2: Regex Healer (Ab2/Ab3) ──────────────────────────┐
│ [進階修復啟動] Regex Pattern Matching...
│ 🔧 [Loop Breaker] 偵測到危險的無限迴圈，正在轉換為有限迴圈...
│    ✅ 已強制替換無限迴圈為有限迴圈（最多 1000 次）
│    ⚠️  警告：這是緊急保護措施，請檢查生成邏輯是否正確
│
│ 📊 結果: 4 項修復 | 代碼長度: 2489 → 2520 字符
└──────────────────────────────────────────────────────────┘

┌─ Step 3: AST Healer (Ab3 Only) ───────────────────────────┐
│ [語法樹修復啟動] Abstract Syntax Tree Analysis...
│ ✅ 3.1 Parse AST                  ✅ 語法樹解析成功
│
│ 📊 結果: 0 項修復 | AST 結構正常
└──────────────────────────────────────────────────────────┘

┌─ Step 5: Dynamic Sampling (Safety Net) ───────────────────┐
│ [執行驗證] Subprocess with 5s Timeout...
│ ❌ 代碼驗證失敗: SyntaxError: 'continue' not properly in loop (<string>, line 708)
│
│ 📊 結果: 0 項修復 | 跳過（代碼無效）
└──────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════╗
║  ✅ Pipeline 執行成功                                       ║
║  總修復: Basic=1, Regex=4, AST=0                          ║
║  驗證狀態: FAILED ❌                                       ║
║  總耗時: 21.22s                                         ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🔍 根本原因分析

### **問題定位**

**Line 684-717** 的縮排結構錯誤：

```python
def generate(level=1, **kwargs):
    for _safety_counter in range(1000):  # ← Line 684 (Loop Breaker 轉換)
        max_degree = random.randint(3, 5)
        # ... 生成邏輯 ...
        if some_condition:
            break  # Line 704 - 正確（在 for 迴圈內）
    
    # ❌ 從這裡開始，縮排錯誤！應該在 for 迴圈內（縮排 +4）
    derivative_orders_list = []  # Line 705
    while len(derivative_orders_list) < random.randint(1, 2):
        # ...
    
    if len(derivatives) != len(derivative_orders_list):
        continue  # ❌ Line 717 - 錯誤！不在任何迴圈內
```

### **Loop Breaker 的問題**

**當前實現** (`core/healers/regex_healer.py` Line 164-168):

```python
refined_code = re.sub(
    r'(\s*)while\s+(True|1|\(True\)|\(1\))\s*:',
    r'\1for _safety_counter in range(1000):  # Safety: converted from while True',
    refined_code
)
```

**缺陷**:
- ✅ 替換迴圈頭：`while True:` → `for _safety_counter in range(1000):`
- ❌ **沒有調整迴圈體的縮排**
- ❌ 導致後續代碼不在迴圈內

---

## 🎯 學術價值

### **三大貢獻**

#### **1. 揭示了 Regex 的局限性**

**發現**：
> 在處理巢狀結構語言（如 Python）時，Regex 只能做淺層修復，深層邏輯（如 Scope/Indent）必須用 AST。

**證據**：
| 修復工具 | 能處理的問題 | 無法處理的問題 |
|---------|------------|--------------|
| **Regex** | 字串替換、模式匹配 | **縮排調整、作用域識別** |
| **AST** | 結構解析、邏輯修復 | 複雜度高（實現成本） |

#### **2. 定義了「修復的兩難 (Healer's Dilemma)」**

**兩難**：
- **不修（Ab2）** → Runtime Timeout（L1 = 0/20）
- **亂修（Ab3）** → Compile Syntax Error（L1 = 0/20）

**結論**：
> 修復系統必須具備「語法感知能力 (Syntax Awareness)」。

**實驗數據**：
| 組別 | Loop Breaker | 驗證結果 | L1 工程基石 | 原因 |
|------|--------------|---------|-----------|------|
| Ab1 | ❌ 無 | ✅ 通過 | 20/20 | 簡單代碼，無無限迴圈 |
| Ab2 | ❌ 無 | ⚠️ Timeout | **0/20** | 無限迴圈，超時 5秒 |
| Ab3 | ✅ Regex | ❌ Syntax Error | **0/20** | 縮排破壞，語法錯誤 |

#### **3. 驗證了動態採樣 (Dynamic Sampling) 的價值**

**發現**：
> 正是因為我們跑了多次實驗，才捕捉到這個只有在特定代碼結構下才會觸發的 Bug。

**實驗嚴謹性**：
- ✅ **Ab1/Ab2/Ab3 完整對比**：3 組實驗全部執行
- ✅ **動態採樣驗證**：每組 3 次執行測試
- ✅ **5 秒 Timeout 機制**：避免無限等待
- ✅ **完整日誌記錄**：捕捉錯誤細節

**結論**：
> 這證明了我們的實驗方法論是嚴謹的。

---

## 📊 實驗結果對比

### **預期 vs 實際**

| 評測項目 | Ab2 (預期) | Ab2 (實際) | Ab3 (預期) | Ab3 (實際) | 差異分析 |
|---------|-----------|-----------|-----------|-----------|---------|
| **L1 工程基石** | 0 (Timeout) | 0 (Timeout) | 20 | **0 (Syntax Error)** | ⚠️ Loop Breaker 破壞語法 |
| **L2 資料衛生** | 5 | 5 | 20 | **0** | ⚠️ 無法執行 |
| **L3 評測公平** | 15 | 15 | 30 | **0** | ⚠️ 無法執行 |
| **L4 教學有效** | 15 | 15 | 30 | **0** | ⚠️ 無法執行 |
| **總分** | 35 (F) | 35 (F) | **100 (A+)** | **0 (F-)** | ⚠️ 完全失敗 |

### **修復的兩難**

```
修復系統的選擇：

不修復（Ab2）
    ↓
Runtime Timeout
    ↓
L1 = 0/20
    ↓
總分 35/100 (F)

         vs

簡單修復（Ab3 - Regex）
    ↓
Syntax Error
    ↓
L1 = 0/20
    ↓
總分 0/100 (F-)

         ↓
         
結論：需要「語法感知修復」（AST-based）
```

---

## 💡 改進方向

### **短期方案：限制性修復**

只修復簡單且安全的 while True 模式：
```python
# 只修復這種簡單模式
while True:
    if condition:
        break

# 複雜模式不修復，交給 Timeout 處理
```

### **中期方案：AST 級別轉換**

使用 `ast` 模組進行結構化修復：
```python
class LoopBreakerTransformer(ast.NodeTransformer):
    def visit_While(self, node):
        if is_infinite_loop(node):
            return convert_to_for_loop(node)
        return node
```

### **長期方案：語法感知 Healer**

結合 AST + Regex + 語義分析：
- **Regex**: 快速識別模式
- **AST**: 結構化修復
- **語義分析**: 理解代碼意圖

---

## 🏆 論文貢獻

### **Case Study: The Failure of Regex-based Loop Breaking**

**摘要**:
> 我們驚訝地發現，初版 System Healer (Ab3) 的得分竟然比 Bare Model 還低（0分）。這是因為 Loop Breaker 的正則表達式破壞了 Python 對縮排極度敏感的語法結構。這揭示了一個重要的工程結論：「基於字串處理 (Regex) 的代碼修復是脆弱的，真正的代碼修復必須基於語法樹 (AST)。」雖然 Ab3 在此案例中失敗了，但它成功阻斷了 Ab2 的無限迴圈（Timeout），證明了攔截機制的必要性，只是實作層面需要更精細的 AST Parser 支援。

**關鍵圖表**:
```
修復效果對比（gh_ApplicationsOfDerivatives）

MCRI 分數
100 ┤                                    ┌─ 未來展望
90  ┤                                    │  (AST-based)
80  ┤                                    │
70  ┤                                    │
60  ┤                                    │
50  ┤                                    │
40  ┤  ■ Ab1 (45分)                       │
30  ┤  ■ Ab2 (35分)                       │
20  ┤                                    │
10  ┤                                    │
 0  ┤  ■ Ab3 (0分) ← Regex 破壞語法       │
    └────────────────────────────────────┴──────
      Bare  Eng  Healer(Regex)  Healer(AST)
                  ↑ 本次發現      ↑ 改進方向
```

---

## 📸 證據保存

### **檔案備份**

- ✅ 原始錯誤檔案：`skills/gh_ApplicationsOfDerivatives_14b_Ab3.py`
- ✅ Error Log：已記錄於本文檔
- ✅ Pipeline 執行日誌：完整輸出已保存

### **關鍵代碼片段**

**問題代碼** (Line 684-717):
```python
def generate(level=1, **kwargs):
    for _safety_counter in range(1000):  # ← Regex 轉換
        # ... 生成邏輯 ...
        if some_condition:
            break  # Line 704
    
    # ❌ 縮排錯誤開始
    derivative_orders_list = []  # Line 705 - 應該在迴圈內
    # ...
    if len(derivatives) != len(derivative_orders_list):
        continue  # Line 717 - SyntaxError!
```

---

## 🎯 下一步行動

1. ✅ **保留此錯誤版本**：作為學術案例
2. ⏳ **手動修復版本**：調整縮排，獲得「理想 Ab3」數據
3. ⏳ **論文撰寫**：在 Discussion 章節詳述此案例
4. ⏳ **改進實施**：開發 AST-based Loop Breaker

---

**結論**：這是一個**漂亮的失敗**。它比平庸的成功更有價值！ 🏆

---

**文檔版本**: 1.0  
**作者**: Math AI Research Team  
**最後更新**: 2026-02-01 21:51
