# Candidate B r003 taxonomy v3.1：remaining101 batch01 20-cell provisional v1

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

## 範圍

- 僅裁決固定 next 20-cell roster；不增減、不替換。
- 不執行 candidate／tests／EvalPlus／diagnostics／validation／Healer。
- 不修改 frozen97、不修改 census revision、不 freeze／commit／push。
- `UNRESOLVED` 不是 L6；本輪 20 格皆 `ADJUDICATED`（不足則 UNRESOLVED，非 PENDING_REVIEW）。

## Roster closure

- adjudication roster SHA-256：`9f475868806c9a73bd25f96cb2c731f6357cafe0e6e08b53aa1fd0a374f13533`
- adjudication records SHA-256：`e08f1eab72275d7c37884883b1a439438daee6a2be0d8df408ba758b2364990b`
- cells=20; unique program/source/task=20/20/16

## Primary / secondary

- primary `L5`：8
- primary `UNRESOLVED`：12
- secondary `(empty)`：20

## Healer eligibility

- {'abstain': 20}

## Outcome / confidence

- outcome：{'VALID_MODEL_OUTCOME': 20}
- confidence：{'HIGH': 8, 'LOW': 12}

## UNRESOLVED

- count：12
- reason codes：{'complex_algorithm_without_public_trace': 1, 'public_examples_non_discriminating_need_diagnostics': 1, 'public_examples_non_discriminating_plus_fail': 10}
- needing future diagnostics：12

## L2 說明

- 本批真正裁決為 L2：0 / 20
- 上一輪 99 格 contract-related **planning signal** 不能直接等於 99 格 L2：
  signal 只表示值得審查；L2 需公開契約明確、差異可觀察、且足以解釋失敗。
  本批多數為 return-shape planning signal，但 entry point 正確、回傳型別家族相符，
  根因若可由公開 assert 證明則多為 L5；若公開例子已滿足則為 UNRESOLVED。

## Execution counts

- 全部為 0。

## 停止點

- 完成 provisional v1 後停止；不進行 post-adjudication audit／v2／freeze。

