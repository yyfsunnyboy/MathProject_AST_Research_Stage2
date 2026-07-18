# MBPP+ b28 2×2 development qualification operator guide

本guide只操作development-only qualification。執行前必須確認main、乾淨工作樹、HEAD==origin/main，並先執行preflight。不得在validation、confirmatory或sealed資料上使用這些指令。

## Windows：生成

```powershell
.\.venv\Scripts\python.exe scripts\run_mbpp_factorial_development_qualification.py preflight
.\.venv\Scripts\python.exe scripts\run_mbpp_factorial_development_qualification.py generate --treatment p0 --run-id mbpp_q35_9b_p0_b28_r001
.\.venv\Scripts\python.exe scripts\run_mbpp_factorial_development_qualification.py generate --treatment candidate_b --run-id mbpp_q35_9b_cb_b28_r001
```

每個run必須完整140/140且每格exactly one attempt。若中斷或失敗，既有run directory永久不可resume、retry、補跑或覆寫；必須先建立新的事故addendum。

## Windows或WSL：建立H0/H1來源帳

```text
python scripts/run_mbpp_factorial_development_qualification.py materialize-factorial
```

此步不呼叫模型或evaluator。每份generation先經同一Pipeline；H0原樣保存normalized source，H1套用同一Healer source、rule order與guards。Pipeline extraction與fence處理不計入Healer。

## WSL：EvalPlus

EvalPlus執行指令尚未啟用：必須先確認兩個140-cell runs及560個factorial source accounts完整，並在下一個execution addendum固定evaluator driver hash。不得直接改用舊Candidate A evaluator。

## 禁止事項

不得為H1重新生成；不得用evaluator結果選擇、撤回或接受個別repair；不得把raw packaging ablation混入四帳；不得修改Candidate B、Pipeline或Healer後重跑相同28題。
