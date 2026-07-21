# Post-adjudication adversarial audit（output/contract-shape 20-cell）

**狀態：`POST_ADJUDICATION_ADVERSARIAL_AUDIT_NOT_FREEZE`**

**Audit verdict：`REVISION_REQUIRED_BEFORE_FREEZE`**

## Roster / SHA closure

- cells=20; unique source=20; unique task=13
- next_batch_roster SHA=`b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804`
- provisional manifest SHA=`548486f59c5a42ef03375ace981bbd7219c5f94ae0b374ac3be1c305805fbf8d`
- processed77 交集=0

## 逐格 audit

- accept=18
- change_required=2

## Primary / secondary

- Primary 分布與預期一致：UNRESOLVED=12、L5=7、L2=1
- Secondary 全空：合理（無充分公開證據支持次層）
- 未把 return_shape 單獨當 root cause

## 矛盾一：sufficient vs UNRESOLVED

- Pre-audit：sufficient=15、conditional=5、insufficient=0
- Provisional：UNRESOLVED=12
- 其中 pre-audit sufficient→UNRESOLVED：**11** 格
- 其中 pre-audit conditional→UNRESOLVED：**1** 格（Mbpp/103 seed55）
- 提示中「新增7格」若以 12−5 估算會低估；正確為 **11** 格 sufficient 未能閉合 primary
- **`sufficient` 只代表足以進行裁決（含合法 UNRESOLVED），不代表足以確定 layer**

### 原5格 conditional 處理

| Task | seed | 結果 |
|---|---:|---|
| Mbpp/603 | 22 | L2 / healer abstain / ACCEPT |
| Mbpp/119 | 33 | L5 / healer abstain / ACCEPT |
| Mbpp/237 | 44 | L5 / healer conditional → **改 abstain** |
| Mbpp/103 | 55 | UNRESOLVED / abstain / ACCEPT |
| Mbpp/237 | 22 | L5 / healer conditional → **改 abstain** |

## 矛盾二：Mbpp/237×2 healer conditional

- L5 primary **成立**（order-sensitive Counter vs public order-insensitive keys）
- 兩格為真正不同 source_sha256
- conditional **不成立**：存在多種安全正規化候選；屬 task-specific probe，非通用 Healer 候選
- 建議：`healer_eligibility` conditional→**abstain**；不得計入已證明可修復

## Mbpp/603

- L2 **成立**：靜態 `yield` → generator；public assert 要 list（output contract）
- failure_chain 有序且未逾證
- healer abstain **合理**；`list(...)` 包裝不可 eligible（演算法仍錯、副作用/生成語意反例）

## L5 七格

- Mbpp/581×2、Mbpp/432、Mbpp/572、Mbpp/119、Mbpp/237×2：皆有公開靜態語意證據
- 未使用 hidden expected/actual

## Proposed changes

- 數量：5（含 Mbpp/237 欄位修正與 pre-audit 用語澄清）
- **不得**直接覆寫 provisional revision；需另開修訂輪次

## Freeze

- 本輪 **不可凍結**（REVISION_REQUIRED）
- 未執行 candidate / EvalPlus / diagnostics / validation / Healer / model
