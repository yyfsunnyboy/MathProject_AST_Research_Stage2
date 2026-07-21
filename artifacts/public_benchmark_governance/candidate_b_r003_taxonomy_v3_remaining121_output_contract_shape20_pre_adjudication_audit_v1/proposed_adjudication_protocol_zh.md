# Proposed adjudication protocol（output/contract-shape 20-cell provisional）

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

## 輸入與固定 roster

- 固定使用 planning v1 `next_batch_roster.csv`（SHA `b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804`）
- 20 格、13 task_id、20 source_sha256；不得增刪或重選
- frozen machine census manifest SHA 釘選

## 允許證據（allowed_evidence）

- public task prompt/spec（`tasks.jsonl`）
- H0 evaluation_source 靜態 AST（不執行）
- coarse diagnostics phase/status/return_type_bucket/return_shape_bucket
- G1/G2/G3e frozen PASS/FAIL flags
- 禁止：hidden expected/actual、exception message、traceback、H1、EvalPlus 重跑

## 逐格輸出欄位

- `program_id`, `task_id`, `source_sha256`
- `allowed_evidence`（JSON path list）
- `observed_machine_signal`：固定 `output_or_contract_shape_signal`
- `primary_layer`：L0–L5 或 UNRESOLVED
- `secondary_layers`：JSON array，僅 L0–L5
- `mechanism_tags`：JSON array（return_shape_mismatch 等；不得放入 layer 標籤）
- `failure_chain`：有序因果 JSON array（例：`["entry_executed","return_shape_mismatch"]`）
- `outcome_validity`：與 taxonomy 分開；completed+G1/G3e PASS → 預設 VALID_MODEL_OUTCOME
- `healer_eligibility`：eligible | conditional | abstain
- `abstain_reason`：層級無法在公開證據下閉合時必填
- `confidence`：HIGH | MEDIUM | LOW
- `evidence_citations`：JSON path+locator list
- `adjudication_identity`：program_id+source_sha256+revision slug

## Primary layer 規則

- 不得僅因 return_type_bucket 非空即判 L5；需有 public prompt/spec 或靜態源碼可引用語意錯誤
- L2 僅在 entry point/arity/可見 signature 與 public contract 衝突且無更深層證據時
- L3 需可見 domain/API/import 誤用證據；不得僅憑 import 存在猜測
- L4 需可見 runtime/algorithm 路徑錯誤（loop/recursion/exception guard）且 public 可定位
- 若 L4 vs L5 無 public 算術或示例可證 → primary=UNRESOLVED，abstain_reason 必填

## Failure chain 規則

- 必須有序因果，不得並列 machine signals
- completed cell 典型鏈：`module_loaded` → `entry_point_invoked` → `returned_value_observed` → `return_shape_or_semantic_mismatch`
- 不得加入未在 allowed_evidence 出現的隱藏測試失敗節點

## Healer eligibility 規則

- 禁止僅因「看起來容易修」標 eligible
- eligible 需同時滿足：可定位、deterministic、bounded、無 hidden oracle、唯一或受約束的安全修改、可提出反例測試
- 若需重建演算法或 public 證據不足以唯一化修補 → conditional 或 abstain
- semantic/output incorrectness 預設 abstain，除非公開示例可唯一推導修正

## Outcome validity

- outcome_validity 與 failure taxonomy 分開判斷
- UNRESOLVED primary 不自動否定 VALID_MODEL_OUTCOME

## 批次偏差提醒

- 本批 return_type 輪詢 oversample 稀有型別；統計不得外推至 remaining119
- 13 task_id 中 6 個具多 source；分析時以 source-level 為 evidence unit
