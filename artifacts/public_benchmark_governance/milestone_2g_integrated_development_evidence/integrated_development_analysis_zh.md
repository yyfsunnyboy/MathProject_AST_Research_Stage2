# Milestone 2G：60題MBPP+ development整合證據

## 結論

資料充分性決策：`PROCEED_TO_NARROW_HEALER_AND_SCAFFOLD_DESIGN`。現有development證據已足以**實作**一條窄範圍、evaluator-blind且有明確abstention的entry-point alias候選規則；這不代表規則已驗證、可部署或可宣稱提升correctness，也不代表Scaffold v1已凍結。

## 60題、300 identities、600 programs的差別

60題指60個unique task IDs，不能把同題五個seed說成五題。每題有seed 11、22、33、44、55，因此共有300個unique task-seed identities。每個identity各有兩個paired treatments，所以保存了600個generated programs：discovery 20題是P0與Scaffold v0共200個programs；expansion 40題是P0與Candidate A共400個programs。Pipeline是同一program的第二個評估帳，不是額外program，也不是Healer。

## Candidate A改善與未升格原因

Expansion中Candidate A把Pipeline-corrected pass由38/200（19%）提高到53/200（26.5%）；30 rescues、15 regressions，exact McNemar p=0.0356978。correctness improvement條件成立，但strict Python-only只有178/200（89%），低於預註冊90%，所以format gate失敗，Candidate A仍不得升格official v1。

## Scaffold候選方向

Candidate A的147個Pipeline failures中，18格／8題有length termination，19格／10題有compile failure，兩者重疊15格。這支持把『簡潔且完整、在輸出上限內完成』列為Candidate B的設計方向，但只是設計假說：truncation沒有保存遺失的後半段，不能由Healer補寫；compile failure也包含異質原因。

本輪只保留一個`candidate_not_frozen` exact-text草案，保留no-fence、output-only與exact entry-point要求，並加入concise/complete方向。不得修改後在同40題重跑；未來若測試必須另立前瞻protocol與使用未啟用development tasks。

## 可能交給Healer的錯誤

唯一達到實作門檻的窄候選是`entrypoint_alias_unique_arity_compatible_v0`：42格、16個unique tasks。trigger只用AST、top-level函式數、預期名稱與model-visible positional arity；transform只追加名稱alias，不改body。只要parse失敗、truncation、多函式、arity不相容、目標名稱已綁定、decorator／binding有歧義或需要改body，就必須abstain。規則接受不得查看修後evaluator pass/fail。

## 必須abstain的錯誤

generic evaluator unknown無法區分functional assertion、runtime、name或dependency原因；truncation缺少未生成內容；一般syntax error過度異質；多個候選函式或arity不相容也無唯一安全轉換。這些一律不能自動修復。format／packaging應由Scaffold或既有Pipeline處理，Pipeline correction不得稱為Healer。

## 是否啟用剩餘56題？

目前不需要先啟用全部剩餘56題，因為目標只是判斷能否進入窄規則與Candidate B的實作／預註冊階段：entry-point候選已有跨多題支持、反例、靜態trigger、安全門與abstention；Scaffold的concise/complete方向也有8至10個unique tasks支持。下一里程碑可實作候選資產並凍結獨立前瞻protocol，但不能把本輪候選視為verified rule。剩餘56題應保留為未啟用development資源，供未來前瞻測試或候選失敗後另立deterministic expansion；本輪不選題、不生成。

## 外推限制

所有結論只限這60題development、既定模型／sampling／treatments與保存的靜態診斷。未讀取validation、confirmatory、excluded historical或sealed reserve，不能外推到封存資料或其他模型。
