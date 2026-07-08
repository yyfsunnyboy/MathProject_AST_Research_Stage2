# 第二階段實驗計畫_AST_Active_Healer外部效度與MCRI效度驗證

## 一、文件定位

本文件為旺宏科學獎決賽報告中「第二階段實驗計畫」之正式方法文件，專門說明兩項新增深化驗證：

1. 公開 benchmark 客觀驗證
2. MCRI（Math-Code Reliability Index，數學與程式可靠度指標）效度驗證

本次修訂以 `C:\Users\yehya\Documents\GitHub\AST_experiment\ast_healer_experiments\ast_healer_experiments\` 為**第一優先程式依據**。原始 `MathProject_AST_Research` 僅作為：

- 四層 Active Healer 的來源
- 官方 MCRI / `evaluate_mcri.py` 的來源
- 數學標準函數庫與工具骨架的依賴來源

因此，本文件對第二階段的狀態判定，均以 `ast_healer_experiments/` 內的腳本、方法文件與既有 Excel 結果為準。

## 二、研究背景與問題來源

第一階段研究已完成以下核心內容：

1. 邊緣模型搭配鷹架提示（scaffolding prompt）生成數學出題程式。
2. 四層 Active Healer：`RegexHealer`、`ASTHealer`、`AntiDuplicationHealer`、`UnifiedCleanupHealer`。
3. MCRI 雙軌評估架構，其中程式價值軌可拆為 L1、L2、L5，數學與教學軌為 L3、L4。
4. Ab1 Bare、Ab2 Scaffolding、Ab3 Healer 消融設計。
5. 405 支生成程式與 2,025 道數學題的初步成果。

初賽評審指出五個核心疑問：

1. 主要證據來自自家數學資料池，外部效度不足。
2. MCRI 為研究自訂指標，需證明分項確實對應其宣稱量測的品質。
3. 第一階段中，邊緣模型與雲端模型未必接受完全對等的 Healer 條件。
4. Active Healer 的能力邊界尚未切分清楚，不能把語法、格式、結構與功能正確性混為一談。
5. 「邊緣模型反超雲端」與「MCRI 高分代表全面正確」等結論需更保守。

因此，第二階段研究的重點不再只是追求更高分，而是補上兩條證據鏈：

- **外部效度**：在公開 benchmark 上驗證 Healer 是否仍有效
- **評估效度**：驗證 MCRI 是否真的反映其所宣稱的品質構面

## 三、第二階段研究目的

### 目的一：外部效度

使用公開程式生成 benchmark，檢驗 Active Healer 在原數學出題資料之外，是否仍能提升 LLM 生成程式的可靠度。

### 目的二：公平比較

讓所有模型都具有相同的修復前與修復後條件，避免只讓邊緣模型使用 Healer。

### 目的三：能力邊界

區分 Active Healer 對以下錯誤的效果：

- 語法錯誤
- 輸出格式污染
- 結構問題
- 執行期錯誤
- 功能或演算法邏輯錯誤

### 目的四：MCRI 效度

驗證 MCRI 各分項是否真的對應其宣稱測量的品質，而不只是比較組別平均分數。

## 四、研究問題

### RQ1

Generic Scaffold 是否能提升不同模型在 HumanEval+ 上的程式生成正確率？

### RQ2

在固定同一份模型原始輸出的條件下，Active Healer 是否能顯著提升 HumanEval+ pass@1？

### RQ3

Active Healer 的 Repair Rate、Regression Rate 與 Net Gain 分別為何？

### RQ4

Active Healer 的效果是否因模型規模或模型類型而異？

### RQ5

Active Healer 主要修復的是語法、格式、結構錯誤，還是也能處理功能邏輯錯誤？

### RQ6

MCRI-Code 的 L1、L2、L5 是否分別對應可執行性、輸出衛生與架構品質？

### RQ7

MCRI-Code 是否能區分 HumanEval+ 中功能通過與失敗的程式？

### RQ8

完整 MCRI 的 L3、L4 是否能在原數學程式池中對應數學正確性與教學品質？

## 五、研究假設

本研究採分構面假設，不預設所有假設都必然成立。

### H1

L1 分數與程式解析成功率、執行成功率呈正向關係。

### H2

L2 分數與 Markdown、中文洩漏、格式污染及輸出契約違規數呈負向關係。

### H3

L3 分數與 SymPy 驗證、答案正確率或 `check()` 通過率呈正向關係。

### H4

L4 分數與教師盲評之教學適切性呈正向關係。

### H5

L5 分數與獨立靜態分析或人工程式品質評分呈正向關係。

### H6

MCRI-Code 對 HumanEval+ pass/fail 具有高於隨機的鑑別能力。

### H7

Active Healer 在 HumanEval+ 上的 Fail→Pass 題數應高於 Pass→Fail 題數；若未成立，需如實說明其淨功能增益有限。

## 六、第二階段整體狀態分級

本階段材料必須清楚分成四種狀態：

### 已完成

1. smoke test 全管線驗證
2. 數學池重新執行
3. 數學池初步效度分析

### 已實作但需封板

1. HumanEval+ loader
2. HumanEval+ / MBPP+ 生成流程
3. Healer benchmark adapter
4. 內建 evaluator
5. MCRI-Code 統計與相關分析

### 正式待執行

1. 模型全量正式生成
2. 官方 EvalPlus evaluator
3. 安全隔離、fail-closed、版本鎖定與封板程序

### 延伸研究

1. HumanEvalFix
2. MBPP+ 全量正式比較
3. ICE-Score

## 七、實驗一：公開 Benchmark 客觀驗證

### 7.1 主要程式依據

本實驗的主要腳本為：

- `exp1_benchmark/run_generation.py`
- `exp1_benchmark/run_eval.py`
- `common/healer_benchmark_adapter.py`

其設計目的與功能皆已存在，不應再寫成「尚未實作」。

### 7.2 資料集

主資料集為 **HumanEval+**。

依 `run_generation.py`：

1. `load_dataset('humaneval')` 會優先嘗試 `evalplus.data.get_human_eval_plus()`。
2. 若載入失敗，現有程式會退回本地 `HumanEval.jsonl.gz`。

因此，正確狀態不是「HumanEval+ 管線尚未實作」，而是：

- **HumanEval+ 先導生成、Healer、評估與統計管線已存在**
- 但**官方 EvalPlus evaluator、安全隔離、fail-closed 與版本鎖定尚未封板**

報告書中應明確寫成：

1. HumanEval+ loader、生成與內建 evaluator 已實作。
2. 正式結果仍需改用官方 EvalPlus evaluator 或同等級封板環境。
3. 正式實驗時不得容許無聲退回原版 HumanEval；現行 fallback 邏輯僅適合作為開發期先導流程。

### 7.3 模型

MVP 模型：

- Qwen 8B
- Gemini 雲端模型

第二優先：

- Qwen 14B

其選擇與 `run_generation.py` 及第二階段方法文件一致：

- Qwen 8B 代表本地邊緣模型
- Gemini 代表雲端模型
- Qwen 14B 用於觀察模型規模效應

### 7.4 解碼設定

正式 MVP 採：

- `temperature = 0`
- greedy decoding
- `n_samples = 1`
- deterministic pass@1

`run_generation.py` 已支援：

- 省算力方案：`--n-samples 1 --temperature 0.0`
- 完整抽樣方案：`--n-samples 10 --temperature 0.2`

因此本階段主報告以 deterministic pass@1 為主，n>1 sampling 屬擴充方案。

### 7.5 實驗組別

#### Ab1：Bare Prompt

僅給原始 prompt，無任何鷹架。

#### Ab2g：Generic Safety-and-Format Scaffold

由 `run_generation.py` 的 `GENERIC_SCAFFOLD` 定義，保留與數學無關的通用規則，例如：

- 只輸出 Python 程式碼
- 不輸出 markdown fences
- 只用 Python 標準函式庫
- 不使用 `input()`
- 不使用 `eval()` / `exec()`
- 不使用 `while True`
- 保持目標函式簽名不變

因此，報告中名稱應使用：

`Generic Safety-and-Format Scaffold`

而不是再將它混同為原數學 `SKILL.md`。

#### Ab3：Ab2g + Active Healer

Ab3 不重新生成程式，而是直接對 Ab2g 的同一份 raw output 套用 Healer。

`run_generation.py` 已清楚註明：

`Ab3 = Ab2g raw 輸出 + Healer`

因此，正確說法不是「Ab2g raw → Ab3 healed 配對尚未實作」，而是：

- **該配對流程已實作**
- 需檢查的是 `task_id + sample_idx` 的配對完整性與封板品質

### 7.6 公平比較

第二階段公平比較原則如下：

1. 所有模型都需同時有 Ab2g 修復前與 Ab3 修復後條件。
2. 雲端模型亦需經過同樣 Healer，不可只讓邊緣模型修復。
3. Ab2g 與 Ab3 使用相同 `task_id` 與 `sample_idx` 配對。
4. raw 輸出統一先做 markdown fence 剝除，此為 harness normalization，不算 Healer 功勞。

這些原則已可對應到現有程式：

- `run_generation.py` 以同一批 Ab2g raw 輸出產生 Ab3
- `run_eval.py` 在 raw 路徑上先執行 `BenchmarkHealer.strip_markdown_fences()`
- `run_eval.py` 內建 Ab2g vs Ab3 的 McNemar 配對分析

### 7.7 Active Healer 的 benchmark 模式

`common/healer_benchmark_adapter.py` 已把原始平台的四層 Healer 包成 benchmark 模式：

1. RegexHealer
2. ASTHealer
3. AntiDuplicationHealer
4. UnifiedCleanupHealer

其關鍵限制已明寫於程式與註解中：

- 關閉數學工具依賴注入（`dependency_map = {}`）
- 關閉 live_show 顯示層 Healer
- 移除數學領域 `generate()` fallback 注入
- 保留領域無關的格式、語法、結構修復

`BenchmarkHealer.heal()` 亦會輸出逐層 `trace`，可記錄：

- 哪一層觸發
- 是否改動
- 修復次數
- 層級細節

故本研究已具備：

1. benchmark 模式的四層 Healer adapter
2. 逐層 trace
3. leave-one-out 層級消融的技術基礎

### 7.8 執行安全

現況需區分為：

#### 已實作

- 內建 subprocess evaluator
- timeout
- 基本隔離式單檔執行

#### 尚未封板

- 官方 EvalPlus evaluator
- Docker 或同等級正式隔離
- fail-closed 行為
- 版本鎖定
- 正式 stdout / stderr 保存規範

因此，報告書中應寫成：

- **先導 HumanEval+ 評估管線已存在**
- **正式評估安全環境尚未封板**

而不是寫成「整條 HumanEval+ 管線尚未實作」。

### 7.9 評估指標

本階段主指標如下：

#### Raw pass@1

Ab2g 原始程式通過所有測試的比例。

#### Healed pass@1

Ab3 修復後程式通過所有測試的比例。

#### Repair Rate

原本失敗但修復後通過的比例。

#### Regression Rate

原本通過但修復後失敗的比例。

#### Net Gain

Fail→Pass 題數減去 Pass→Fail 題數，再除以總題數。

#### Trigger Rate

至少一層 Healer 實際修改程式的比例。

#### Effective Repair Precision

Healer 有修改的程式中，最終真正由 Fail→Pass 的比例。

### 7.10 統計方法

保留原先正確設計：

- exact McNemar test
- pass@1 差值
- bootstrap 95% confidence interval
- 多模型比較時使用 Holm correction

其中：

- Ab2g vs Ab3 是配對因果比較
- Ab1 vs Ab2g 是不同提示策略比較

`run_eval.py` 已實作：

- `pass_at_k()`
- `classify_error()`
- `mcnemar()`

正式報告只需將其升級為封板版流程，而非重寫方法本身。

### 7.11 錯誤分類

錯誤分類至少包含：

- SyntaxError
- IndentationError
- NameError
- TypeError
- ImportError
- Timeout
- Assertion failure
- Signature mismatch
- Incomplete output
- Other runtime error
- Functional or logical failure

其中 `run_eval.py` 已有基礎 `classify_error()`，可作為正式錯誤表的起點。

## 八、Smoke Test：已完成的全管線驗證

### 8.1 主要程式依據

`smoke_test/run_smoke_test.py`

### 8.2 已完成狀態

Smoke test 屬於**已完成**，不可再寫成待規劃。

其真實狀態為：

- 合成樣本數 `n = 240`
- 四種品質層：`T0_clean`、`T1_dirty`、`T2_semantic`、`T3_broken`

對應意義：

- T0：canonical code
- T1：格式污染與 fence / 中文思考洩漏
- T2：功能語意錯誤
- T3：刪行與壞語法 mutation

### 8.3 已有結果

依 `results/SMOKE_TEST_exp2_pipeline_demo.xlsx`：

1. T0 修復前 pass 1.000，修復後 0.967
2. T1 修復前 pass 1.000，修復後 0.967
3. T2 修復前後皆 0.533
4. T3 修復前 0.000，修復後 0.667

因此，第二階段報告必須明寫以下事實：

1. **Healer 約有 3% regression**
2. **T3 修復後出現 66.7% 的異常高通過率**
3. 此結果僅屬**管線驗證**，不可當作正式研究結論
4. T3 必須進一步進行 canonical 洩漏、mutation 污染與刪行有效性稽核

### 8.4 Smoke test 的研究意義

其主要用途為：

1. 驗證 Healer 載入、評估、MCRI 程式軌、相關分析與 Excel 輸出整條管線可執行
2. 預先顯示 Healer 不是單向有益，正式研究必須同時報告 repair 與 regression
3. 誠實揭示 MCRI 程式軌對 T2 語意錯誤的邊界

## 九、HumanEvalFix 延伸能力邊界分析

本節仍列為**延伸研究**。

原因是：

- `ast_healer_experiments/` 已完成 HumanEval+、MBPP+、數學池與 smoke test
- 但尚未提供 HumanEvalFix 專用實作腳本

因此本節在報告中應標為：

- **延伸研究**
- 用於界定 Active Healer 對人工植入語意 bug 的直接能力邊界

建議未來分類：

- Value misuse
- Missing logic
- Excess logic
- Operator misuse
- Variable misuse
- Function misuse

與結果標記：

- Directly addressable
- Partially addressable
- Out of scope
- Successful repair
- Partial improvement
- Changed but ineffective
- No action
- Regression

## 十、實驗二：MCRI 效度驗證

### 10.1 主要程式依據

本實驗主要腳本為：

- `exp2_validity/score_mcri_program_track.py`
- `exp2_validity/correlation_analysis.py`
- `exp2_validity/ingest_math_pool.py`
- `exp2_validity/compute_codebleu.py`

### 10.2 核心概念

MCRI 不能只用總分和 pass@1 算單一相關係數。必須拆成不同構面並對應不同外部效標。

本研究保留以下效度矩陣原則：

- L1：工程基礎
- L2：資料與輸出衛生
- L3：數學正確性
- L4：教學有效性
- L5：架構品質

### 10.3 MCRI-Code 與 MCRI-Math

本研究維持：

- `MCRI-Code = L1 + L2 + L5`
- `MCRI-Math = L3 + L4`

其中：

1. benchmark 池只驗證 MCRI-Code
2. 數學池驗證完整 MCRI 與數學構面
3. 兩池不得直接合併為單一主要 Spearman ρ

### 10.4 效度矩陣

| MCRI構面 | 測量內容 | 外部效標 | 適用資料池 |
| --- | --- | --- | --- |
| L1 | 語法及工程可執行性 | parse success、execution success | 兩池 |
| L2 | 格式與資料衛生 | 污染數、契約違規數 | 兩池 |
| L3 | 數學正確性 | SymPy、check_pass、答案正確率 | 數學池 |
| L4 | 教學有效性 | 教師盲評、題目適切性 | 數學池 |
| L5 | 程式架構品質 | 靜態分析、人工程式品質 | 兩池 |
| MCRI-Code | 綜合工程品質 | HumanEval+ pass、ROC-AUC | benchmark 池 |
| 完整MCRI | 數學程式整體品質 | 執行、數學正確、教師評分 | 數學池 |

### 10.5 數學池樣本與資料流

這一版不得再寫「未找到 659 的來源」。

依 `實驗方法_完整版.md` 與 `ingest_math_pool.py`：

- 數學任務池為 **659 支程式**
- 修復前後共 **1,318 次執行**

`ingest_math_pool.py` 亦清楚記錄三態檔案：

- `*_raw.txt`
- `*_extracted.py`
- `*_healed.py`

因此，真正需要釐清的不是 659 是否存在，而是：

- 659 支第二階段數學任務池
- 第一階段 405 支正式生成程式

兩者之間的樣本關係、版本關係與統計單位關係為何。

正式報告中必須新增樣本流向說明：

原始檔案
→ 去重
→ 成功配對
→ 抽出 extracted / healed
→ 補公平工具環境
→ 獨立執行
→ 最終分析樣本

### 10.6 數學池公平工具環境校正

`ingest_math_pool.py` 已對方法學混淆做出校正：

1. extracted 檔缺工具庫時，利用 `extract_injected_preamble()` 從 healed 檔抽取注入區塊
2. 以單元級 preamble 快取補齊早期鷹架差異
3. 將工具注入效應與純修復效應分離

因此，本研究已能在數學池中檢查：

- Healer 真正的增益
- 以及哪些結果只是工具環境注入所造成

### 10.7 已完成的數學池重新分析結果

本節屬於**已有第二階段先導結果**，不得再寫成尚未執行。

依 `實驗方法_完整版.md` 與 `results/exp2_math_pool_validity.xlsx`，應在正式報告中明確列出：

1. **Ab2 / Ab3 在公平工具環境下，原始輸出已 100% 可執行**
2. **Healer 在鷹架條件下的功能級增益趨近零**
3. **Ab1 語法改善明顯，但功能執行率僅小幅提升**
4. **數學池全池 MCRI vs exec_pass ρ = 0.162**
5. **Ab1 層內 ρ = 0.458**（工作表顯示 extracted 0.449、healed 0.467，方法文件摘要取 0.458）
6. **官方 MCRI 總分 ρ = 0.558**（方法文件已明述）

同時，必須保守解讀：

- 數學池全池 ρ 低，顯示其作為單一效度池不足
- 主要原因是 Ab2 / Ab3 的 exec_pass 已飽和為 100%，造成效標端變異不足
- 這正是必須引入公開 benchmark 池的實證理由

### 10.8 統計方法

保留原先正確原則：

對二元效標：

- point-biserial correlation
- ROC-AUC
- logistic regression
- Mann–Whitney U
- bootstrap 95% CI

對連續或序位效標：

- Spearman ρ 為主
- Pearson r 為補充

教師盲評：

- 至少兩位評分者
- 隱藏模型與組別
- Cohen’s κ 或 ICC

### 10.9 效度判讀原則

保留原文件中正確的判讀方式：

1. MCRI-Code 與 pass 高相關，表示工程品質與功能正確性重疊較高。
2. 若中度相關，需拆解 L1、L2、L5。
3. 若低相關且分項亦不成立，需修訂 MCRI。
4. L4 與 pass 低相關不代表 L4 無效，因其測量的是教學品質。

## 十一、研究結果判讀原則

### 情況一

Repair Rate 高、Regression Rate 低，可支持 Active Healer 改善功能正確性。

### 情況二

Repair 與 Regression 接近，表示淨功能增益有限，需要更保守的觸發策略或 regression guard。

### 情況三

pass@1 無明顯改善，但語法、格式、結構品質改善，表示 Active Healer 的主要作用是工程穩定性，而不是演算法邏輯修復。

### 情況四

HumanEvalFix 修復率低，代表 Active Healer 是結構修復器，而不是通用語意修復系統。

### 情況五

MCRI-Code 與 pass 只有中度相關時，應先檢查分項效度，不可立即判定整個 MCRI 無效。

## 十二、研究限制

1. HumanEval+ 與教育數學出題任務仍存在 domain shift。
2. greedy pass@1 不等同完整 sampling pass@k。
3. 雲端模型 API 可能隨時間更新。
4. HumanEval+ 測功能正確性，無法驗證教學品質。
5. 數學池 exec_pass 不等於數學答案正確。
6. HumanEvalFix 的 bug 類型可能與 Active Healer 原設計不重疊。
7. MCRI 的 L4 仍需教師盲評。
8. 公開 benchmark 表現不能直接代表真實課堂成效。

## 十三、預期產出

- HumanEval+ 每題原始資料表
- Raw / Healed pass@1
- Repair Rate
- Regression Rate
- McNemar 檢定
- bootstrap CI
- 錯誤類型表
- Healer 層級觸發熱力圖
- MCRI 分項效度矩陣
- ROC curve
- 數學池與 benchmark 池分開的效度結果
- 樣本流向圖
- 成本－效能 Pareto 圖
- 研究限制與能力邊界表

## 十四、實驗排程

### 第 1 週

- 完成官方 EvalPlus evaluator、fail-closed 與版本鎖定封板
- 完成 benchmark 安全隔離與 smoke 稽核
- 進行 10 至 20 題 pilot 複驗

### 第 2 週

- 執行 Qwen 8B 與 Gemini HumanEval+ 正式生成與評估
- 視進度加入 Qwen 14B

### 第 3 週

- 完成 MCRI-Code 的 benchmark 效度分析
- 完成數學池 L1～L5 分項分析
- 釐清 405 與 659 的樣本關係

### 第 4 週

- HumanEvalFix pilot
- 圖表整理
- 正式統計
- 報告改寫
- 答辯材料

## 十五、寫作限制

1. 不得宣稱尚未跑出的結果。
2. 不得把 smoke test 當正式結果。
3. 不得把可執行等同功能正確。
4. 不得把 MCRI 高分等同所有測試通過。
5. 不得使用「完全根除」「全面反超」「絕對正確」等過度用語。
6. 清楚區分：已完成、已有先導結果、已實作但需封板、正式待執行、延伸研究。
7. 每一個程式檔名與函式名稱必須與實際專案一致。
8. 若現有程式與方法文件不一致，先列出差異，再以實際程式為準。
9. 文件最後附「研究問題－資料－方法－指標－統計檢定」總表。
10. 文件最後附「正式實驗啟動前檢核表」。

## 十六、研究問題－資料－方法－指標－統計檢定總表

| 研究問題 | 資料 | 方法 | 指標 | 統計檢定 |
| --- | --- | --- | --- | --- |
| RQ1 | HumanEval+ | Ab1 vs Ab2g prompt 比較 | pass@1 | 比例差、bootstrap CI |
| RQ2 | HumanEval+ | 同一 raw output 的 Ab2g vs Ab3 配對比較 | Raw pass@1、Healed pass@1 | exact McNemar test |
| RQ3 | HumanEval+ | 錯誤轉移分析 | Repair Rate、Regression Rate、Net Gain | bootstrap CI |
| RQ4 | HumanEval+ | 依模型分層分析 | pass@1 差值、Net Gain | Holm correction |
| RQ5 | HumanEval+ / HumanEvalFix | 錯誤型別與 Healer trace 對照 | Trigger Rate、錯誤類型表 | 描述統計、分層比較 |
| RQ6 | benchmark 池 + 數學池 | MCRI-Code 分項效度分析 | L1/L2/L5 與外部效標關聯 | point-biserial、Mann–Whitney U |
| RQ7 | HumanEval+ | MCRI-Code 鑑別分析 | ROC-AUC、logistic regression | bootstrap CI |
| RQ8 | 數學池 | 完整 MCRI 效度分析 | Spearman ρ、教師盲評一致性 | Spearman、ICC / Cohen’s κ |

## 十七、正式實驗啟動前檢核表

- [ ] 已將 HumanEval+ 載入流程改為 fail-closed。
- [ ] 已鎖定 EvalPlus / HumanEval+ 版本。
- [ ] 已完成官方 EvalPlus evaluator 對接。
- [ ] 已完成安全隔離、無網路、CPU / memory / process 限制。
- [ ] 已確認 `task_id + sample_idx` 配對完整無缺漏。
- [ ] 已完成 raw / normalized / healed 各版本保存。
- [ ] 已完成 smoke test 的 T3 洩漏與 mutation 稽核。
- [ ] 已確認 benchmark 池與數學池完全分開分析。
- [ ] 已釐清 405 與 659 的樣本關係與流向。
- [ ] 已完成正式統計腳本封板。

## 十八、第二階段套件的實際目錄樹

```text
AST_experiment/
├─ README.md
├─ 實驗方法_完整版.md
└─ ast_healer_experiments/
   └─ ast_healer_experiments/
      ├─ README.md
      ├─ common/
      │  └─ healer_benchmark_adapter.py
      ├─ exp1_benchmark/
      │  ├─ HumanEval.jsonl.gz
      │  ├─ run_generation.py
      │  └─ run_eval.py
      ├─ exp2_validity/
      │  ├─ score_mcri_program_track.py
      │  ├─ correlation_analysis.py
      │  ├─ ingest_math_pool.py
      │  ├─ compute_codebleu.py
      │  └─ compute_ice_score.py
      ├─ results/
      │  ├─ SMOKE_TEST_exp2_pipeline_demo.xlsx
      │  └─ exp2_math_pool_validity.xlsx
      └─ smoke_test/
         └─ run_smoke_test.py
