# MBPP+ development expansion 預註冊與名單凍結（Milestone 2D）

## 治理範圍

本 addendum 不改寫原 frozen split；它引用原 split hash 與 starting HEAD，僅凍結 development expansion overlay。本輪沒有模型呼叫、EvalPlus 執行、run directory、Scaffold v1 generation plan 或 Healer 建置。Candidate A 保持 candidate-only，exact UTF-8 text 未修改。

選取只使用 dataset 名稱／版本、task_id、frozen governance role 與固定公開 seed/salt；未讀取 prompt、答案、tests、canonical solution、模型輸出、錯誤類別或通過結果。

## 凍結統計

- Historical development pool：116 題。
- Discovery development：原20題，完整保留。
- 剩餘可選候選：96題。
- Expansion development：deterministic 選取40題。
- 合計：60個 unique task IDs。
- 未來每個 treatment 的 identities：60 × 5 seeds = 300 unique `task_id + seed`；本輪只凍結 identity 規格，不建立 run。
- 與 validation、internal/external confirmatory、excluded、sealed reserve 重疊：0。

## 公開 deterministic selection 規格

- Selection seed：`20260718`
- Selection salt：`MathProject_AST_Research_Stage2|MBPP+|development_expansion_v1`
- Algorithm：`sha256(utf8(salt + LF + seed + LF + dataset + LF + dataset_version + LF + frozen_role + LF + task_id + LF)); sort by (selection_hash, task_id) ascending; select first 40 of the 96 non-active historical-development candidates`
- 無人工 override、換題或例外名單。

Exact preimage 是以下六欄以 LF 連接並保留最後 LF：`salt`、`seed`、`dataset`、`dataset_version`、`frozen_role`、`task_id`。

## 新增40題凍結名單

