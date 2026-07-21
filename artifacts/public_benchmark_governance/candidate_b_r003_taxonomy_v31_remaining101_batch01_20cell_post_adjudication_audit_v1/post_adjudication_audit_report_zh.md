# Candidate B r003 taxonomy v3.1：batch01 20-cell post-adjudication audit v1

**狀態：`POST_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FREEZE`**
**總評：`POST_ADJUDICATION_REVISION_REQUIRED`**

## 範圍

- 僅稽核 provisional v1；不修改 provisional／census／next20／frozen97。
- 不執行 candidate／tests／EvalPlus／diagnostics／Healer／外部模型。

## 結果摘要

- primary verdict：{'AFFIRMED': 19, 'CHALLENGED': 1}
- materiality：{'MATERIAL': 1, 'NONE': 19}
- transition：{'L5→L5': 8, 'UNRESOLVED→L5': 1, 'UNRESOLVED→UNRESOLVED': 11}
- L5 affirmed/challenged：8/0
- UNRESOLVED affirmed/challenged：11/1
- L2 reverse：AFFIRMED_L2_EQUALS_ZERO
- healer：{'provisional_abstain': 20, 'eligible_candidates_found': 0, 'conditional_candidates_found': 0, 'abstain_affirmed': 20, 'abstain_challenged': 0}
- cells requiring provisional v2：['bfa80269cd8ac74c1987bbbac1e79a24054e0e85f65cf1a4afe972f89b56e57b']

## MATERIAL finding

- Mbpp/103 (`bfa80269…`)：靜態 DP 展開顯示 `A[3][1]` 從未寫入，回傳 0≠公開 assert 4。
  建議 provisional v2：UNRESOLVED→L5、confidence LOW→HIGH、healer 維持 abstain。

## 為何 contract-signal 批仍可 L2=0

- 20 格預期 entry point 皆存在且唯一；無 generator/list 衝突；無足以解釋失敗的公開 shape／signature 違約。
- planning signal 只是審查線索；unique-entry 與 return_shape 已被正確 REJECTED 作為根因。

## 停止點

- 不修改 provisional v1；不建立 v2／freeze／commit／push（本輪）。

