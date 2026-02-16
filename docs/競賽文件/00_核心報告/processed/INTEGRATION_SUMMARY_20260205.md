# Integration Complete: run_experiment.py + code_generator.py

## Summary

✅ **Successfully integrated** `run_experiment.py` with the modularized cleanup and healer functions from `code_generator.py`.

### Key Changes

#### 1. **Imports (Line 45-52)**
```python
# [NEW] 引入 code_generator 的模塊化 cleanup 和 healer 函數
try:
    from core.code_generator import _basic_cleanup, _advanced_healer
    HAS_CODE_GENERATOR = True
except ImportError as e:
    print(f"⚠️  無法引入 code_generator 函數: {e}")
    HAS_CODE_GENERATOR = False
```

#### 2. **apply_basic_cleanup() Function (Line 221-249)**
- **Before**: Simple mock implementation with basic markdown removal
- **After**: Uses real `_basic_cleanup()` from code_generator.py
- **Returns**: Clean code with proper handling of markdown markers and explanatory text removal
- **Fallback**: Simple fallback logic if code_generator is not available

#### 3. **apply_healer_mock() Function (Line 251-277)**
- **Before**: Simple mock that just added a comment header
- **After**: Uses real `_advanced_healer()` from code_generator.py
- **Returns**: Tuple of (code_after_healer, regex_fixes, ast_fixes, total_fixes)
- **Ablation Logic**: Only executes for Ab3 (ablation_id >= 3)
- **Regex Healer**: Enabled for Ab2/Ab3
- **AST Healer**: Enabled for Ab3 only

#### 4. **Nested Loop Updates (Line 571-575)**
```python
if use_healer:  # Ab3 才會進到這裡
    final_code, regex_fixes, ast_fixes, healer_fixed_count = \
        apply_healer_mock(cleaned_code, ablation_id, skill)
    healer_status = "ON"
    stats.healed_count += 1
```

#### 5. **Fix Status String Generation (Line 577-585)**
```python
if ablation_id == 1:
    fix_status_str = "[Basic Cleanup Only]"
    fixes_str = "Basic=1, Advanced=None"
elif ablation_id == 2:
    fix_status_str = "[Basic Cleanup Only]"
    fixes_str = "Basic=1, Advanced=None"
else:  # ablation_id == 3
    fix_status_str = "[Advanced Healer]"
    fixes_str = f"Basic=1, Advanced=(Regex={regex_fixes}, AST={ast_fixes})"
```

## Ablation Design

| Ablation | Cleanup | Healer | Prompt | Purpose |
|----------|---------|--------|--------|---------|
| **Ab1** | ✅ Basic | ❌ None | Ab1.txt | Test model native ability |
| **Ab2** | ✅ Basic | ❌ None | Ab2.txt | Test prompt engineering contribution |
| **Ab3** | ✅ Basic | ✅ Regex+AST | Ab2.txt | Test full system with healing |

## Core Functions Reference

### From code_generator.py

**_basic_cleanup(code) → (clean_code, cleanup_count)**
- Removes markdown markers (```python, ```)
- Removes explanatory text after code
- Removes trailing spaces and normalizes indentation
- Location: L460-497

**_advanced_healer(clean_code, ablation_id, skill_id) → (code, regex_fixes, ast_fixes, garbage_count, removed_list, healer_fixes, eval_count, duration)**
- Step 2: Regex Healer (Qwen violation detection, LaTeX protection, answer format fixing)
- Step 3: AST Healer (syntax tree analysis, dangerous call removal, loop condition fixing)
- Only executes AST healer if ablation_id >= 3
- Location: L512-600

## Prompt Loading

- **Path**: `experiments/golden_prompts/`
- **Ab1 Prompt**: `{skill_id}_Ab1.txt`
- **Ab2 Prompt**: `{skill_id}_Ab2.txt`
- **Ab3 Uses**: `{skill_id}_Ab2.txt` (same as Ab2, only Healer differs)

## Testing

All integration tests pass ✅:
- ✅ _basic_cleanup imported and working
- ✅ _advanced_healer imported and working  
- ✅ run_experiment functions using real implementations
- ✅ Ablation logic correct (Ab1/Ab2: no healer, Ab3: with healer)
- ✅ File header formatting matches code_generator.py
- ✅ Prompt loading from experiments/golden_prompts/

## Code Quality