| Rank | task_id | Selection SHA-256 |
|---:|---|---|
| 1 | Mbpp/748 | `02315c2ba9052d56e48077cc2228eb14d65cea43397037964854d8e839c43ac1` |
| 2 | Mbpp/759 | `0240cfe3b8511005981e60d90c5449d5ffe39ad986c000b1284401ae638f1c0f` |
| 3 | Mbpp/430 | `04b317e0c52de2aca97c891016cae83ecd7e239af8bf849b885caec4f96bf7ab` |
| 4 | Mbpp/67 | `0783ac3b67efba0ec5f0319f854a1a10047e1761bdf125fa6aedabbdaa454bff` |
| 5 | Mbpp/11 | `0e03a0cc03895ffa232e2cfc422c5d13fd440b2a649513e0f404b51161fa3d45` |
| 6 | Mbpp/162 | `0fcdbcbfc4cf03f11e6df5b6de94c55889732f30267db557cff9cf4e1fae0eb1` |
| 7 | Mbpp/432 | `141aa0d407393d603d6b3b28b0d2910d80a1bc00da08ef58ded86b118cbcdbf7` |
| 8 | Mbpp/572 | `171ffcf62f88b32e016baccc10d0579abe78df85305b14e899cfe6691f760f4e` |
| 9 | Mbpp/626 | `194e38ac79258cba687af40d40d2aca2eb5631f4a9d1d70c158cd8419a85f385` |
| 10 | Mbpp/138 | `1b41d11a21257bb47d923ca5f38151022077270a6ff60f0e801c87468a30bb67` |
| 11 | Mbpp/244 | `1bb470f126222701f9787a7e502a090a09e3bec338cc121849377f6f64cb530c` |
| 12 | Mbpp/735 | `1e98853609201d93bcabf9976fb7794c7056c822ec11303217054a616634491a` |
| 13 | Mbpp/14 | `1f7a557c8af7771681cc8c68972dc22a2198e0923708102105345515e0bcf684` |
| 14 | Mbpp/787 | `21f10250ed6f886dec105aab9a590e27463adfeeb7eb8449da707531e651283e` |
| 15 | Mbpp/722 | `23a67ab8dc16ad412577d04e3038354564ea1e4cab30b716b17d29827cca0cb3` |
| 16 | Mbpp/781 | `3133004aa89b9a900eb1ca15793b60c5c17908d8b8ec0c5fc02ac70ac2bd808e` |
| 17 | Mbpp/622 | `31a402722e9fc17e75e12a67b71daa15a794ac7b00fcd446390408da4865158b` |
| 18 | Mbpp/607 | `344eb178d9f407362a4a521d568822210249171ebd040566e12697766a277348` |
| 19 | Mbpp/410 | `34572e52f34a4929415573c1c37bec597877d33d3493bcfa2e126fb798d26830` |
| 20 | Mbpp/581 | `368ef52349661eee45d7246c2712a92fd2371738f3382189f1f0a20b478ce0de` |
| 21 | Mbpp/255 | `37d31b128d6f79d90748c675eca93c78778679694e010966f3134786df253cd9` |
| 22 | Mbpp/99 | `389380d5bebb827eae8d0f8e998ecbc14394deab54217fe05aff55404796cabd` |
| 23 | Mbpp/103 | `390826459331085aad4f5cbc16f1d611d85ef59a1dfd79f0363894e9f7e58ecc` |
| 24 | Mbpp/427 | `3af5c0b3122814a13806bccce5ed06ca648bac16a26a76bde1c6840306b86dd6` |
| 25 | Mbpp/6 | `3cf518d2382f744a01dbdd3486110a6324ebd20722235847431bf69030be08a2` |
| 26 | Mbpp/771 | `411d4d64a083463d4245e273df75205957eeed4a7d992c09db2df75d50483ada` |
| 27 | Mbpp/119 | `463633e2e189bd14e73a9e31665803c755a5f0bdddd068e4af15dd5208903b6d` |
| 28 | Mbpp/306 | `48413b00ae0ac08b565eb07c3c1b9ebfe213545e50688322622fc4bb2f206c8e` |
| 29 | Mbpp/620 | `4846832479e830a4a87fc99ec2b51962d5c990fb5196666fcb8e3b234ddfd61b` |
| 30 | Mbpp/237 | `4a0770102cda199c7952c982b2cde6652665d7e8826e5892e7c7d6431ecc1959` |
| 31 | Mbpp/440 | `4a912d6e5bda681a0de36f7fe637f8768000e9584087b1b6466298feba84dffc` |
| 32 | Mbpp/392 | `4d212ab5344fdcfac8336073fab3c98a682660093e24c62484a33e47f2b19463` |
| 33 | Mbpp/406 | `4e87308f80a665ddaf874592fa5fb624bfeaee0bf14ced01a9dd54e9803a369f` |
| 34 | Mbpp/419 | `521f125df9e9eb2fb99bfb124baecabd3a534ba07abe6e3c956a295e5beac740` |
| 35 | Mbpp/786 | `53467a70a52a62db16ad74e307dd08ca146193e8a4f3c51c2ebfe876b945f480` |
| 36 | Mbpp/16 | `553a107a02a37f801965d6c8cc3532ac6dce87121599116daedb3b8c914bb809` |
| 37 | Mbpp/576 | `57c0e967152ecbda1b375f6757539e04494f37fcc274031f6e3fa2178c943f97` |
| 38 | Mbpp/118 | `5858719cd0a6789f3a135c2ffab6b118b86478ee85a0d5905382d4cc4180212e` |
| 39 | Mbpp/615 | `593ce78585a82da2f4454200f22cfc7c34bb2b16311216058a2975c166713eee` |
| 40 | Mbpp/287 | `5c8690b3d8ac015ab02b1c95398a0c8eb484b42d9e58b77f1ef1a2ecd8075cf2` |

## Immutable references 與後續限制

- Original frozen split SHA-256：`3bb00bab0d9476412d03c67923c1db4ab1352f551f0e8020ee7e8cb7a367f9d4`。
- Original frozen split HEAD reference：`23a430538f44fbe8e57a025a19ca0f49778e1ab1`；本 addendum starting HEAD：`08764eb643947bbe23009bf4867e284f6500c0b7`。
- Candidate A exact text SHA-256：`bffa1e7e3d1ff77b0de326083bf6c7fd441b2f3b050b45e205a5ba51be87f058`；狀態為 `candidate_only_not_frozen`。
- 未來 treatment 的生成與評測必須另立預註冊 milestone；本 addendum 不授權模型、EvalPlus、Scaffold v1 或 Healer 執行。
