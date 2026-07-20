# AI生成程式共同失敗分類標準 v2：MBPP+ adapter

## 身分與範圍

- 上位 taxonomy：`20260719_AI生成程式共同失敗分類標準_實際使用版_v2.md`
- 上位 taxonomy SHA-256：`7a28fcbc19cee92592639ed828c502ef79644ff6b1d71eabe2060076c81abeef`
- 適用範圍：Candidate B r003 development60 的 300 個 H0 programs。
- 本 adapter 只使用公開 prompt contract、evaluation source、AST、generation metadata 與既有 frozen EvalPlus pass/base/plus status；不使用答案、task-specific patch 或 hidden tests。

## MBPP+ gate 對應

| Gate | MBPP+ adapter |
|---|---|
| G1 | `ast.parse(evaluation_source)`；失敗為 L1。 |
| G2 | frozen 結果沒有逐格 exception traceback；除正式 PASS 外，不由 aggregate FAIL 猜測 execution gate。 |
| G3 | 公開 prompt assertions 提供 required function name、觀察 arity與return-use contract；缺函式、signature不相容或沒有 value return 為 L2。 |
| G3a | `NOT_APPLICABLE`：MBPP+ 本輪沒有事前 required Domain API。 |
| G3c | `NOT_APPLICABLE`：MBPP+ 以函式測試通過為準，沒有 canonical-form gate。 |
| G4 | 使用既有 frozen EvalPlus 結果，不重跑；aggregate FAIL 若無更早層證據，維持 `UNRESOLVED`。 |

`evaluator_hash` 欄位使用 frozen evaluation manifest SHA-256 作治理身分；該 manifest 綁定
EvalPlus `0.3.1` 與 `evalplus_0.3.1_check_correctness_subset`。Repository 沒有凍結 EvalPlus
package source hash，因此此欄不可誤稱為 evaluator package code hash；這項 provenance 限制保留在報告中。

## L0–L5 與保守規則

- L0：缺 raw/candidate/result 或來源身分不完整；`INVALID_INFRASTRUCTURE`，不送 Healer。
- L1：evaluation source 無法 parse，或 fail cell 有明確 length truncation；僅機械且唯一的修復才可 review。
- L2：required function、signature、return contract 或 packaging 的公開契約失敗。
- L3：僅 Domain API；本輪一般 MBPP+ 為 N/A，不因缺一般標準函式庫 import 改標 L3。
- L4：runtime/data-flow/缺標準函式庫 import。缺 import 只有靜態候選證據時標 `UNRESOLVED + CANDIDATE_REVIEW`，沒有 traceback 不直接定案 L4。
- L5：必須先有 G1/G2/G3 完整證據才可標。aggregate EvalPlus FAIL、甚至 base-pass/plus-fail，都不足以排除 plus input 下的 runtime failure，因此不得默認 L5。
- 證據不足：`primary_failure_layer=UNRESOLVED`、`outcome_validity=PENDING_REVIEW`。
- 76 個 formal PASS 作 negative controls，保留 `PASSED` 而不塞入 L0–L5。

## repairability_tier

- `ELIGIBLE_EXACT`：公開 contract + AST 可唯一決定的既有 entry-point alias guard。
- `CANDIDATE_REVIEW`：有一般性機械候選，但仍需人工與 regression 評估；本輪不實作。
- `INELIGIBLE`：PASS、L0、語義/return重建或其他越界情況。
- `UNRESOLVED`：尚無足夠證據決定失敗層或修復資格。

## 人工 review 邊界

Queue 只含 AST/contract 特徵與 hash，不含 source。代表案例由 feature stratum 後依 program_id 決定，不以 task_id、答案或 hidden tests 選擇或設計修法。任何 candidate family 都只是 development evidence；`healer_rules_modified=false`。
