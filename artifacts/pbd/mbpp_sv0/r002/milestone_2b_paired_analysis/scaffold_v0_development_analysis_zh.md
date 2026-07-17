# MBPP+ Scaffold v0 development paired analysis（Milestone 2B）

## 研究界線

本報告只分析凍結的20題active development subset與既有P0/P1 artifacts。這是development exploratory analysis，不代表validation、confirmatory或外部泛化結果。Pipeline correction不是Healer；本輪沒有建置Healer或Scaffold v1，也沒有重新生成或重新評估。

## 配對結論

- 以 `task_id + seed` 得到100組完整配對，無重複或缺漏。
- Observed：70 fail→fail、30 fail→pass、0 pass→fail、0 pass→pass；Scaffold paired rescues=30、regressions=0、net=+30。
- Pipeline-corrected：53 fail→fail、17 fail→pass、17 pass→fail、13 pass→pass；paired rescues=17、regressions=17、net=0。
- P1的30個Pipeline成功不等於P0的30個成功：只有13個pass→pass，另有17個新成功與17個paired regressions。

## Observed、Pipeline與Scaffold效果分離

- **Observed effect**：直接通過由0/100升至30/100，且因P0無Observed pass，所以沒有Observed paired regression。
- **Pipeline effect**：兩組皆為30/100，但逐格配對顯示17 rescue與17 regression；淨效果為0，不能以相同總數推論cells相同。
- **Scaffold effect**：strict Python-only與直接可編譯性大幅提升，這支持『提升直接可評估性』；但沒有提升Pipeline-corrected correctness。
- **Reasoning leakage**：P1有1格，是獨立protocol violation；該格仍按ITT保留，沒有算成合規、Healer或Pipeline rescue。

## 格式與結構診斷（100 cells）

| 指標 | P0 | P1 |
|---|---:|---:|
| Strict Python-only compliant | 0 | 91 |
| Code fence | 96 | 0 |
| 額外文字（fence外） | 79 | 0 |
| 多段程式（多個完整fenced blocks） | 25 | 0 |
| Length termination／truncation | 13 | 8 |
| Raw compile pass | 0 | 94 |
| Pipeline compile status | `{"fail": 6, "not_run_extraction_failed": 21, "pass": 73}` | `{"fail": 6, "pass": 94}` |
| Reasoning leakage | 0 | 1 |

P0 extraction actions：`{"extract:fenced_python": 74, "pass_through:plain_text": 5, "reject_ambiguous:fenced_other": 1, "reject_ambiguous:fenced_python": 20}`。
P1 extraction actions：`{"pass_through:plain_text": 100}`；100格皆為既有plain-text pass-through。

P0 Pipeline entry-point status：`{"extraction_failed": 21, "missing": 17, "not_assessed_compile_fail": 6, "present": 56}`。
P1 Pipeline entry-point status：`{"missing": 3, "not_assessed_compile_fail": 6, "present": 91}`。

操作定義沿用Milestone 1D：strict compliance要求非空、無Markdown fence、無多段fenced program、無fence外文字、非length termination、raw可編譯，並在本分析額外要求無reasoning leakage。它衡量可直接交付Python parser的格式，不等於功能正確。

## Failure census與signature比較

| Taxonomy category | P0 Pipeline failures | P1 Pipeline failures |
|---|---:|---:|
| extraction_or_format_failure | 21 | 0 |
| syntax_failure | 6 | 6 |
| missing_or_wrong_entry_point | 17 | 3 |
| import_or_name_failure | 0 | 0 |
| runtime_exception | 0 | 0 |
| timeout_or_resource_failure | 0 | 0 |
| functional_test_failure | 0 | 0 |
| unknown | 26 | 61 |

- Scaffold消除：code fence 96→0、fence外文字79→0、多段fenced programs 25→0、Pipeline extraction failures 21→0。
- 仍存在：syntax failures 6→6；entry-point failures由17降至3；length termination由13降至8。
- 新增／新暴露：reasoning leakage 0→1；此外Pipeline有17個paired correctness regressions。後者是結果轉移，不應推測成特定程式錯誤原因。
- P1有61個`unknown`：saved evaluator diagnostics只表示generic failure，不能可靠區分functional assertion、runtime、import/name等原因，因此全部維持manual review。

## 統計解讀

Observed exact McNemar p=`1.86265e-09`，paired risk difference=+30 percentage points。Pipeline exact McNemar p=`1`，paired risk difference=0。完整matched-pairs effect size與exact 95% CI見transition summary。

這些cell共享task群組且來自development selection，p值與CI僅作探索性量化，不應解讀為獨立同分布母體抽樣或外部泛化證據。

## v0治理判定

Scaffold v0可以維持為**已凍結、已評估的development baseline artifact**，但目前不能提升為『已證明改善Pipeline correctness』的最終規則：Pipeline淨增益為0且存在17個paired regressions。若要變更提示，只能另提Scaffold v1候選並重新預註冊；本輪不修改v0，也不開始v1。

## Per-task five-seed pass counts

| task_id | Observed P0→P1 (Δ) | Pipeline P0→P1 (Δ) |
|---|---:|---:|
| Mbpp/633 | 0→0 (+0) | 2→0 (-2) |
| Mbpp/769 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/453 | 0→5 (+5) | 0→5 (+5) |
| Mbpp/259 | 0→1 (+1) | 1→1 (+0) |
| Mbpp/739 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/124 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/72 | 0→2 (+2) | 3→2 (-1) |
| Mbpp/792 | 0→0 (+0) | 3→0 (-3) |
| Mbpp/435 | 0→1 (+1) | 0→1 (+1) |
| Mbpp/597 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/732 | 0→5 (+5) | 3→5 (+2) |
| Mbpp/721 | 0→5 (+5) | 1→5 (+4) |
| Mbpp/765 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/777 | 0→0 (+0) | 2→0 (-2) |
| Mbpp/473 | 0→5 (+5) | 4→5 (+1) |
| Mbpp/420 | 0→5 (+5) | 3→5 (+2) |
| Mbpp/742 | 0→1 (+1) | 5→1 (-4) |
| Mbpp/279 | 0→0 (+0) | 3→0 (-3) |
| Mbpp/125 | 0→0 (+0) | 0→0 (+0) |
| Mbpp/603 | 0→0 (+0) | 0→0 (+0) |
