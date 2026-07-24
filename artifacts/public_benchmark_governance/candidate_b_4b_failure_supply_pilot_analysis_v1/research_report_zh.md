# Stage2 qwen3.5:4b failure-supply pilot 研究報告

## 範圍與資料完整性

本輪僅處理 Stage2／MBPP+ run `mbpp_q35_4b_dev20_failure_supply_pilot_r001`。凍結 manifest SHA-256 為
`955a0b463e2ca6a71b76ed745a266977c5cd7005562e621a1b8091a28fd3eccb`。200 格 generation journal、raw response 與 identity
均驗收通過；本輪 model calls=0，未修改既有 raw、journal、prompt、manifest 或 frozen artifact。
generation `failed=0` 只表示 200 格回應已持久化，不代表 200 格程式正確。

## 離線抽取與 ITT

使用 repo canonical `agent_tools/finals_rebuild/extraction.py`（SHA-256
`a59da1c0a76fe24e868a51481306a5ea09d8d8977c92aab38a6c0c4dc38feccf`）重放：186 格 extracted、14 格 ambiguous。所有 200
格均保留於 ITT 分母；14 格沒有依評測或任一候選內容選程式，因此不送 EvalPlus。
Cell 5（Mbpp/633／Ab1_H0／seed=33）維持 ambiguous、未選 code block、ITT 保留。

## H0 EvalPlus

正式環境為 WSL/Linux、EvalPlus 0.3.1、MBPP+ v0.2.0、parallel=1。可評測 186 格中，
base pass=68、plus pass=52、base+plus aggregate pass=52。
以 200 格 ITT 分母計，base=68/200（34.0%）、
plus=52/200（26.0%）、aggregate=52/200（26.0%）。

## Taxonomy v3.1 與 Healer eligibility

Primary 分布：{"L0": 14, "L1": 22, "L2": 15, "NOT_APPLICABLE_PASS": 52, "UNRESOLVED": 97}。
本輪只使用 extraction、AST、公開 entry point 與 EvalPlus aggregate status。base/plus FAIL
本身不足以區分 runtime 與 semantic root，因此未硬歸 L5，而保留 UNRESOLVED/LOW。
eligibility：eligible=0、conditional=0、abstain=200。未套用或修改 Healer，未建立 H1、
rescue 或 regression 結果。

## 限制

這是 20 個 development tasks 的 failure-supply pilot，不是 validation、confirmatory 或
sealed-reserve 結論。14 格 extraction ambiguity 以 fail-closed 計入 ITT 非通過；186 格評測
只保存 base/plus aggregate status，沒有使用 hidden inputs、canonical solution、expected/actual
或 PASS/FAIL 回饋挑選程式。由於未執行額外定位 diagnostics，多數測試失敗只能安全標為
UNRESOLVED；這是證據邊界，不代表已證明不存在 L3、L4 或 L5 問題。

## 結論

本輪資料可作為 Stage2 MBPP+ 4B failure supply 與後續安全規則研究的 audited input；
目前沒有任何格具備足以授權 Healer 的唯一、答案獨立、確定性修復證據。