```

## 十九、每個主要檔案的現有功能摘要

### `smoke_test/run_smoke_test.py`

使用 30 題 HumanEval canonical solutions 合成 T0/T1/T2/T3 四類樣本，經真 Healer、真測試執行、真 MCRI 程式軌評分與真相關分析後輸出 Excel，作為全管線 smoke test。

### `exp1_benchmark/run_generation.py`

負責 HumanEval+ / MBPP+ 生成階段；支援 Ab1、Ab2g，並以 Ab2g 同一份 raw output 形成 Ab3；同時保存 raw 與 healed 程式檔，並記錄 parseable_before / after 與 healer trace。

### `exp1_benchmark/run_eval.py`

負責 benchmark 評估階段；使用內建 subprocess evaluator 執行測試案例，計算 per-item pass、summary pass@1、錯誤類型與 Ab2g vs Ab3 的配對 McNemar。

### `common/healer_benchmark_adapter.py`

將原始 MathProject 的四層 Healer 包為 benchmark 模式，關閉數學領域規則與 fallback，保留通用修復能力，並輸出逐層 trace。

### `exp2_validity/score_mcri_program_track.py`

將官方 MCRI 的程式價值軌獨立抽出，對任意 Python 程式評 L1、L2、L5 與總程式軌分數，且 L5 直接呼叫原版 `evaluate_mcri.py` 的 `analyze_code_robustness()`。

### `exp2_validity/correlation_analysis.py`

對 benchmark 池或混合樣本池做效度分析，輸出 Spearman ρ、point-biserial、AUC、bootstrap CI、variance check 與 pre-registered verdict。

### `exp2_validity/ingest_math_pool.py`

針對 659 支數學任務池進行重新對帳、join 官方 runs CSV、補公平工具環境、獨立執行 extracted / healed、評 MCRI 程式軌，最後輸出數學池效度工作簿。

### `exp2_validity/compute_codebleu.py`

在 benchmark 池中，以 canonical solution 為 reference 計算 CodeBLEU，作為 MCRI 與 pass 之外的補充指標；不適用於數學池。

### `實驗方法_完整版.md`

完整方法學底稿，已明載 smoke test、公開 benchmark、數學池效度分析、pre-registration 判準與主要已完成結果。

### `results/SMOKE_TEST_exp2_pipeline_demo.xlsx`

保存 smoke test 的逐筆原始數據、heal effect、correlations、variance_check、discrimination 與 verdict。

### `results/exp2_math_pool_validity.xlsx`

保存 659 支數學池修復前後共 1,318 次執行的逐筆資料、heal effect 與效度分析工作表。

## 二十、文件與實際程式不一致處

1. 上一版文件錯把 `MathProject_AST_Research` 當作第二階段主專案，這點已更正。
2. `run_eval.py` 的檔頭註解宣稱有 `--engine evalplus` 與 `--engine builtin` 兩模式，但目前實際程式只實作了內建 subprocess evaluator，尚未真正接上官方 evalplus engine。
3. `run_generation.py` 目前對 HumanEval+ 採「優先 EvalPlus，失敗則退回 HumanEval」；因此它已不是未實作，而是**尚未 fail-closed 封板**。
4. `實驗方法_完整版.md` 已寫出「官方 MCRI 總分 ρ=0.558」，但現有 `exp2_math_pool_validity.xlsx` 的 `correlations` 工作表中 `official_mcri_total` 顯示為 NaN，表示文件結論與現有輸出表之間仍有一處需要回頭核對的分析或匯出差異。
5. smoke test 的設計初衷是讓 T1 代表「格式髒但邏輯對，Healer 應能救活」，但實際工作表顯示 T1 在 baseline fence-strip 後修復前已是 1.000，修復後反而 0.967；因此正式報告應以實際結果為準，不能再沿用理想化預期敘述。
6. `correlation_analysis.py` 的預註冊門檻仍以單一 `ρ ≥ 0.6` 作為 H1 判準；正式報告中可保留此 pre-registered threshold，但主體論述仍應採分構面假設與雙資料池分開分析，不可把它當成整個 MCRI 是否有效的唯一標準。
