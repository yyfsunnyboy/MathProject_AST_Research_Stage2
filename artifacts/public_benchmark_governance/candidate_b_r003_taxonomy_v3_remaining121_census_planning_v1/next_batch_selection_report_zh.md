# Candidate B r003 taxonomy v3：remaining121 下一批次選定報告

**狀態：`CENSUS_PLANNING_NOT_TAXONOMY_ADJUDICATION`**

## 選定原則（統計前固定）

- 目標 work cluster：`output_or_contract_shape_signal`
- 目標規模：20 格
- 來源去重：True
- return_type 輪詢：True
- 與 processed77 交集必須為 0
- 不使用 hidden oracle；不因 Healer 可修性選樣

## 本批摘要

- 格數：20
- 唯一 task_id：13
- 唯一 source_sha256：20
- roster SHA256：b020499fdff42b94bcfc9efa1af0ad7011a59ad5c20184c7fc5468bcc3d1f804

## return_type_bucket 分布

| Bucket | Cells |
|---|---:|
| `bool` | 3 |
| `dict` | 2 |
| `float` | 3 |
| `int` | 2 |
| `list` | 2 |
| `mixed` | 2 |
| `other` | 1 |
| `set` | 2 |
| `str` | 2 |
| `tuple` | 1 |

## 選定理由

- remaining121 在排除 module_exception（37）與 multiple_signal_chain（13）後，絕大多數格具 `output_or_contract_shape_signal`：completed 且具 return shape 公開訊號。
- 此 family 與已處理的 runtime exception／multi-signal chain 邊界分明，適合釐清 L3/L4（語意／契約）與 outcome validity 邊界。
- 本批以 source_sha256 代表格去重，避免跨 seed 重播被當成獨立錯誤模式。
- return_type 輪詢確保批次內含 bool/int/str/list 等多種公開 return shape 線索。

## 邊界

- 本報告僅規劃下一批 roster；尚未開始 provisional adjudication。
- `no_decisive_machine_signal`（2 格 INVALID_INFRASTRUCTURE）不納入本批。
