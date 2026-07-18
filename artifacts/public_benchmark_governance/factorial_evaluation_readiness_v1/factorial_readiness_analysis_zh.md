# MBPP+ 2×2 factorial evaluation readiness v1

本資產把正式研究目標轉成可機器驗證的帳務與前瞻計畫草案；目前仍是development-only，因final P1與final Healer尚未凍結，所以不得啟用validation。

## 正式四帳

- P0+H0：P0 generation經共同frozen Pipeline後直接評估。
- P0+H1：同一份P0 normalized output套用共同Healer後評估。
- P1+H0：P1 generation經同一Pipeline後直接評估。
- P1+H1：同一份P1 normalized output套用同版本Healer後評估。

H0/H1共享generation ID、raw SHA與Pipeline normalized input；Healer不得重新生成。Pipeline extraction、fence stripping與plain-text normalization不是Healer。

## Development-only觸發稽核

目前唯一eligible窄候選`entrypoint_alias_unique_arity_compatible_v0`在P0輸出觸發40格／16題，在既有Scaffold-like輸出觸發2格／1題。低觸發率不允許改變規則：P0與P1必須使用相同版本、順序、guards與abstention。

其他syntax、truncation與generic unknown仍分別為insufficient evidence或nonrepairable；format/packaging只屬Scaffold或Pipeline。逐規則完整分層統計在CSV。

## Validation啟用條件

必須先凍結final P1 exact text/hash、final Healer source/hash/rule order/guards、Pipeline source/hash、validation identities、模型與sampling、分析程式與claim rules。此前validation task清單保持空白，且不得執行正式generation或evaluation。

## Raw deployment packaging ablation

可另設raw deployment packaging ablation，但它不是正式2×2 factorial的一部分，不得取代Pipeline或Healer帳，結果必須獨立標示。
