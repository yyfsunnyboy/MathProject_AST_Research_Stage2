# Golden Prompt 模式實作說明

## 📌 修改目的

**問題診斷**：
- 每次都動態生成 Prompt → 浪費時間，變因不可控
- 研究焦點模糊 → 看起來在展示 PromptBuilder 能力，而非 Healer 效果

**解決方案**：
- **固定 Golden Prompts**（已驗證可用的 Prompt）
- **控制單一變因**：只改變 Healer 開關（Ab2 vs Ab3）
- **清晰研究問題**：Healer 對生成品質的影響

## 🔧 修改內容

### 1. core/code_generator.py

#### 修改 `_build_prompt` 函數
```python
def _build_prompt(skill_id, ablation_id, db_master_spec, use_golden_prompt=False):
```

**新增邏輯**：
- 當 `use_golden_prompt=True` 時：
  - Ab1 讀取：`experiments/golden_prompts/temp/{skill_id}_Ab1.txt`
  - Ab2/Ab3 共用：`experiments/golden_prompts/temp/{skill_id}_Ab2.txt`
- Fallback：文件不存在時，自動降級為動態生成

#### 修改 `auto_generate_skill_code` 函數
```python
def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    use_golden_prompt = kwargs.get('use_golden_prompt', False)  # 新增參數
    prompt, topic, textbook_example = _build_prompt(
        skill_id, ablation_id, db_master_spec, 
        use_golden_prompt=use_golden_prompt  # 傳遞參數
    )
```

### 2. scripts/sync_skills_files.py

#### 模式 2 啟用 Golden Prompt
```python
elif mode == '2':
    list_to_process = sorted(list(target_skill_ids))
    skip_architect = True
    use_golden_prompt = True  # 新增：使用固定 Prompt
    print("\n📌 [實驗模式 2] 將使用固定的 Golden Prompts（不再動態生成）")
```

#### 修改 `execute_coder_phase` 函數
```python
def execute_coder_phase(skill_ids, current_model, ablation_id, 
                        model_size_class, prompt_level, 
                        use_golden_prompt=False):  # 新增參數
    
    is_ok, msg, metrics = auto_generate_skill_code(
        skill_id, 
        queue=None, 
        ablation_id=ablation_id, 
        model_size_class=model_size_class,
        prompt_level=prompt_level,
        use_golden_prompt=use_golden_prompt  # 傳遞參數
    )
```

#### 所有調用點更新
- `run_expert_pipeline` → `use_golden_prompt=False`（Mode 4 動態生成）
- Mode 0（綜合評估）→ `use_golden_prompt=False`
- Mode 1/2/3 → 傳遞 `use_golden_prompt` 變量（Mode 2 為 True）

## 📂 Golden Prompt 文件結構

```
experiments/
└── golden_prompts/
    └── temp/
        ├── gh_ApplicationsOfDerivatives_Ab1.txt  # Bare Prompt
        ├── gh_ApplicationsOfDerivatives_Ab2.txt  # Engineered Prompt (Ab2/Ab3 共用)
        ├── jh_LinearEquations_Ab1.txt
        ├── jh_LinearEquations_Ab2.txt
        └── ...
```

## 🎯 實驗流程對比

### 舊流程（動態生成）
```
1. 從數據庫讀取 MASTER_SPEC
2. 調用 PromptBuilder.build() 動態生成
3. 每次可能產生不同的 Prompt（變因不可控）
4. 研究焦點：Prompt 生成 + Healer（混淆）
```

### 新流程（Golden Prompt）
```
1. 讀取固定的 Golden Prompt 文件
2. Ab2 和 Ab3 使用同一個 Prompt
3. 只改變 Healer 開關（單一變因）
4. 研究焦點：純粹的 Healer 效果（清晰）
```

## 🔬 實驗設計優勢

### 控制變因
- ✅ **Ab2 vs Ab3**：相同 Prompt，唯一差異是 Healer 開關
- ✅ **可重現性**：每次實驗使用相同的 Golden Prompt
- ✅ **統計有效性**：變因單一，結果可信

### 效率提升
- ⚡ 不需每次都調用 PromptBuilder
- ⚡ 不需訪問數據庫讀取 MASTER_SPEC
- ⚡ 批次生成時間大幅縮短

### 研究聚焦
- 🎯 **清晰的研究問題**：Healer 能提升多少成功率？
- 🎯 **明確的對照組**：Ab2（無 Healer）vs Ab3（有 Healer）
- 🎯 **簡潔的論述**：不再需要解釋 Prompt 生成邏輯

