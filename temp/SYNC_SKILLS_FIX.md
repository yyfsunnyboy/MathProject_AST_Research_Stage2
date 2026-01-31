# sync_skills_files.py 修復 - Model Size Class 選擇

## 🐛 發現的問題

**位置**: [scripts/sync_skills_files.py](scripts/sync_skills_files.py#L454-L476)

**問題描述**：
當用戶選擇 `[0] 綜合評估` 時，程式會跳過詢問 Model Size Class 的步驟，改為使用**自動判斷邏輯**：

```python
# 舊代碼（問題）
if ab_input == '0':
    # 直接根據當前模型自動判斷
    model_config = Config.MODEL_ROLES.get('coder', {})
    current_model_name = model_config.get('model', 'unknown')
    
    if 'gemini' in current_model_name.lower():
        model_size_class = 'Cloud'
    elif '14b' in current_model_name.lower():
        model_size_class = '14B'
    # ...
```

**為什麼是問題**：
1. ❌ 用戶無法選擇想要的 Model Size Class
2. ❌ 自動判斷可能出錯（特別是當模型名稱不符合預期格式時）
3. ❌ 不符合科學實驗的交互設計（應該顯式選擇，而不是隱式判斷）

---

## ✅ 已應用的修復

**新代碼**：

```python
# [FIX V9.2.1] 先詢問 Model Size Class，再執行三個 Ablation
if ab_input == '0':
    print("✅ 已設定實驗模式：綜合評估 (AB1 + AB2 + AB3)")
    
    # 顯示選擇提示
    print("\n" + "="*60)
    print("📏 [實驗變因控制] 請選擇本次綜合評估的 Model Size Class:")
    print("   1: Cloud     -> 大型模型 (如 Gemini, GPT-4)")
    print("   2: Local 14B -> 中型模型 (如 Qwen 2.5-14B)")
    print("   3: Edge 7B   -> 小型模型 (如 Llama 3-8B, Phi-3)")
    print("="*60)
    
    # 接收用戶輸入
    size_map = {'1': 'Cloud', '2': '14B', '3': '7B'}
    ms_input = input("   👉 輸入選項 (1/2/3, 預設 1): ").strip()
    model_size_class = size_map.get(ms_input, 'Cloud')
    print(f"✅ 已設定模型量級：{model_size_class}")
    
    # 使用同一個 model_size_class 執行三個 Ablation
    for ablation_id in [1, 2, 3]:
        # ... 使用相同的 model_size_class ...
```

**優勢**：
✅ 用戶可以明確選擇 Model Size Class  
✅ 三個 Ablation 使用相同的 model_size_class（科學實驗需要）  
✅ 避免自動判斷的不確定性  
✅ 提升用戶體驗和交互一致性

---

## 📊 修復前後對比

| 場景 | 修復前 ❌ | 修復後 ✅ |
|------|---------|----------|
| 選擇 [0] 綜合評估 | 跳過選擇，自動判斷 | 顯示選擇提示 |
| Model Size Class | 自動（可能出錯） | 用戶明確輸入 |
| 三個 Ablation 執行 | 各自獨立判斷 | 使用相同 model_size_class |

---

## 🎯 預期使用流程（修復後）

```
Step 1: 選擇 Ablation ID
   👉 輸入 Ablation ID (0/1/2/3, 預設 3): 0
   ✅ 已設定實驗模式：綜合評估 (AB1 + AB2 + AB3)

Step 2: 選擇 Model Size Class
   📏 [實驗變因控制] 請選擇本次綜合評估的 Model Size Class:
   1: Cloud     -> 大型模型 (如 Gemini, GPT-4)
   2: Local 14B -> 中型模型 (如 Qwen 2.5-14B)
   3: Edge 7B   -> 小型模型 (如 Llama 3-8B, Phi-3)
   👉 輸入選項 (1/2/3, 預設 1): 1
   ✅ 已設定模型量級：Cloud

Step 3: 執行三個 Ablation
   ⏳ 正在執行 AB1 (Bare)...
   ✅ AB1 執行完成
   
   ⏳ 正在執行 AB2 (Engineered-Only)...
   ✅ AB2 執行完成
   
   ⏳ 正在執行 AB3 (Full-Healing)...
   ✅ AB3 執行完成
   
   🎉 綜合評估完成！模型: Cloud，已生成三個版本...
```

---

## ✅ 驗證清單

- [x] 添加 Model Size Class 選擇提示（當選擇 [0] 時）
- [x] 移除自動判斷邏輯（不確定性來源）
- [x] 三個 Ablation 使用相同的 model_size_class
- [x] 提示信息清晰且遵循現有格式

---

## 📝 修改文件

| 文件 | 改動 | 狀態 |
|------|------|------|
| [scripts/sync_skills_files.py](scripts/sync_skills_files.py) | 行 454-476：添加 Model Size Class 選擇邏輯 | ✅ 完成 |

---

*修復完成時間：2026-01-31 03:58*
*版本更新：V9.2.0 → V9.2.1*
*優先級：Medium (影響用戶交互)*
