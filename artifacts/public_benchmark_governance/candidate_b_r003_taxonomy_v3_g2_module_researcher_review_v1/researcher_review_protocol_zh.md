# Candidate B r003 taxonomy v3：G2_module researcher review v1

**明確聲明：`AI_ASSISTED_SECOND_PASS_NOT_FORMAL_HUMAN_ADJUDICATION`**

本 revision 目錄名含 `researcher_review_v1`，但內容為 AI-assisted second-pass（含第01–03格既有 session 覆核與第04–27格批次 second-pass）。**不是** formal human adjudication，**不**計算 Cohen’s kappa，**不**宣稱雙真人盲審。

## 凍結基準

- freeze baseline commit：`ba2244f3804232a2ea2dd52f9c3d60f9e35b46b6`
- AI provisional revision：`candidate_b_r003_taxonomy_v3_g2_module_ai_assisted_provisional_adjudication_v1`
- AI provisional CSV SHA256：`90d17695c25d4c1f054fa23949cbd5237fcfeb4ade80eb38175b3c022687b119`
- reviewer_id：`OPENAI_CODEX_AI_ASSISTED_REVIEW_20260721`
- 範圍：僅 `G2_module` 27 格；不分析其餘 420 格

## 唯讀原則

1. 不修改 AI provisional 目錄、CSV 內容或其 SHA。
2. Worksheet 中 `ai_*` 欄位為 AI 初判快照，覆核過程保持唯讀。
3. 第二遍裁決只寫入 `researcher_*`／`modified_*`／`modify_reason` 欄位。
4. 每列與 manifest／report 均標 `review_type=AI_ASSISTED_SECOND_PASS_NOT_FORMAL_HUMAN_ADJUDICATION`。
5. 不顯示 hidden expected／actual；不使用 H1 結果反推。
6. 不執行模型、EvalPlus、diagnostics、Healer、validation 或新 correctness 測試。
7. 刪除 top-level assert 最多視為解除 module 載入阻斷的候選 packaging 轉換，不視為安全 Healer。
8. 完成前不 commit／不 push。

## 操作結果

- 第01–03格：既有 ACCEPT 內容保持不變（僅補 `review_type`）。
- 第04–27格：獨立 second-pass 批次寫入；每格含具體 notes。
- 產物見同目錄 manifest、worksheet、diff／summary CSV 與 report。
