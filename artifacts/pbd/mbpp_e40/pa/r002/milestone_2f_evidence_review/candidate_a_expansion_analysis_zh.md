# Milestone 2F：Candidate A expansion證據審查與升格判定

## 一頁結論

Candidate A在這批40題、每題5個固定seed的development expansion中，把Pipeline-corrected通過率從P0的19%（38/200）提高到26.5%（53/200），淨增加15格，也就是7.5個百分點。配對結果有30個rescues、15個regressions；two-sided exact McNemar p = 0.0356978，因此預註冊的correctness improvement統計條件成立。這是development內的配對關聯證據，不證明Scaffold造成某一種語意修正。

然而Candidate A不能升格為official Scaffold v1：strict Python-only只有89%（178/200），低於事先凍結的90%門檻。fence為0%、extra text為0%、Pipeline extraction為100%，correctness safety gate與protocol gate都通過，但promotion要求完整通過所有gate；本輪不事後把89%改寫成及格。正確表述是：**correctness有顯著改善，但未滿足預註冊完整promotion gates。**

## 1. 完整性與重現性

- P0與Candidate A各有200個generation、200個evaluation rows與200個journals；40 tasks × 5 seeds形成200組唯一且完整配對。
- model為`qwen3.5:9b`，digest、Q4_K_M、think=false與全部sampling參數均符合凍結計畫；兩組retry皆為0。
- raw文字SHA、Pipeline來源／輸出SHA、evaluation SHA、generation ID與paired identities逐格相符。
- Candidate r001的兩個事故generation ID沒有出現在r002，r001對正式分析仍為0格。
- 重新計算transition為132 fail→fail、30 fail→pass、15 pass→fail、23 pass→pass；exact McNemar p與正式paired manifest一致。
- 本分析未呼叫模型、未執行EvalPlus，也沒有將Pipeline correction稱為Healer。

## 2. 22格格式不合規是什麼？

22格是依同一個預註冊操作定義逐格重建；違規診斷計數（可重疊）為`{"generation_length_termination": 18, "raw_not_python_compilable": 19}`。每格的done reason、compile diagnostic、entry point、extraction與功能結果都列在CSV。

這四個概念不可混用：strict output compliance衡量raw輸出是否可直接當Python檔；generation protocol compliance衡量transport、一次嘗試與thinking等執行規則；Pipeline extraction只說既有extractor是否產生程式；functional correctness才是保存的EvalPlus pass/fail。某格protocol compliant或extraction成功，仍可能格式不合規或功能失敗。

## 3. Rescues、regressions與跨seed集中性

30個rescues、15個regressions及23個共同成功均逐格列入ledger。Mbpp/6是5/5 rescues，表示這個task在五個凍結seed上方向一致；這仍是關聯，不是語意因果識別。

15個regressions只出現在6題：`{"Mbpp/432": 1, "Mbpp/572": 3, "Mbpp/14": 4, "Mbpp/722": 1, "Mbpp/607": 4, "Mbpp/786": 2}`。其中Mbpp/14與Mbpp/607各4/5 regressions。現有evaluator只保存generic fail，無法指出錯誤演算法、邊界案例或其他功能原因，所以15格都標為`insufficient_evidence`，不能宣稱是Scaffold造成特定語意錯誤。

## 4. Candidate A的147個Pipeline failures

既有taxonomy的primary分類為`{"syntax_failure": 19, "unknown": 128}`；另有18格failure與length termination重疊，protocol violation為0格。truncation是正交診斷，不拿來覆蓋syntax、entry-point或unknown primary category。

只有format/extraction或length termination可作為下一版Scaffold的候選問題；syntax與missing entry point可列為evaluator-blind Healer研究候選，但屬高風險，標籤不等於已驗證repair rule。generic evaluator unknown、timeout及需要語意判斷的失敗不得自動修復，也不得因unknown硬分配給Healer。Pipeline correction不是Healer。

## 5. Promotion decision

| Gate／rule | 結果 | 直接證據 |
|---|---:|---|
| Strict Python-only ≥90% | Fail | 89%（178/200） |
| Fence ≤5% | Pass | 0% |
| Extra text ≤5% | Pass | 0% |
| Pipeline extraction ≥95% | Pass | 100% |
| Correctness safety | Pass | 53≥38；30 rescues≥15 regressions；regressions全揭露 |
| Protocol | Pass | reasoning leakage 0；transport-complete ITT；無retry |
| Correctness claim rule | Pass | 30>15且exact McNemar p=0.0356978<0.05 |
| 完整promotion | **Fail** | format gate未通過，Candidate A不得升格official v1 |

## 6. 下一步：Scaffold還是Healer？

先針對22格的可觀察格式診斷形成Candidate B的evidence-based設計需求，再以未啟用development tasks另立前瞻protocol；本輪不設計、實作或凍結Candidate B。Healer只能另行研究那些可由saved source做evaluator-blind判斷的syntax或entry-point候選，而且必須先驗證不改變語意。unknown功能失敗不能交給Healer。

## 7. 外推限制

所有數字只適用於這40題expansion development、這個模型版本、量化、sampling、Scaffold文字與五個seed。沒有讀取validation、internal/external confirmatory、excluded historical或sealed reserve；因此不能外推到封存split、其他模型、其他sampling或正式benchmark效能。

完成標記：`CANDIDATE_A_EXPANSION_EVIDENCE_REVIEW_COMPLETED`
