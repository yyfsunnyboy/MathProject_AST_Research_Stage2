# Ab2gA-short-v1 中文研究說明

H2 功能評測已於 commit `30ed664e2bf75e8afca612e8eec99e7c75b87f61` 完成，觀察到 71 transformed、46 partial repair、0 rescue、0 regression；決策為 `development_candidate_not_frozen`。本次只凍結下一輪演算法鷹架的設計、完整提示與評測預登錄，不生成答案也不執行程式。

研究問題是：在不改動既有 Ab2g 輸出約束的前提下，加入短版內部演算法檢查段落，是否改善 Raw 語意正確率及失敗分布。這是 development／condition-transfer 證據，不是未見題目的驗證。

固定題目為：Mbpp/633、Mbpp/769、Mbpp/453、Mbpp/259、Mbpp/739、Mbpp/124、Mbpp/72、Mbpp/792、Mbpp/435、Mbpp/597、Mbpp/732、Mbpp/721、Mbpp/765、Mbpp/777、Mbpp/473、Mbpp/420、Mbpp/742、Mbpp/279、Mbpp/125、Mbpp/603。每題固定五個 seeds，4B／9B 使用同一題目與 seed 配對，共 200 個唯一 cell identity。完整 prompt 逐格保存在 `complete_prompt_manifest.jsonl`；因 seed 與模型不改變 prompt 文字，200 格對應 20 個唯一 prompt hashes，hash 集合的 SHA-256 為 `66ad2eebaa5002c8dbd34fc5c420ed53e8c0337e7ae69d548213397f0f7820ed`。

H1 保持既有 frozen evaluator-blind healer 角色；H2 保持指定 rule SHA，僅作前瞻固定的 development-candidate 分析。任何後驗規則修改、格子排除或 confirmatory 宣稱都不允許。
