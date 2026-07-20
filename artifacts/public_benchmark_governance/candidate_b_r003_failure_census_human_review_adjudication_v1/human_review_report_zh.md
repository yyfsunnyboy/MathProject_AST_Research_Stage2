# Candidate B r003 failure census：human-review adjudication

## 範圍與方法

本裁決只審查 frozen `human_review_queue.csv` 的 21 個代表案例。程式以 program identity 從 r003 frozen H0 journal 擷取這 21 份 source，逐一驗證 source SHA-256；不修改原始資料，也不輸出完整 source。判斷只使用公開 contract 與 source/AST 可觀察證據。本次是 development replay 的治理分析，不是 validation。

執行邊界：`model_calls=0`、`evalplus_executions=0`、`healer_rules_modified=false`、`validation_not_executed=true`。

## 裁決總覽

- 21 案 repairability：ELIGIBLE_EXACT 2、CANDIDATE_REVIEW 1、INELIGIBLE 13、UNRESOLVED 5。
- adjudicated layer：L1 9, L2 6, L4 1, UNRESOLVED 5。
- outcome validity：VALID_MODEL_OUTCOME 16；PENDING_REVIEW 5。
- rank 21 可由重複覆寫後的無進展 self recursion 升為 L4；修法仍不唯一，故 INELIGIBLE。

## L1 裁決

未發現「只移除 Markdown／文字污染即可留下完整、唯一程式」的安全案例。rank 4 的文字污染與截斷推理交織；rank 5、7 是未終止推理 docstring 且沒有實作；rank 1–3、8–9 都需要補寫算法或選擇重複候選，必須 abstain。rank 6 的空 suite 插入 `pass` 是唯一局部 token 修復，且不需要答案；但較早程式仍可能先執行，只有 1 cell／1 task，也沒有允許的新 execution 證據，因此只列 CANDIDATE_REVIEW，不實作。

## L2 裁決

rank 14–15 是相同機制的 unique entrypoint alias：公開 required name 缺失、只有一個 arity-compatible 頂層 callable，純 alias 為機械且唯一，因此 2 案升為 ELIGIBLE_EXACT。這是既有 Healer v0 family，不是新規則；正式 H1 兩案均 fail→fail，代表 packaging 轉換精確，不代表功能被救回。rank 10 有兩個相容候選，屬 ambiguous entrypoint。rank 11–13 的三參數 contract 對兩參數實作需要語義性參數映射，wrapper 不安全；3 cells 也只來自 1 task。

## Candidate rule families

沒有至少跨 2 個不同 task、且達到安全與唯一要求的**新** rule family。既有 unique alias 有 2 cells／1 task；空 suite 候選有 1 cell／1 task。所有其他候選均因截斷、歧義、需算法理解或缺 execution diagnostic 而拒絕。

## 必須 abstain 的案例

除 rank 14–15 的既有 exact alias 外，其餘 19 案目前都必須對自動修復 abstain：rank 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21。其中 rank 6 可保留作研究候選，但在跨題證據與安全診斷不足前仍不得實作。

## 是否足以設計 Healer v1

不足。21 案沒有安全的跨題新 family；唯一 exact family 已存在於 v0 且沒有 rescue，另一個局部 token 候選只有單一案例。這些證據不足以開始設計或實作 Healer v1，也不得將單題修補宣稱為通則。

## 198 unresolved 的最小診斷

後續若依預先核准流程收集 diagnostics，最小集合應是：failure phase、exception class、最後一個 model-source frame 的 line/AST node、entrypoint/signature binding、termination 與 return type/shape、bounded stdout/stderr metadata，以及完整 identity hashes。只保留類別與形狀，不保存 hidden-test 輸入、expected、實際答案、evaluator frame 或輸出內容。這足以協助區分 L2、L4 與仍待判定的 L5，同時避免用 hidden tests 設計規則。

## 保守結論

可升為 ELIGIBLE_EXACT 的是 2/21，且都只是既有 unique-alias guard 下的 packaging 修復；沒有跨 2 tasks 的安全新 rule family。其餘 19 案 abstain。Candidate B failure census 仍是有價值的 development evidence，但目前不授權 Healer v1 設計、規則修改或 untouched20 validation。
