# Candidate B r003 development60 正式 2×2 paired analysis

## 範圍與凍結聲明

本分析是同一組 60 tasks × 5 seeds 的 **development replay**，不是 validation，也不是外部效度或 confirmatory evidence。完整納入 P0 與 Candidate B 各 300 programs、四臂共 1200 accounts；沒有排除 task、seed、cell 或帳戶，沒有依結果修改 prompt、Healer、Pipeline、規則或 gate。r001/r002 response 未被使用；untouched20 validation 未讀取、未執行。

## 四臂結果

| Arm | Pass | Rate |
|---|---:|---:|
| P0 H0 | 68/300 | 22.6667% |
| P0 H1 | 77/300 | 25.6667% |
| Candidate B H0 | 76/300 | 25.3333% |
| Candidate B H1 | 76/300 | 25.3333% |

## Scaffold 的直接效果（Candidate B H0 對 P0 H0）

Candidate B H0 比 P0 H0 多 8 pass，差 2.6667 percentage points，相對變化 11.7647%。配對轉移為 fail→fail 186、fail→pass 46、pass→fail 38、pass→pass 30；exact two-sided McNemar p=0.445204669047。這是 development replay 的描述性配對量化，不應外推為 validation 結論。

## Healer 效果

| Prompt condition | Modified / trigger | Abstain | No-trigger | Rescue | Regression | Net | Exact McNemar p |
|---|---:|---:|---:|---:|---:|---:|---:|
| P0 | 39 / 39 | 116 | 145 | 9 | 0 | +9 | 0.003906250000 |
| Candidate B | 2 / 2 | 21 | 277 | 0 | 0 | 0 | 1.000000000000 |

P0 上 Healer 有 9 個 rescue、0 regression；Candidate B 上兩個 changed window 都是 fail→fail，因此 H1 沒有增加 pass，也沒有 regression。298 個 unchanged H1 只有在 evaluation-source bytes/SHA-256 與 H0 完全相同且 ledger 身分吻合後才 reuse。

## 2×2 保守解讀

目前可分別支持「Candidate B 有直接 Scaffold development 效果」與「Healer 在 P0 上有修復效果」，但資料不足以判定兩者是 additive、overlapping/substitutive，或存在一般性交互作用。Candidate B 可能預防了部分 Healer 可處理的介面錯誤；然而 Candidate B 僅產生 2 個 changed window，且兩格均 fail→fail，不能據此宣稱一般性的負交互作用。現階段應標記為 **無法判定交互作用**。

## 預先凍結 gates 與決策

Candidate B 通過格式 gates，且 H0 pass count 高於 P0 H0，因此通過「Scaffold 本身優於 P0」門檻。但預先固定的完整 qualification 明確要求 Candidate B H0→H1 paired net change > 0；觀察值為 0，該 gate 必須判定 **FAIL**，不能用「無 regression」替代。故 Candidate B + Healer **未通過全部 qualification gates**，目前 **不得進入 untouched20 validation**。

這不抹除 Candidate B 的 development evidence：可保留其 +8 pass、+2.6667 percentage points 的直接 Scaffold 證據，以及格式完全合規的觀察；但它不是完整 qualification pass。依預先規格，應暫停正式 20 題 validation，先處理 gate failure；本輪不深化 prompt 或 Healer。

## 執行聲明

- model_calls=0
- evalplus_executions=0
- validation_not_executed=true
