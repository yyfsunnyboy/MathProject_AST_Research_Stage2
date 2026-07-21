# Candidate B r003 taxonomy v3：remaining134 multiple_signal_chain provisional adjudication v1

**狀態：`AI_ASSISTED_PROVISIONAL_ADJUDICATION_NOT_FORMAL_HUMAN_REVIEW`**

本 revision 針對 remaining171 machine census 中 `operational_cluster == multiple_signal_chain` 的 13 格，
以 frozen H0 source、AST、coarse diagnostics phase/class/line 與 public prompt contract 進行 AI-assisted provisional adjudication。
**不是**正式人工裁決；未載入 H1、hidden expected、新 diagnostics、EvalPlus 或 Healer；未重新執行程式。

## Primary layer 彙總

| Layer | Cells |
|---|---:|
| `L4` | 11 |
| `L5` | 1 |
| `UNRESOLVED` | 1 |

## 方法學邊界

- machine census manifest SHA 已釘選驗證
- 母體為 remaining171 roster；與 G2_module 27 及 module_exception 37 交集均為 0
- machine signals 為輸入線索，不得直接等同 taxonomy layer
- outcome_validity 一律 VALID_MODEL_OUTCOME（模型失敗路徑）
- healer_eligibility 均為 abstain；未宣稱 Healer 安全或充分
- pre-freeze adversarial audit 已執行；修訂後 verdict READY_TO_FREEZE_WITHOUT_CHANGE
- mechanism tag 政策：specific tags 恆保留；frozen diagnostic phase 在 {G2_base,G2_plus} 且 termination raised 時另加 module_execution_exception
- outcome_validity ≠ taxonomy layer 確定性；VALID_MODEL_OUTCOME 可與 UNRESOLVED primary 並存
