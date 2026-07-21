# Pre-audit sufficiency clarification / corrigendum（v2）

**本文件為 v2 文件層澄清，不覆寫、不竄改原 pre-adjudication audit revision。**

## 定義

- pre-audit `evidence_sufficiency=sufficient`：**公開證據足以進行合法的 provisional adjudication**。
- 合法裁決**包含** `primary_layer=UNRESOLVED`（當公開證據不足以閉合 L2/L3/L4/L5 時）。
- `sufficient` **不等於**「足以確定 failure taxonomy layer」。
- `conditional`：可進入裁決，但預期需依賴 abstain/UNRESOLVED 路徑。

## 與 v1 provisional 的關係

- provisional v1：UNRESOLVED=12、LOW=12
- 其中 **11** 格 pre-audit=`sufficient` → provisional=`UNRESOLVED`
- 其中 **1** 格 pre-audit=`conditional`（Mbpp/103 seed55）→ provisional=`UNRESOLVED`
- 其餘 closed layers：L5=7、L2=1（來自 pre-audit sufficient 或 conditional 且公開證據可閉合者）

## 禁止的錯誤敘述

- 不得再描述為「相對於 pre-audit **新增 7 格 UNRESOLVED**」。
- 不得將 `sufficient` 解讀為「必須判出 L2–L5」。
- 不得為降低 UNRESOLVED 數量而推測 root cause。

## 原 artifact 狀態

- `candidate_b_r003_taxonomy_v3_remaining121_output_contract_shape20_pre_adjudication_audit_v1` **保持不變**。
- 本澄清只存在於 provisional **v2** revision。