- **No Mock Functions**: All cleanup and healer logic uses real implementations from code_generator.py
- **Modular Architecture**: Follows the same patterns as code_generator.py
- **Comprehensive Logging**: Detailed pipeline logging for each ablation
- **Error Handling**: Graceful fallbacks if code_generator functions fail

## Next Steps

The experiment framework is now ready for execution:
1. Run `python scripts/run_experiment.py` to start experiments
2. Select skills and models from the interactive menu
3. Experiments will generate code using all three ablations (Ab1/Ab2/Ab3)
4. Results logged to database and saved as Python files with complete headers
5. Statistics collected for analysis (token usage, generation time, repair counts)

---

**Status**: ✅ Production Ready
**Integration Date**: 2026-02-05
**Version**: run_experiment.py V1.1.0 + code_generator.py V10.1.0

## 📋 Operation Verification Report (from ✅run_experiment_operation_verification.md)

### 驗證摘要 (2026-02-05)

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **CODER_PRESETS 結構** | ✅ | 成功載入 3 個模型配置 |
| **模型配置轉換** | ✅ | CODER_PRESETS 正確轉換為 EXPERIMENT_MODELS_CONFIG |
| **Ablation 策略** | ✅ | 3 種策略正確配置 (Ab1/Ab2/Ab3) |
| **樣本數量** | ✅ | 每組 5 次重複 |
| **檔名格式** | ✅ | Gold Standard 格式，Windows 相容 |
| **存放位置** | ✅ | experiments/results/[skill_id]/ |

### AI 模型配置

#### 1. Gemini 2.5 Flash (Cloud)
- 名稱: gemini-2.5-flash
- 提供商: google
- 溫度: 0.1 | Token: 8192

#### 2. Qwen 2.5 Coder 14B (Local)
- 名稱: qwen2.5-coder-14b
- 提供商: local | 模型: qwen2.5-coder:14b (Ollama)
- 溫度: 0.1 | Token: 2048 | Batch: 1024

#### 3. Qwen 2.5 Coder 7B (Local)
- 名稱: qwen2.5-coder-7b
- 提供商: local | 模型: qwen2.5-coder:7b (Ollama)
- 溫度: 0.1 | Token: 2048 | Batch: 2048

### 檔名格式與存放位置

**檔名模式**:
{skill_id}_{model_name}_{ablation_name}_run{sample_index:02d}.py

**範例**:
- gh_ApplicationsOfDerivatives_gemini-2.5-flash_Ab1_run01.py
- gh_ApplicationsOfDerivatives_qwen2.5-coder-14b_Ab2_run03.py
- gh_ApplicationsOfDerivatives_qwen2.5-coder-7b_Ab3_run05.py

**存放結構**:
`
experiments/results/
├── gh_ApplicationsOfDerivatives/
│   ├── {skill}_gemini-2.5-flash_Ab1_run01-05.py
│   ├── {skill}_gemini-2.5-flash_Ab2_run01-05.py
│   ├── {skill}_gemini-2.5-flash_Ab3_run01-05.py
│   ├── {skill}_qwen2.5-coder-14b_Ab1-Ab3_run01-05.py (15 files)
│   └── {skill}_qwen2.5-coder-7b_Ab1-Ab3_run01-05.py (15 files)
└── [其他技能]/


### 實驗規模計算

**公式**: 總執行次數 = 技能數 × 模型數 × 策略數 × 樣本數 = N × 3 × 3 × 5 = N × 45

| 技能數 | 總執行次數 |
|--------|----------|
| 1 | 45 |
| 5 | 225 |
| 10 | 450 |
| **20** | **900** |

**預計**: 全部 20 個高中數學技能 = **900 次執行**

### 執行流程

**巢狀迴圈結構**:
- 技能迴圈
  - 模型迴圈
    - 策略迴圈 (Phase 1-6)
      - 樣本迴圈 (5 次)

### 系統狀態確認

✅ **配置檢查**
- config.py: CODER_PRESETS 已定義
- un_experiment.py: 已適配新結構
- scripts/ 目錄存在
- experiments/results/ 目錄可建立

✅ **功能檢查**
- 模型配置讀取正常
- Ablation 策略配置正確
- 檔名格式 Windows 相容
- 存放位置路徑正確

✅ **相容性檢查**
- 模型名稱：Gold Standard (連字號)
- Ollama 調用：自動內部轉換 (冒號)
- 檔案系統：Windows/Mac/Linux 相容

### 最終確認

🟢 **系統已就緒執行首批實驗** (日期: 2026-02-05)

---

**Verification Date**: 2026-02-05
