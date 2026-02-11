#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用指南：動態工具選用系統 (V2.4)
Context-Aware Tool Selection System

這份指南說明如何在你的代碼中使用新增的動態工具選用功能。
"""

# ============================================================================
# 快速開始 (Quick Start)
# ============================================================================

from core.prompts.prompt_builder import PromptBuilder

# 方式 1: 自動檢測 (推薦)
# ─────────────────────────
prompt = PromptBuilder.build(
    master_spec=your_master_spec,
    ablation_id=2,
    topic="分數的四則運算",           # 系統會根據 topic 自動檢測
    skill_id="jh_數學1上_FourArithmeticOperationsOfNumbers"
)
# ✅ 系統自動偵測「分數」相關關鍵字
# ✅ 自動啟用 FractionOps, IntegerOps
# ✅ 植入分數運算的工具協定


# ============================================================================
# 進階使用 (Advanced Usage)
# ============================================================================

# 方式 2: 手動調用動態函數
# ─────────────────────────
api_manual, active_tools = PromptBuilder._get_dynamic_api_manual(
    skill_name="多項式的微分",
    skill_desc="學習對多項式函數進行微分運算"
)

print(f"已啟用的工具: {active_tools}")
# 輸出: ['IntegerOps', 'CalculusOps']

# 方式 3: 自訂工具協定
# ─────────────────────────
protocol = PromptBuilder._build_tool_selection_protocol(
    active_tools=['IntegerOps', 'FractionOps', 'CalculusOps']
)
# 會生成包含所有這些工具的使用指南


# ============================================================================
# 關鍵字觸發表
# ============================================================================

# 要啟用 FractionOps，prompt 中需要包含這些關鍵字之一：
FRACTION_KEYWORDS = ['分', 'frac', '/', 'ratio', '有理', 'div', '除法', 'rational']
# 例子:
#   "分數運算" → 觸發 FractionOps ✅
#   "有理數計算" → 觸發 FractionOps ✅
#   "整數四則運算" → 不觸發 (但 IntegerOps 預設啟用) ✅

# 要啟用 RadicalOps，prompt 中需要包含這些關鍵字之一：
RADICAL_KEYWORDS = ['根', 'sqrt', 'root', '幾何', 'geo', '畢氏', 'pythag', '開方', 'radical']
# 例子:
#   "平方根運算" → 觸發 RadicalOps ✅
#   "畢氏定理" → 觸發 RadicalOps ✅

# 要啟用 CalculusOps，prompt 中需要包含這些關鍵字之一：
CALCULUS_KEYWORDS = ['微', '積', 'diff', 'poly', '函', 'func', '切線', 'derivative', '多項式']
# 例子:
#   "微分運算" → 觸發 CalculusOps ✅
#   "多項式函數" → 觸發 CalculusOps ✅


# ============================================================================
# 常見場景
# ============================================================================

# 場景 1: Ablation 研究
# ─────────────────────────
# 比較不同 Ablation 模式中的 Prompt 差異：

ab1_prompt = PromptBuilder.build(
    master_spec=spec,
    ablation_id=1,  # 無動態工具選用
    textbook_example="計算 3/2 - 1/4",
    topic="分數運算"
)

ab2_prompt = PromptBuilder.build(
    master_spec=spec,
    ablation_id=2,  # 有動態工具選用 ✨ 新增
    topic="分數運算",
    skill_id="skill_id_here"
)

ab3_prompt = PromptBuilder.build(
    master_spec=spec,
    ablation_id=3,  # 有動態工具選用 ✨ 新增
    topic="分數運算",
    skill_id="skill_id_here"
)

# 場景 2: 檢查哪些工具被啟用
# ─────────────────────────
if "FractionOps" in ab2_prompt:
    print("✅ 分數工具已啟用")
else:
    print("❌ 分數工具未啟用")

if "Domain Tool Selection Protocol" in ab2_prompt:
    print("✅ 工具選用協定已注入")
else:
    print("❌ 工具選用協定未注入")

# 場景 3: 測量 Token 重量
# ─────────────────────────
ab1_size = len(ab1_prompt)
ab2_size = len(ab2_prompt)

print(f"Ab1 Prompt 大小: {ab1_size} 字符")
print(f"Ab2 Prompt 大小: {ab2_size} 字符")
print(f"差異: {ab2_size - ab1_size} 字符 ({(ab2_size/ab1_size - 1)*100:.1f}% 增大)")
# 預期: Ab2 會比 Ab1 大 10-15% (因為增加了工具手冊)


# ============================================================================
# 工具手冊內容示例
# ============================================================================

# FractionOps 手冊:
# ─────────────────────────
"""
### 2. ✨ 分數工具 (FractionOps) - [檢測到分數相關關鍵字時啟用]
- `FractionOps.create(num, den)`: 建立分數，自動約分。
- `FractionOps.to_latex(frac, mixed=True)`: 輸出 LaTeX (mixed=True 為帶分數格式)。
- `FractionOps.add(a, b)`, `sub`, `mul`, `div`: 分數四則運算。
**規則**: 涉及有理數運算時，必須使用此模組，嚴禁使用 float。
"""

# RadicalOps 手冊:
# ─────────────────────────
"""
### 3. ✨ 根號與幾何工具 (RadicalOps) - [檢測到根號/幾何關鍵字時啟用]
- `RadicalOps.create(inner)`: 建立根號 sqrt(inner) 並自動化簡。
- `RadicalOps.to_latex(expr)`: 輸出標準 LaTeX 根式。
- `RadicalOps.is_perfect_square(n)`: 檢查完全平方數。
**規則**: 涉及無理數或幾何運算時，必須使用此模組。
"""

# ============================================================================
# 調試技巧
# ============================================================================

# 技巧 1: 檢查關鍵字偵測
# ─────────────────────────
import logging
logging.basicConfig(level=logging.INFO)

# 執行這行時會看到詳細的 log:
#   ✅ 檢測到分數相關關鍵字，啟用 FractionOps
#   ✅ 檢測到微積分相關關鍵字，啟用 CalculusOps
#   etc.

prompt = PromptBuilder.build(
    master_spec=spec,
    ablation_id=2,
    topic="高等數學: 分數、根號與微分",
    skill_id="my_skill"
)

# 技巧 2: 手動檢查啟用的工具
# ─────────────────────────
manual, tools = PromptBuilder._get_dynamic_api_manual(
    "你的技能名稱",
    "你的技能描述"
)
print(f"Active tools: {tools}")

# 技巧 3: 比較不同 skill_id 的效果
# ─────────────────────────
for skill_id in ["skill_A", "skill_B", "skill_C"]:
    _, tools = PromptBuilder._get_dynamic_api_manual(skill_id, "")
    print(f"{skill_id}: {tools}")


# ============================================================================
# 預期效果 (Expected Results)
# ============================================================================

# 對於「分數四則運算」技能：
#
# 生成的 Prompt 會包含：
#   1. BARE_PROMPT_TEMPLATE (Ab1) 或 UNIVERSAL_GEN_CODE_PROMPT (Ab2/Ab3)
#   2. ✨ NEW: 【已啟用的數學軍火庫】部分 (含 IntegerOps + FractionOps)
#   3. ✨ NEW: Domain Tool Selection Protocol
#   4. Domain Helpers Code (如果適用)
#   5. MASTER_SPEC
#
# Gemini 會收到的指令：
#   ✅ 「涉及除法、比率時，必須使用 FractionOps」
#   ✅ 「嚴禁自己實現 simplify、gcd 等已有功能」
#   ✅ 「永遠不要說『我沒有這個工具』」
#
# 預期結果：
#   ✅ Gemini 生成的代碼更正確地使用工具
#   ✅ Token 使用更有效
#   ✅ 幻覺率降低

# ============================================================================
# 常見問題 (FAQ)
# ============================================================================

# Q1: 關鍵字檢測區分大小寫嗎？
# A: 不區分。系統會將 skill_name 和 skill_desc 轉為小寫後進行匹配。
#    所以「分數」、「FRAC」、「Frac」都能觸發。

# Q2: 多個關鍵字組合時會怎樣？
# A: 系統會啟用所有匹配的工具。
#    例: 「分數與根號」會同時啟用 FractionOps 和 RadicalOps。

# Q3: 能自訂關鍵字嗎？
# A: 目前不行，但代碼中的 KEYWORD 清單可以方便地修改。
#    如需自訂，請編輯 _get_dynamic_api_manual() 中的關鍵字清單。

# Q4: 如果 skill_id 為空會怎樣？
# A: 系統會跳過動態工具選用，只使用預設的 IntegerOps。

# Q5: 每個工具手冊會增加多少 Token？
# A: 平均每個手冊 200-400 Token。
#    完整的 4 個工具手冊約 800-1000 Token。

print(__doc__)
