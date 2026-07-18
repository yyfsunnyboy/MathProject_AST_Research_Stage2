# MBPP+ 2×2 development qualification v1

目前正式2×2尚未完成：Candidate A有correctness改善但format gate失敗；Healer只有靜態安全證據，尚無完整H0/H1功能帳；validation名單仍未讀取也未凍結。

## 既有600程式的Healer稽核

已凍結1200個development-only評估帳：每份既有Pipeline-normalized程式各有H0原樣帳與H1候選帳。兩帳共享generation與Pipeline輸入；不得重新生成、選擇性接受或在看到evaluator結果後撤回個別轉換。本輪尚未執行評估。

## Candidate B的新資料資格測試

從既有公開hash排序的未使用56題中，固定取排名41至68的28題；不讀prompt、答案或tests，並保留另外28題。每題5 seeds，P0與Candidate B各140 generations，共280；之後同一generation分H0/H1，形成560個development-only評估帳。

Candidate B只是`frozen_experimental_candidate_not_official_p1`。它不能回到Candidate A的40題重測；若失敗，不得修改後重跑這28題。Healer也必須在P0與P1使用完全相同source、rule order與guards。

## 為何仍不能進validation

本次只凍結下一階段protocol與名單，未建立run directory、未呼叫模型、未執行EvalPlus。只有完成新development qualification、依預註冊gates分別凍結final P1與final Healer，再凍結validation identities、sampling與analysis claim rules，才能啟用正式validation。
