# 模式 4 自動保存 Golden Prompts 功能說明

## 🎯 功能目標

在執行**模式 4（專家分工模式）**時，系統會：
1. ✅ 動態生成 Prompt（原有功能）
2. ✅ 將 Prompt 保存到資料庫（原有功能）
3. ✅ **同時將 Prompt 自動保存為 Golden Prompt 文件**（新功能）

## 📂 文件保存規則

### 保存位置
```
experiments/golden_prompts/temp/
├── {skill_id}_Ab1.txt   # Ab1 專用
└── {skill_id}_Ab2.txt   # Ab2/Ab3 共用
```

### 保存邏輯
| Ablation | 保存文件 | 說明 |
|----------|---------|------|
| Ab1 | `{skill_id}_Ab1.txt` | Bare Prompt |
| Ab2 | `{skill_id}_Ab2.txt` | Full Prompt（工程化版本）|
| Ab3 | `{skill_id}_Ab2.txt` | 與 Ab2 共用（差異只在 Healer 開關）|

## 🔧 技術實作

### 修改的文件

1. **core/code_generator.py**
   - `_build_prompt` 增加 `save_golden_prompt` 參數
   - 當 `save_golden_prompt=True` 時：
     - 自動創建目錄（如不存在）
     - 保存 Prompt 到對應文件
     - Ab2/Ab3 自動共用同一文件

2. **scripts/sync_skills_files.py**
   - `run_expert_pipeline` 調用時傳遞 `save_golden_prompt=True`
   - `execute_coder_phase` 增加 `save_golden_prompt` 參數
   - Mode 4 自動啟用保存功能
   - 用戶友好的提示訊息

### 核心代碼邏輯

```python
# 在 _build_prompt 函數中
if save_golden_prompt:
    # Ab2/Ab3 共用同一個 Ab2 文件
    prompt_ablation_id = 1 if ablation_id == 1 else 2
    
    golden_prompt_path = os.path.join(
        project_root,
        'experiments', 'golden_prompts', 'temp',
        f'{skill_id}_Ab{prompt_ablation_id}.txt'
    )
    
    os.makedirs(os.path.dirname(golden_prompt_path), exist_ok=True)
    
    with open(golden_prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"   💾 已保存 Golden Prompt: {os.path.basename(golden_prompt_path)}")
```

## 🎮 使用方式

### 執行模式 4

```bash
python scripts/sync_skills_files.py
```

**操作步驟**：
1. 選擇課綱/年級/章節
2. 選擇 `[4] 專家分工模式：全部重跑 (Full Pipeline + AST Healing)`
3. 系統顯示：
   ```
   💻 [Step 2] 啟動工程師批次實作 (gemini-1.5-flash)
      🧬 Experiment Config: Ablation=2 | Size=14b | Prompt=Engineered-Only
      💾 自動保存 Golden Prompts（實驗模式 4）
   ```
4. 執行過程中會看到：
   ```
   ╔════════════════════════════════════════════════════════════╗
   ║  🔬 Code Generation & Healing Pipeline                     ║
   ║  Skill: gh_ApplicationsOfDerivatives                       ║
   ║  Ablation: Ab2 (Engineered-Only)                           ║
   ╚════════════════════════════════════════════════════════════╝
   
      💾 已保存 Golden Prompt: gh_ApplicationsOfDerivatives_Ab2.txt
   ```

### 驗證結果

執行完成後，檢查文件：

```bash
# 查看生成的 Golden Prompts
ls experiments/golden_prompts/temp/

# 應該看到：
gh_ApplicationsOfDerivatives_Ab1.txt
gh_ApplicationsOfDerivatives_Ab2.txt
jh_LinearEquations_Ab1.txt
jh_LinearEquations_Ab2.txt
...
```

## 📊 工作流程整合

### 完整實驗流程

```
階段 1: 準備 Golden Prompts
├─ 方法 A: 手動準備（已驗證的 Prompt）
└─ 方法 B: 模式 4 自動生成並保存 ✨ [NEW]

階段 2: 執行批次實驗
├─ 模式 2: 讀取固定 Golden Prompts
└─ 生成 100+ 樣本進行統計分析

階段 3: 數據分析
└─ 比較 Ab1/Ab2/Ab3 的成功率差異
```

### 模式對比

| 模式 | 動態生成 | 讀取 Golden | 保存 Golden | 用途 |
|------|---------|------------|------------|------|
| Mode 1 | ❌ | ❌ | ❌ | 只生成缺失文件 |
| Mode 2 | ❌ | ✅ | ❌ | **批次實驗**（使用固定 Prompt）|
| Mode 3 | ✅ | ❌ | ❌ | 增量生成 |
| Mode 4 | ✅ | ❌ | ✅ | **準備階段**（生成並保存 Prompt）|

## ✅ 測試驗證

### 自動化測試結果

