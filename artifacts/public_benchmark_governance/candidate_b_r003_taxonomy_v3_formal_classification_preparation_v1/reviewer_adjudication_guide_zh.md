# Candidate B r003 taxonomy v3 reviewer／adjudication guide

## 範圍

本 revision 是 development evidence 的 machine preparation，不是正式人工 adjudication。`classification_preparation.csv` 的198格均為 `PENDING_REVIEW`、`primary_failure_layer=null`；196格可進人工review queue，2格因diagnostic infrastructure failure維持證據阻塞。

## 人工判定順序

1. 先核對 frozen source hash、公開 task contract、evaluator與diagnostics identity。
2. 依 taxonomy v3 順序檢查 infrastructure → G1 → G3e → G2 → G3s → G3a → G3c → G4。
3. diagnostic phase只表示觀察階段，不等於L0–L5；exception class也不能單獨決定layer。
4. `completed/returned` 加 correctness fail仍須先排除L2 output schema／packaging與evaluator問題，才可能裁決L5。
5. G2 raised案例須查看短source context、公開contract及source-frame；Domain API/tool、stdlib、第三方dependency與environment問題必須分流。
6. evidence不足時保持layer null與PENDING_REVIEW，不猜測。

## Infrastructure兩格

兩格只有worker-ready後result EOF/signal exit，沒有model-source frame或return payload。固定保持 `INVALID_INFRASTRUCTURE`、layer null、Healer not_run；不得標L4、不得局部重跑、不得因同屬Mbpp/119互相推定。

## Healer邊界

diagnostics永遠不得成為Healer runtime input。本輪不執行Healer。Eligibility須 evaluator-blind；truncation原則上abstain；entry-point只有唯一、安全、跨題且answer-free候選才可能eligible，多候選必須ambiguous並abstain。不得從correctness結果反推修法。

人工裁決應另建新revision，保存reviewer、時間、證據與disagreement；不得覆寫本 preparation、legacy census、既有21案adjudication或v3 crosswalk。
