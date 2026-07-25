# H2 module assert quarantine 功能評測報告

本輪依執行前預登錄，使用 WSL2 Ubuntu、Python 3.14.4、EvalPlus 0.3.1、
MBPP+ v0.2.0、parallel=1，僅執行 71 個 transformed Post-H2 candidate。
20 個 abstained 格僅驗證 pipeline/output SHA 完全一致，未執行。

## 結果

- 4B：Raw strict PASS 28；
  Post-H2 strict PASS 28。
  25 個 transformed Raw PASS 控制格全部 preserved，regression 0。
- 9B Conditional23：Raw strict PASS 0；
  Post-H2 strict PASS 0。
- 合計：verified rescue 0、partial repair
  46、regression 0、
  preserved pass 25、abstained unchanged
  20。
- 71 個 transformed 格都有 per-test execution detail，故 assert module-load
  blocker 均有解除證據；其中 46 格仍未達 strict PASS。

## 凍結決定

套用預登錄判準 B：`development_candidate_not_frozen`。
沒有 regression，所有 Raw PASS 均 preserved，但 verified rescue 為
0，因此不凍結為 v1。此結論不代表 H2 無法解除
module-load 阻斷；它只表示本 cohort 未觀察到 strict FAIL→PASS。

本輪零模型呼叫、零重新生成、Raw結果只沿用正式證據；未修改 H1、H2 rule、
raw、static audit，亦未執行新演算法鷹架實驗。