```bash
$ python test_mode4_save_golden.py

【測試 1】Ab1 自動保存 Golden Prompt
------------------------------------------------------------
   💾 已保存 Golden Prompt: jh_LinearEquations_Ab1.txt
✅ Ab1 Golden Prompt 已保存
✅ 保存內容與生成內容一致
   長度: 966 字符

【測試 2】Ab2 自動保存 Golden Prompt
------------------------------------------------------------
   💾 已保存 Golden Prompt: jh_LinearEquations_Ab2.txt
✅ Ab2 Golden Prompt 已保存
✅ 保存內容與生成內容一致
   長度: 11399 字符

【測試 3】Ab3 保存到 Ab2 文件（共用測試）
------------------------------------------------------------
   💾 已保存 Golden Prompt: jh_LinearEquations_Ab2.txt
✅ Ab3 成功更新 Ab2 文件（符合共用設計）
✅ Ab3 保存內容正確

【測試 4】save_golden_prompt=False 時不保存
------------------------------------------------------------
✅ save_golden_prompt=False 時確實不保存文件

============================================================
測試完成 | 全部通過 ✅
============================================================
```

## 🎯 實際應用場景

### 場景 1: 初次準備 Golden Prompts

```bash
# 步驟 1: 執行模式 4 生成並保存
python scripts/sync_skills_files.py
# 選擇 Mode 4

# 步驟 2: 驗證生成的 Prompts
cat experiments/golden_prompts/temp/gh_ApplicationsOfDerivatives_Ab1.txt
cat experiments/golden_prompts/temp/gh_ApplicationsOfDerivatives_Ab2.txt

# 步驟 3: （可選）手動微調 Prompts
# 編輯文件以優化 Prompt

# 步驟 4: 使用 Mode 2 執行批次實驗
python scripts/sync_skills_files.py
# 選擇 Mode 2
```

### 場景 2: 更新 Golden Prompts

```bash
# 情況：MASTER_SPEC 更新後，需要重新生成 Prompts

# 步驟 1: 備份舊的 Golden Prompts
cp -r experiments/golden_prompts/temp experiments/golden_prompts/temp_backup

# 步驟 2: 執行模式 4 重新生成
python scripts/sync_skills_files.py
# 選擇 Mode 4

# 步驟 3: 比較新舊 Prompts
diff experiments/golden_prompts/temp_backup/gh_*.txt experiments/golden_prompts/temp/gh_*.txt

# 步驟 4: 決定是否採用新版本
```

### 場景 3: 多技能批次準備

```bash
# 為 20 個技能批次生成 Golden Prompts

python scripts/sync_skills_files.py
# 選擇年級：ALL
# 選擇模式：Mode 4
# 選擇 Ablation：0（全部）

# 系統會自動：
# 1. 為每個技能生成 MASTER_SPEC（Architect）
# 2. 生成 Ab1/Ab2/Ab3 的 Prompts（Coder）
# 3. 自動保存 Ab1.txt 和 Ab2.txt（Golden Prompts）

# 結果：
experiments/golden_prompts/temp/
├── skill_1_Ab1.txt
├── skill_1_Ab2.txt
├── skill_2_Ab1.txt
├── skill_2_Ab2.txt
└── ...（共 40 個文件：20 技能 × 2 文件）
```

## 🔒 安全機制

### 文件覆蓋保護

- ⚠️ **模式 4 會覆蓋現有的 Golden Prompt 文件**
- 建議：執行前先備份重要的 Prompt

```bash
# 備份現有 Golden Prompts
cp -r experiments/golden_prompts/temp experiments/golden_prompts/temp_$(date +%Y%m%d_%H%M%S)
```

### 目錄自動創建

```python
os.makedirs(golden_prompt_dir, exist_ok=True)
```

- 即使 `experiments/golden_prompts/temp/` 不存在，也會自動創建
- 不會因為目錄缺失而報錯

## 📈 效益分析

### 時間效益

**舊流程**（手動準備）：
1. 執行模式 4 生成代碼
2. 手動從終端複製 Prompt
3. 手動創建文件並粘貼
4. 重複 20 次（20 個技能）
→ **總耗時：約 30 分鐘**

**新流程**（自動保存）：
1. 執行模式 4
2. 系統自動保存
→ **總耗時：0 分鐘（自動完成）**

### 準確性提升

- ✅ 消除人為複製錯誤
- ✅ 確保文件內容與生成內容一致
- ✅ 自動處理 Ab2/Ab3 共用邏輯

### 可維護性

- ✅ MASTER_SPEC 更新後，重新執行模式 4 即可
- ✅ 不需要手動管理多個 Prompt 文件
- ✅ 版本控制友善（Git 可追蹤變更）

## 🏆 總結

### 核心價值

1. **自動化**：模式 4 一鍵生成 + 保存
2. **標準化**：確保 Ab2/Ab3 使用同一 Prompt
3. **可追蹤**：Golden Prompts 可納入版本控制
4. **高效率**：節省手動準備時間

### 實驗流程優化

```
準備階段（一次性）
└─ 模式 4：生成 MASTER_SPEC + 保存 Golden Prompts ✨

實驗階段（重複執行）
└─ 模式 2：讀取固定 Golden Prompts + 批次生成

分析階段
└─ 讀取實驗日誌 + 統計分析
```

### 關鍵改進

- **模式 2 + 模式 4** = 完整的實驗管理方案
- **準備（Mode 4）→ 執行（Mode 2）→ 分析** = 科學實驗流程
- **固定輸入 + 可重現輸出** = 嚴謹的實驗設計

---

**現在您可以：**
1. 使用模式 4 快速準備所有技能的 Golden Prompts
2. 使用模式 2 執行可重現的批次實驗
3. 專注於分析 Healer 的純粹效果

這是實驗流程的又一次重大改進！🎉
