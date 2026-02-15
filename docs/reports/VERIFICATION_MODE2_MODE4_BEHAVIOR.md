======================================================================
🔍 [Verification Report] Mode [2] vs Mode [4] 行為確認
======================================================================

Date: 2026-02-08
Project: MathProject_AST_Research
File: scripts/sync_skills_files.py

---

## ✅ MODE [2] - 強制重新生成（使用 Golden Prompt）

📋 配置位置: 第 427-433 行

当用户选择 Mode [2] 时：

✅ 第 427 行：skip_architect = True
   → 不运行 Architect 阶段，跳过 Prompt 自动生成

✅ 第 428 行：use_golden_prompt = True  
   → 标志位设为 True，告诉系统使用已保存的 Golden Prompts

✅ 第 429 行：print("將使用固定的 Golden Prompts（不再動態生成）")
   → 用户提示：将使用固定的 Golden Prompts

✅ 输出信息：
   - Ab1 读取: experiments/golden_prompts/temp/{skill_id}_Ab1.txt
   - Ab2/Ab3 共用: experiments/golden_prompts/temp/{skill_id}_Ab2.txt

📌 传递链确保：
   ├─ 第 516 行 (Ablation [0] 循环)
   │  use_golden_prompt=use_golden_prompt  ✅ 
   │  → 传递 True 给 execute_coder_phase()
   │
   ├─ 第 242 行 (execute_coder_phase)
   │  use_golden_prompt=use_golden_prompt  ✅
   │  → 传递给 auto_generate_skill_code()
   │
   └─ 第 181-196 行 (code_generator._build_prompt)
      if use_golden_prompt:
          读取 experiments/golden_prompts/temp/{skill_id}_Ab{1|2}.txt
          返回已保存的 Golden Prompt
          ✅ 不会调用 PromptBuilder 生成新的

🔄 Ablation 逻辑验证：

   [选 [0] → 综合评估]
   ├─ AB1: use_golden_prompt=True → 读取 Ab1 Golden Prompt ✅
   ├─ AB2: use_golden_prompt=True → 读取 Ab2 Golden Prompt ✅
   └─ AB3: use_golden_prompt=True → 读取 Ab2 Golden Prompt ✅

   [选 [1/2/3/其他任意选项]]
   ├─ AB?: use_golden_prompt=True → 读取对应 Golden Prompt ✅
   └─ 不会触发动态生成

🎯 Mode [2] 结论：
   ✅ 不管后面选什么 Ablation ([0/1/2/3])
   ✅ 都会使用 Golden Prompts (不会生成新的)
   ✅ 实验可完全复现

---

## ✅ MODE [4] - 專家分工模式（重新生成 + 保存覆蓋 Golden Prompt）

📋 配置位置: 第 435-437 行

当用户选择 Mode [4] 时：

✅ 第 435 行：run_full_pipeline = True
   → 启用完整流程（包括 Architect 阶段）

✅ 第 436 行：跳过 use_golden_prompt 赋值
   → use_golden_prompt 保持默认值 False (第 421 行)

✅ 第 571-582 行：
   if run_full_pipeline:
       run_expert_pipeline(
           list_to_process, 
           arch_model,              ← Architect 已启用
           current_model,
           ablation_id,
           model_size_class,
           prompt_level
       )
   → 调用 run_expert_pipeline() 而不是 execute_coder_phase()

📌 run_expert_pipeline() 流程：

   第 170-216 行 (run_expert_pipeline 函数)：
   
   for ablation_id in ablation_ids:  ← 遍历所有指定的 ablation
       
       # STEP 1: 运行 Architect 阶段（生成新的 Spec）
       run_architect_phase(...)      ✅ 调用 Architect 生成提示词
       
       # STEP 2: 运行 Coder 阶段（生成代码）
       execute_coder_phase(
           ...,
           use_golden_prompt=False,  ✅ 使用新生成的 Prompt
           save_golden_prompt=True   ✅ 保存覆盖 Golden Prompt！
       )

🔄 Ablation 逻辑验证：

   [选 [0] → 综合评估]
   ├─ AB1: run_architect_phase() 生成新 Prompt → 覆盖 Ab1 Golden ✅
   ├─       save_golden_prompt=True → 保存到 experiments/golden_prompts/temp/
   │
   ├─ AB2: run_architect_phase() 生成新 Prompt → 覆盖 Ab2 Golden ✅
   ├─       save_golden_prompt=True → 覆盖保存 Ab2 Golden
   │
   └─ AB3: run_architect_phase() 生成新 Prompt → 覆盖 Ab2 Golden ✅
           save_golden_prompt=True → 最后一次覆盖 Ab2 Golden

   [选 [1/2/3/其他任意选项]]
   ├─ AB?: run_architect_phase() 生成新 Prompt ✅
   ├─       execute_coder_phase(..., save_golden_prompt=True)
   └─       覆盖保存对应的 Golden Prompt ✅

🎯 Mode [4] 结论：
   ✅ 不管后面选什么 Ablation ([0/1/2/3])
   ✅ 都会:
      1. 运行 Architect 阶段（生成全新的 Specification Prompt）
      2. 生成全新的代码（不使用旧的 Golden Prompts）
      3. 将新生成的 Prompt 保存覆盖原有的 Golden Prompts
   ✅ 原有的 Golden Prompts 被新值完全替换

---

## 📊 对比总结表

┌──────────────────┬─────────────────────┬──────────────────────┐
│ 模式选择         │ Mode [2]            │ Mode [4]             │
├──────────────────┼─────────────────────┼──────────────────────┤
│ 运行 Architect   │ ❌ 否 (跳过)        │ ✅ 是 (运行)         │
│ 使用 Golden      │ ✅ 是 (读取)        │ ❌ 否 (生成新的)     │
│ 保存 Golden      │ ❌ 否 (不覆盖)      │ ✅ 是 (覆盖保存)     │
│ Ablation [0]     │ 都用 Golden         │ 都生成新的           │
│ Ablation [1/2/3] │ 都用 Golden         │ 都生成新的           │
│ 实验再现性       │ ✅ 完全可复现      │ ❌ 每次都新生成     │
│ 文件输出         │ ✅ Overwrite 範圍   │ ✅ 全覆盖 (含Golden) │
│ 用途             │ 测试已有 Prompts    │ 优化和更新 Prompts   │
└──────────────────┴─────────────────────┴──────────────────────┘

---

## ✅ 最終確認

你的需求已完全满足 ❌ BOTH modes now correctly handle:

✅ Mode [2]: 
   - 不管选什么 Ablation，都只读取 Golden Prompts
   - 不会进行动态生成
   - 完全复现之前的实验

✅ Mode [4]:
   - 不管选什么 Ablation，都会重新生成 Prompts
   - 每个 ablation 都运行 Architect
   - 生成的新 Prompts 覆盖掉原本的 Golden Prompts
   - 适合迭代改进和参数优化

======================================================================
验证日期: 2026-02-08
状态: ✅ 所有逻辑验证无误
======================================================================
