【🏆 金牌策略快速參考】

══════════════════════════════════════════════════════════════════════════════

✅ 推薦的 20 支技能一覽表

Domain           技能名稱                                    課本例題  複雜度
────────────────────────────────────────────────────────────────────────────

【CALCULUS】(4支)
               gh_ApplicationsOfDerivatives                  28      ⭐⭐⭐
               gh_AreaBetweenCurves                          15      ⭐⭐⭐
               gh_AverageValueOfContinuousFunction           18      ⭐⭐⭐
               gh_DefiniteIntegralAndArea                   ~10      ⭐⭐⭐

【GEOMETRY & CONICS】(4支)
               gh_DistancesRelatedToLines                    24      ⭐⭐⭐
               gh_GeometricApplicationsOfEllipse             20      ⭐⭐⭐
               gh_JudgingTheRelationshipOfCircleAndLine       6      ⭐⭐⭐
               gh_EquationOfALine                             4      ⭐⭐⭐

【LINEAR ALGEBRA】(3支)
               gh_VectorDotProduct                            7      ⭐⭐⭐
               gh_MatrixMeaningAndEquality                    6      ⭐⭐⭐
               gh_CrossProductOfSpaceVectors                  5      ⭐⭐⭐

【TRIGONOMETRY】(2支)
               gh_BasicTrigonometricIdentities               16      ⭐⭐⭐
               gh_SineAndCosineFunctionGraphs                24      ⭐⭐⭐

【COMPLEX & POLAR】(2支)
               gh_PolarFormOfComplexNumbers                   8      ⭐⭐⭐
               gh_ConversionBetweenRectangularAndPolar        3      ⭐⭐⭐

【PROBABILITY & STATS】(2支)
               gh_ConditionalProbability                      6      ⭐⭐⭐
               gh_BayesTheorem                                3      ⭐⭐⭐

【SEQUENCES & SERIES】(1支)
               gh_Sequence                                   16      ⭐⭐⭐

【備選】(2支 - 替代方案)
               gh_PolynomialInequalities                    ~15      ⭐⭐⭐
               gh_RootsOfQuadraticEquations                ~12      ⭐⭐⭐

════════════════════════════════════════════════════════════════════════════

💡 為什麼這樣選？

1. ✅ 複雜度優先：全是複雜度 3（300+ 行代碼的 Gemini 版本作參考）
2. ✅ Domain 多樣化：7 個不同的數學領域
3. ✅ 課本例題充足：平均每個 11-12 個例題（可生成多個變化）
4. ✅ Gemini 代碼對標：每個都有對應的高品質參考實現

════════════════════════════════════════════════════════════════════════════

🎯 Domain 設計思路

為什麼要分 Domain？
  • 不同領域需要不同的「助手函數庫」
    └─ Calculus: 多項式、導數、積分
    └─ Complex: 複數格式化、極坐標轉換
    └─ Linear Algebra: 矩陣運算、向量點積
    
  • 降低 Token 成本
    └─ 從 2500+ 個「混合」 Token 降到 500-800 個「領域專用」 Token
    └─ Qwen 14B 更容易專注於該領域的邏輯
    
  • 提高代碼準確度
    └─ 簡化 MASTER_SPEC = 更少幻覺 = 更多正確代碼

建議的 Domain 分類表：
  
  1. calculus (4個)      → 微分、積分、導數應用
  2. geometry_and_conics (4個) → 直線、圓、橢圓、距離
  3. linear_algebra (3個) → 向量、矩陣、點積
  4. trigonometry (2個)  → 三角函數、恆等式
  5. complex_and_polar (2個) → 複數、極坐標
  6. probability_stats (2個) → 條件機率、貝葉斯
  7. sequences_series (1個) → 數列、級數

════════════════════════════════════════════════════════════════════════════

📊 統計數據

總課本例題數：       209 個
平均每技能例題數：    ~11 個
總 Domain 數：        7 個
複雜度分佈：          全部為 3（最高）

Gemini 代碼參考：
  ├─ 平均行數：        450+ 行
  ├─ 平均助手函數：    ~10 個
  └─ 代表了「天花板」標準

════════════════════════════════════════════════════════════════════════════

🔬 Ablation Study 設計

在這 20 個技能上，執行三層對比：

Ab1: 「Bare Prompt」
     ├─ BARE_MINIMAL_PROMPT (270字符)
     ├─ + Domain-Specific MASTER_SPEC
     └─ NO Healer
     
Ab2: 「SPEC Only」  
     ├─ Domain-Specific MASTER_SPEC (500-800字符)
     └─ NO Healer
     
Ab3: 「Full Stack」
     ├─ Domain-Specific MASTER_SPEC
     ├─ + 統一 Healer (Regex + AST)
     └─ 預期最佳結果

測試資料點：
  • 每個技能 × 10 次迭代 × 3 個層級 = 600 個測試點
  • 或者 20 個技能 × 10 次 = 200 個測試點（若只測 Ab3）

════════════════════════════════════════════════════════════════════════════

🏆 科學獎項核心訴求

評委會想看什麼？

✅ 科學性 (Scientific Rigor)
   → Ablation Study 數據證明
   → 每一層都有量化的效果提升

✅ 創新性 (Innovation)  
   → Domain-Aware Prompt 的新思路
   → 單一 Healer 卻能跨 7 個 Domain

✅ 完整性 (Completeness)
   → 20 個技能 × 7 個 Domain
   → 209 個課本例題作驗證集

✅ 實效性 (Practical Value)
   → 14B 模型 = 成本 1/50 vs Gemini
   → 速度更快、可自部署

✅ 呈現力 (Presentation)
   → 進度條展示：Bare → Spec → Healer 的逐步改進
   → 折線圖：跨 Domain 的性能對比
   → 成功案例視覺化

════════════════════════════════════════════════════════════════════════════

⚠️ 風險與對策

風險 1️⃣: Domain-Specific MASTER_SPEC 難以設計
   對策：參考 Gemini 代碼中的「輔助函數」章節

風險 2️⃣: 20 個太多，時間不夠
   對策：Phase 1 只做 Calculus 4個，證明可行性後擴展

風險 3️⃣: 某些 Domain（如複數）的 Healer 效果差
   對策：在 Healer 中添加 Domain-Specific Rules

風險 4️⃣: Qwen 14B 無法達到 Gemini 水準
   對策：失敗本身也是結果 → 驅動未來研究方向

════════════════════════════════════════════════════════════════════════════

📅 實施路線圖（5週）

Week 1: 數據庫與模型設計
        ├─ 在 models.py 添加 domain 字段
        └─ 為 20 個技能標註 domain

Week 2: Domain-Specific MASTER_SPEC 設計
        ├─ 設計 7 個模板
        └─ 修改 prompt_architect.py

Week 3: Healer 層優化
        └─ 添加 Domain-Aware Checks

Week 4: 快速驗證與調整
        ├─ 對比測試：old vs new
        └─ 根據結果調整

Week 5: Ablation Study 執行
        └─ 200+ 個測試點收集數據

════════════════════════════════════════════════════════════════════════════

🎯 最後三句話：

「用 14B 開源模型 × Domain-Aware Prompt × 統一修復策略
  達到 Gemini 級代碼生成品質。
  這是『精簡但智慧』的 LLM 工程新方向。」

════════════════════════════════════════════════════════════════════════════
