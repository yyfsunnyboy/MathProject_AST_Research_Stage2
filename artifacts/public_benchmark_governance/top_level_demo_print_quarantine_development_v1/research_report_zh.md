# 頂層示範 print 隔離規則 development 評測

本研究僅為 development candidate 評測，不構成 confirmatory validation。

- 全 cohort 靜態盤點：500 格（4B 200、9B 300）；命中 21、abstain 479。
- Raw 控制：PASS 128、FAIL 358、未正式評測 14。
- 新規則單獨臂：17/21 strict PASS；保留 17 個命中的 Raw PASS，4 個 Raw FAIL 均未救援。
- 新規則：verified rescue 0、regression 0、unchanged failure 4。
- H2 使用既有精確規則 SHA `dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18`，效果獨立記錄，未歸功於新規則。
- 新執行 EvalPlus 50 次；模型呼叫與模型生成皆為 0。

依預登錄 criterion B，最終狀態為 `development_candidate_not_frozen`。
