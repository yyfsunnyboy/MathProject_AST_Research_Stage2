# MBPP+ evaluator-blind Healer candidate v0 development audit

這是development-only候選實作與靜態安全稽核，不是正式Healer凍結，也不是功能修復成效證明。本輪只重用既有600份Pipeline-normalized development程式，沒有呼叫模型或EvalPlus。

## 候選規則

唯一規則只在程式可解析、預期名稱尚未被綁定、恰有一個無decorator的同步頂層函式，且其參數數量相容於prompt中可見呼叫時，於檔尾追加名稱alias。原函式body、control flow與imports完全不改。任何模糊情況都維持原輸出並abstain。

## 2×2相容性

Pipeline一定先執行；H0保留normalized source，H1才呼叫此候選。API沒有P0/P1、Scaffold或evaluator欄位，因此兩種prompt條件使用相同版本、單一規則順序及相同guards。Pipeline extraction、fence stripping與plain-text normalization不計入Healer。

## Development-only觸發

guard前靜態shape signature在P0為40格、Scaffold為2格。套用truncation等全部guards後，P0實際安全觸發並轉換39格／16題；Scaffold條件為2格／1題。P0少掉的一格是length-terminated輸出，依規則必須abstain。這些是靜態trigger與AST差異證據，不是evaluator驗證的repair success。

semantic risk仍為中等：被alias的唯一函式可能本身語意錯誤。因此未來只能前瞻比較同一generation的H0/H1帳，不能用pass/fail挑選是否接受修復。truncation、syntax、multiple functions、unknown與語意不確定案例全部abstain。

## 目前狀態

候選尚未凍結、尚未進入validation。正式2×2計畫仍須先凍結final P1、Healer source/hash/rule order/guards、Pipeline hash、validation identities與claim rules。
