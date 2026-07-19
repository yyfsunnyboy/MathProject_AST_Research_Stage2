# Milestone 2J-B：既有600份 development programs Healer H0→H1 paired analysis

## 凍結範圍與帳務

本分析完整納入60個development tasks、600個programs與1200個H0/H1 accounts，沒有排除cell，也沒有依結果調整Healer規則。41個changed H1使用人工WSL EvalPlus 0.3.1結果；559個unchanged H1只在identity與source-state SHA-256完全一致後沿用H0。Pipeline correction先於H0/H1分帳，且不計為Healer；verified rescue只指同一program由H0 fail轉為H1 pass。

## Cell-level主要結果

- H0：151/600 pass（25.17%）。
- H1：160/600 pass（26.67%）。
- 淨變化：+9 pass，+1.50 percentage points。
- fail→pass verified rescue：9；pass→fail regression：0。
- fail→fail：440；pass→pass：151。
- exact McNemar two-sided p = 0.003906250000（discordant pairs=9）。
- Healer rule實際修改41/600（6.83%）；abstain 148；no-trigger 411。
- 41個changed cells中，verified rescue 9、regression 0；559個unchanged cells僅作identity reuse。

## P0與Scaffold-like分層

- P0：H0 68/300 → H1 77/300；rescue 9、regression 0、changed 39。
- Scaffold-like：H0 83/300 → H1 83/300；rescue 0、regression 0、changed 2。

Healer的可介入窗口高度集中在P0：39個P0 cells被修改並出現9個verified rescues；Scaffold-like只有2個cells被修改，未觀察到額外rescue或regression。這可保守描述為既有Scaffold-like generations較少留下「唯一函式但entry point名稱缺失」的窄修復窗口；不能據此宣稱一般性的Scaffold × Healer因果交互作用，因本資料是development evidence，且兩種prompt條件對應不同generation outputs。

## Development layer分層

- Discovery development：200 programs；H0 60 → H1 68；rescue 8、regression 0。
- Expansion development：400 programs；H0 91 → H1 92；rescue 1、regression 0。
- Task-level：60題完整；有verified rescue的題數為4，有regression的題數為0。

## 保守判定

依評估前固定規則，本輪狀態為`eligible_for_independent_prospective_qualification`：regression為0且rescue至少1，因此此development Healer candidate只取得「可進入獨立prospective qualification」資格，不等於final Healer、不等於validation成功，也不能把個別成功cell用作post-hoc selective acceptance。後續若進行prospective qualification，必須維持相同Healer版本、guards、rule order與完整ITT帳務。