## 📋 使用方式

### 1. 準備 Golden Prompts

#### 方法 A：手動生成並保存
```python
from core.prompts.prompt_builder import PromptBuilder
import os

skill_id = "gh_ApplicationsOfDerivatives"
master_spec = """[從數據庫或其他來源獲取]"""

# 生成 Ab1 Prompt
ab1_prompt = PromptBuilder.build(master_spec, ablation_id=1, skill_id=skill_id)
with open(f'experiments/golden_prompts/temp/{skill_id}_Ab1.txt', 'w', encoding='utf-8') as f:
    f.write(ab1_prompt)

# 生成 Ab2 Prompt（Ab2/Ab3 共用）
ab2_prompt = PromptBuilder.build(master_spec, ablation_id=2, skill_id=skill_id)
with open(f'experiments/golden_prompts/temp/{skill_id}_Ab2.txt', 'w', encoding='utf-8') as f:
    f.write(ab2_prompt)
```

#### 方法 B：從已生成的成功樣本提取
```bash
# 如果已經生成過成功的檔案，可以提取其使用的 Prompt
# （需要從日誌或實驗記錄中找到）
```

### 2. 執行實驗模式 2

```bash
python scripts/sync_skills_files.py
```

選擇：
- 操作模式：`[2] 強制重新生成範圍內所有檔案 (Overwrite All)`
- 系統會自動提示：
  ```
  📌 [實驗模式 2] 將使用固定的 Golden Prompts（不再動態生成）
     📄 Ab1 讀取: experiments/golden_prompts/temp/{skill_id}_Ab1.txt
     📄 Ab2/Ab3 共用: experiments/golden_prompts/temp/{skill_id}_Ab2.txt
  ```

### 3. 驗證功能

```bash
python test_golden_prompt_mode.py
```

## ⚠️ 注意事項

### Golden Prompt 文件命名規範
- 必須遵守：`{skill_id}_Ab{n}.txt`
- Ab1：獨立文件
- Ab2/Ab3：共用同一個 Ab2 文件

### Fallback 機制
- 如果 Golden Prompt 文件不存在
- 系統會自動降級為動態生成模式
- 並在終端顯示警告訊息

### 模式選擇建議
- **Mode 2**：批次實驗，固定變因（推薦）
- **Mode 4**：探索新題型，需要動態生成

## 📊 實驗數據比較

### 可比較的指標
1. **成功率**：Ab2 vs Ab3
2. **修復次數**：Healer 平均修復了多少問題
3. **生成時間**：Healer 增加了多少額外時間
4. **代碼品質**：MCRI 分數差異

### 不可比較的（已排除）
- ❌ Prompt 變異影響（已固定）
- ❌ 數據庫更新影響（已固定）
- ❌ PromptBuilder 版本影響（已固定）

## 🎓 論文寫作優勢

### 實驗設計章節
```
我們採用固定的 Golden Prompts 作為輸入，確保實驗組（Ab3）
和對照組（Ab2）面對完全相同的生成任務，唯一差異在於
AST Healer 的啟用與否。這種設計排除了 Prompt 變異性對
結果的干擾，使得我們能夠純粹地量化自癒機制的貢獻。
```

### 結果分析章節
```
在固定 Prompt 的條件下，Ab3（含 Healer）相較於 Ab2（無 Healer）
的成功率提升了 X%，平均每題修復 Y 處錯誤...
```

## 🔍 除錯工具

### 檢查 Golden Prompt 是否正確載入
```python
# 在 code_generator.py 中已添加日誌輸出
# VERBOSE_LEVEL >= 1 時會顯示：
📄 已讀取 Golden Prompt: gh_ApplicationsOfDerivatives_Ab2.txt
```

### 手動測試特定技能
```python
python test_golden_prompt_mode.py
```

## 📝 版本記錄

- **2026-02-04**: 首次實作 Golden Prompt 模式
  - 修改 `core/code_generator.py`
  - 修改 `scripts/sync_skills_files.py`
  - 創建 `test_golden_prompt_mode.py`
  - 模式 2 啟用固定 Prompt 讀取

---

**重要提醒**：
此修改是科展實驗設計的重大改進，確保了實驗的科學嚴謹性。
請務必在執行批次實驗前，準備好所有需要的 Golden Prompt 文件。
