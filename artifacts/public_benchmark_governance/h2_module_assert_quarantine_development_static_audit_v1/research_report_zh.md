# H2 module assert quarantine 靜態研究報告

規則 `module_assert_entrypoint_selftest_quarantine_v0` 狀態為 `development_candidate_not_frozen`。本 audit 僅涵蓋 Stage2／MBPP+：
4B 凍結證據中全部 68 個 module-level assert 格，以及
9B 正式 Conditional23 的 23 格。

4B：48 格轉換、20 格 abstain；
abstain 分組為 entry-point 缺失／非唯一 9、
複雜／外部狀態／來源不完整 8、
多 assert 3。
9B Conditional23：23 格轉換。
4B 轉換格中的既有原 PASS 控制格為 25；此值只在決策完成後統計，
未提供給規則，也未用於挑選轉換。

既有核對值是否完全一致：false。
差異已定位：參考的複雜／外部狀態 11 是「來源不完整 6」與「predicate
複雜／外部狀態 5」的非互斥相加，其中 3 格同時具備兩種旗標。逐格決策採唯一
primary reason 時不得重複扣除，因此 4B 唯一 abstain 為 20、轉換為 48。
若為得到 45 而排除純 builtin `abs(entrypoint(...)-literal)`，結構相同的兩個
9B Conditional23 格也會被排除，與單一 cohort-agnostic 規則及 9B 23/23 衝突。
規則只把唯一且明確的 entry-point 自我測試 assert 移至
`if __name__ == "__main__":`，不刪除 assert、不修改函式內容。
研究主張僅限解除 import 時的該 assert 阻斷，不主張程式因此 PASS。

本輪零模型呼叫、零 candidate execution、零 EvalPlus、零重新評分；
未套用或修改既有 H1。
