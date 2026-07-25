# Ab2gA-short-v1 生成與評測預登錄

狀態：`preregistered_frozen_not_executed`

本研究是 development／condition-transfer 增量實驗，只使用既有 development20；不得宣稱為未見 task 的 confirmatory validation。

## 鷹架凍結

Ab2gA-short-v1 僅由正式凍結 Ab2g 原 bytes、單一 LF 分隔及唯一增量段落組成。Ab2g 不改寫、不刪減、不重新排版。Ab2g SHA-256 為 `31969abe8799b1846c488d3f7fca558af79875c7eb90ab76db7a6b62ad263305`；增量段落 SHA-256 為 `20a24ce1cecc28f4d021a36b24a706f20d781fc394a542800ae27dbcf8b4ac6a`；合成鷹架 SHA-256 為 `0c1bc9c4865eafe8f07917f9e58fa0ff04988263db3bc22adcfc99ecf69300ff`。

## 設計

固定 20 題、seeds 11／22／33／44／55；qwen3.5:4b 與 qwen3.5:9b 各 100 格，共 200 格。模型 digest、Q4_K_M 量化及 temperature=0.2、top_p=0.95、top_k=20、num_ctx=8192、num_predict=2048、thinking=false、stream=false 均沿用正式 manifest，不換題、不換 seed、不改參數。

主要比較為 Ab2g-Raw vs Ab2gA-short-v1-Raw，以及 Raw vs 既有 frozen H1。H2 僅按 SHA `dbd96fc3c1228f74c784e2444350102de121d4e202dcb0075aad214090bbfa18` 作前瞻固定的 development-candidate 評測；其狀態是 `development_candidate_not_frozen`，不得稱為 frozen Healer。

## 指標與配對

預先報告 Base／Plus／strict pass、可抽取率、可解析率、可執行率、eligible、transformed、abstained、blocker removed、verified rescue、partial repair、regression、preserved pass、failure layer、failure chain，以及以 model × task × seed 為單位的逐格配對轉換。

本輪模型呼叫、candidate 執行、EvalPlus、Raw 假資料、cohort 擴充，以及 H1／H2／Ab2g／舊結果修改均為零。
