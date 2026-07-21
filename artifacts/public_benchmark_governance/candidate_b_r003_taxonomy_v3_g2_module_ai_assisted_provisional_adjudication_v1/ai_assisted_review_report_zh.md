# Candidate B r003 taxonomy v3：G2_module AI-assisted provisional adjudication v1

狀態：`AI_ASSISTED_PROVISIONAL_NOT_FORMAL_HUMAN_ADJUDICATION`。這不是正式人工裁決，也不是兩位真人獨立盲審；不計算 Cohen’s kappa。

本 revision 只使用公開 task contract、完整 H0 required-function source、module-level executable statements、imports/API 與既有 coarse diagnostic phase/class/line。未使用 hidden expected/actual、correctness 結果、exception message 或 traceback。

## 彙總

### Primary layer

| Layer | Cells |
|---|---:|
| L0 | 0 |
| L1 | 0 |
| L2 | 2 |
| L3 | 0 |
| L4 | 25 |
| L5 | 0 |
| UNRESOLVED | 0 |

### Proposed Healer eligibility

| Status | Cells |
|---|---:|
| eligible | 0 |
| conditional | 23 |
| abstain | 4 |

### Mechanism tags（非互斥）

| Tag | Cells |
|---|---:|
| `algorithmic_error` | 12 |
| `control_flow_failure` | 5 |
| `edge_case_omission` | 3 |
| `mathematical_error` | 8 |
| `model_assembly_failure` | 27 |
| `module_level_executable_assertion` | 25 |
| `parameter_semantics_swap` | 3 |
| `schema_mismatch` | 2 |
| `semantic_goal_drift` | 7 |
| `stdlib_regex_pattern_construction` | 1 |
| `text_parsing_control_flow_failure` | 1 |

## 逐格 evidence packet 與 provisional adjudication

### 01. `000357b8ea9e8c7519556e3a8c85625c29516c022be9ed61c9a8fdd3d229c169`

- Identity：task `Mbpp/742`；seed `33`；cell `640c7544c87c0f5b40cf6113d1342ee47207bff3568a4fff235e49d7f5a518b6`
- Required entry point：`area_tetrahedron(a)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `6`；AST `Assert/Constant`
- Imports：`["math"]`
- API calls：`["abs","area_tetrahedron"]`

公開 task contract：

```text
"""
Write a function to caluclate the area of a tetrahedron.
assert area_tetrahedron(3)==15.588457268119894
"""
```

Required function完整 source（原行 3–4）：

```python
def area_tetrahedron(a):
    return a**2 * (1 + 5**0.5) / 4
```

Module-level executable statement完整內容：

```python
lines 6-6:
assert abs(area_tetrahedron(3) - 15.588457268119894) < 1e-10
```

Diagnostic最少必要前後文：

```text
4:     return a**2 * (1 + 5**0.5) / 4
5:
6: assert abs(area_tetrahedron(3) - 15.588457268119894) < 1e-10
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"mathematical_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The tolerance assertion is a model-added variant rather than an AST-exact public assertion; it is nevertheless consistent with the public numeric example.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The required function uses a formula inconsistent with the public tetrahedron example, and the model-added executable assertion turns that public mismatch into the observed module-stage failure. Assert removal is only a candidate packaging rule and is not declared safe or sufficient.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/742","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=000357b8ea9e8c7519556e3a8c85625c29516c022be9ed61c9a8fdd3d229c169;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=640c7544c87c0f5b40cf6113d1342ee47207bff3568a4fff235e49d7f5a518b6","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 02. `01b6bac38cef8f198113a5cd475e8be41beccd60d7c559172443b76df714e34c`

- Identity：task `Mbpp/138`；seed `33`；cell `49fbbe8f8a8ca4e49bd79707da38c3cf1246450da8809ec8d4f7ce38f3977253`
- Required entry point：`is_Sum_Of_Powers_Of_Two(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `4`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["is_Sum_Of_Powers_Of_Two","print"]`

公開 task contract：

```text
"""
Write a python function to check whether the given number can be represented as sum of non-zero powers of 2 or not.
assert is_Sum_Of_Powers_Of_Two(10) == True
"""
```

Required function完整 source（原行 1–2）：

```python
def is_Sum_Of_Powers_Of_Two(n):
    return n > 0 and (n & (n - 1)) == 0
```

Module-level executable statement完整內容：

```python
lines 4-4:
assert is_Sum_Of_Powers_Of_Two(10) == True

lines 5-5:
print(is_Sum_Of_Powers_Of_Two(10))
```

Diagnostic最少必要前後文：

```text
2:     return n > 0 and (n & (n - 1)) == 0
3:
4: assert is_Sum_Of_Powers_Of_Two(10) == True
5: print(is_Sum_Of_Powers_Of_Two(10))
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"semantic_goal_drift","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","semantic_goal_drift","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The natural-language phrase 'sum of non-zero powers of 2' can be read broadly, but the public example unambiguously requires 10 to be accepted.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function implements a single-power-of-two predicate, contradicting the public example; the copied executable assertion exposes that semantic mismatch during module execution. Assert removal remains an unvalidated candidate only.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/138","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=01b6bac38cef8f198113a5cd475e8be41beccd60d7c559172443b76df714e34c;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=49fbbe8f8a8ca4e49bd79707da38c3cf1246450da8809ec8d4f7ce38f3977253","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 03. `0460f62eee335e54ae79d20dba3f1c72d36982ade60d364ec6b3f5aa8c80feed`

- Identity：task `Mbpp/739`；seed `22`；cell `986356145523dd664151d8e0b78ce04d5fdfcdbb39014eb82a9194d7eb1cb050`
- Required entry point：`find_Index(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `9`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_Index","len","str"]`

公開 task contract：

```text
"""
Write a python function to find the index of smallest triangular number with n digits.
assert find_Index(2) == 4
"""
```

Required function完整 source（原行 1–7）：

```python
def find_Index(n):
    k = 1
    while True:
        t = (k * (k + 1)) // 2
        if len(str(t)) == n:
            return k - 1
        k += 1
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert find_Index(2) == 4
```

Diagnostic最少必要前後文：

```text
7:         k += 1
8:
9: assert find_Index(2) == 4
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example directly fixes the required index convention.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The loop identifies the first n-digit triangular number but returns k-1, conflicting with the public index 4; the public assertion then blocks module execution. Assert removal is not presumed to repair the algorithm.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/739","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=0460f62eee335e54ae79d20dba3f1c72d36982ade60d364ec6b3f5aa8c80feed;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=986356145523dd664151d8e0b78ce04d5fdfcdbb39014eb82a9194d7eb1cb050","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 04. `0833737e006fd2c6b58fc71e5f03d64bd4b088689b09734f808c776659507990`

- Identity：task `Mbpp/138`；seed `22`；cell `64187ed15da3a753654af4583d63c98578716b198ba919db3ddb1b1fb6855fbc`
- Required entry point：`is_Sum_Of_Powers_Of_Two(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `12`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["is_Sum_Of_Powers_Of_Two"]`

公開 task contract：

```text
"""
Write a python function to check whether the given number can be represented as sum of non-zero powers of 2 or not.
assert is_Sum_Of_Powers_Of_Two(10) == True
"""
```

Required function完整 source（原行 1–10）：

```python
def is_Sum_Of_Powers_Of_Two(n):
    if n <= 0:
        return False
    while n > 1:
        if (n & 1) == 1 and n != 3:
            break
        n >>= 1
    else:
        return True
    return n == 2
```

Module-level executable statement完整內容：

```python
lines 12-12:
assert is_Sum_Of_Powers_Of_Two(10) == True
```

Diagnostic最少必要前後文：

```text
10:     return n == 2
11:
12: assert is_Sum_Of_Powers_Of_Two(10) == True
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","control_flow_failure","model_assembly_failure"]`
- Confidence：`MEDIUM`
- Uncertainty：The exact intended characterization beyond the public example is not fully stated, although the public case is decisive for this observation.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The bit-shift control flow returns false for the public input 10, and the copied assertion exposes that semantic/control-flow error at module load. Assert deletion is only a candidate packaging transformation.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/138","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=0833737e006fd2c6b58fc71e5f03d64bd4b088689b09734f808c776659507990;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=64187ed15da3a753654af4583d63c98578716b198ba919db3ddb1b1fb6855fbc","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 05. `111a968cb6674525f58b26a0484603b9765056f5566cec9589d61af3733bc4c1`

- Identity：task `Mbpp/440`；seed `11`；cell `2eb6ecf61e5ca5d4b075519d27307b0b939afaefe5939cd35fb7cc8ceb140a4b`
- Required entry point：`find_adverb_position(sentence: str)`
- Diagnostic：phase `G2_module`；class `ValueError`；candidate line `7`；AST `Raise/Name`
- Imports：`["re"]`
- API calls：`["ValueError","enumerate","find_adverb_position","len","re.match","sentence.split","word.lower"]`

公開 task contract：

```text
"""
Write a function to find the first adverb and their positions in a given sentence.
assert find_adverb_position("clearly!! we can see the sky")==(0, 7, 'clearly')
"""
```

Required function完整 source（原行 1–7）：

```python
def find_adverb_position(sentence: str):
    import re
    words = sentence.split()
    for i, word in enumerate(words):
        if re.match(r'^\w+ly$', word.lower()):
            return (i * 7 + len(word), i * 7 + len(word) - 1, word)
    raise ValueError("No adverb found")
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert find_adverb_position("clearly!! we can see the sky")==(0, 7, 'clearly')
```

Diagnostic最少必要前後文：

```text
5:         if re.match(r'^\w+ly$', word.lower()):
6:             return (i * 7 + len(word), i * 7 + len(word) - 1, word)
7:     raise ValueError("No adverb found")
8:
9: assert find_adverb_position("clearly!! we can see the sky")==(0, 7, 'clearly')
```

Provisional adjudication：

- Primary：`L4`；secondary：`[]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"text_parsing_control_flow_failure","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"}]`
- Mechanisms：`["text_parsing_control_flow_failure","control_flow_failure","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The contract specifies the public punctuation-bearing example but does not define behavior when no adverb exists.
- Proposed Healer eligibility／decision：`abstain`／`not_run`
- Rationale：The anchored regex rejects the public token containing trailing punctuation, so the required function reaches its explicit raise while the module assertion calls it. Repair would require choosing tokenization and position semantics, so no unique mechanical root repair is established.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/440","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=111a968cb6674525f58b26a0484603b9765056f5566cec9589d61af3733bc4c1;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=2eb6ecf61e5ca5d4b075519d27307b0b939afaefe5939cd35fb7cc8ceb140a4b","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 06. `147d093943f1f9676c4d779f88a7478b62c2a71021f831900f136291bee3f2eb`

- Identity：task `Mbpp/430`；seed `44`；cell `7ce98a367f29080d205ac02e5b76248df7a4c714c1b70af8f871c1f3459bc3e7`
- Required entry point：`parabola_directrix(a, b, c)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `14`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["ValueError","parabola_directrix"]`

公開 task contract：

```text
"""
Write a function to find the directrix of a parabola.
assert parabola_directrix(5,3,2)==-198
"""
```

Required function完整 source（原行 1–11）：

```python
def parabola_directrix(a,b,c):
    # Given quadratic equation y = ax^2 + bx + c in vertex form: x = (y - k)/a where a is coefficient of x^2?
    # Actually, standard parabola opening sideways or up/down. The problem likely refers to vertical axis parabola y=ax^2+bx+c
    # For y = a(x-h)^2 + k -> directrix is y = k - p where 4p = 1/a => p = 1/(4a)
    # Vertex (h,k): h = -b/(2a), k = c - b^2/(4a)
    # Directrix: y = k - 1/(4a) = c - b^2/(4a) - 1/(4a) = c - (b^2+1)/(4a)

    if a == 0:
        raise ValueError("Coefficient 'a' cannot be zero for a parabola")

    return c - ((b**2 + 1) / (4 * a))
```

Module-level executable statement完整內容：

```python
lines 14-14:
assert parabola_directrix(5,3,2)==-198
```

Diagnostic最少必要前後文：

```text
12:
13: # Verification with given test case
14: assert parabola_directrix(5,3,2)==-198
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"mathematical_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","semantic_goal_drift","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The terse natural-language contract omits the intended formula, but the public numeric example is explicit.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The implemented standard vertical-parabola formula does not satisfy the public contract value; the copied assertion exposes the mathematical goal mismatch during module execution. No formula rewrite is Healer-eligible.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/430","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=147d093943f1f9676c4d779f88a7478b62c2a71021f831900f136291bee3f2eb;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=7ce98a367f29080d205ac02e5b76248df7a4c714c1b70af8f871c1f3459bc3e7","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 07. `1ed09edb92c4da77d9ccb4eac0e420c2cbd4319a9d8a55e3340ea9f1a20544d8`

- Identity：task `Mbpp/787`；seed `33`；cell `291e1df791e7d75a35f7b6232af3516fd74ea360fcd7609f1dd38f4b05a859b9`
- Required entry point：`text_match_three(text)`
- Diagnostic：phase `G2_module`；class `PatternError`；candidate line `4`；AST `Return/Name`
- Imports：`["re"]`
- API calls：`["bool","print","re.search","text_match_three"]`

公開 task contract：

```text
"""
Write a function that matches a string that has an a followed by three 'b'.
assert not text_match_three("ac")
"""
```

Required function完整 source（原行 3–4）：

```python
def text_match_three(text):
    return bool(re.search(r'a\b{3}', text))
```

Module-level executable statement完整內容：

```python
lines 6-6:
assert not text_match_three("ac")

lines 7-7:
print("All tests passed.")
```

Diagnostic最少必要前後文：

```text
2:
3: def text_match_three(text):
4:     return bool(re.search(r'a\b{3}', text))
5:
6: assert not text_match_three("ac")
```

Provisional adjudication：

- Primary：`L4`；secondary：`[]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"stdlib_regex_pattern_construction","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"}]`
- Mechanisms：`["stdlib_regex_pattern_construction","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：A valid regex could be written in multiple ways; source evidence does not establish a unique invariant-preserving token replacement.
- Proposed Healer eligibility／decision：`abstain`／`not_run`
- Rationale：The required function constructs a malformed stdlib regular expression before returning, producing the observed G2 failure when called by the module assertion. This is general runtime/API assembly, not Domain API or infrastructure.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/787","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=1ed09edb92c4da77d9ccb4eac0e420c2cbd4319a9d8a55e3340ea9f1a20544d8;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=291e1df791e7d75a35f7b6232af3516fd74ea360fcd7609f1dd38f4b05a859b9","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 08. `200edc3e0eec7ea9c2f029ace4027b019b020d97c66d503db848f9ff332ffc06`

- Identity：task `Mbpp/739`；seed `55`；cell `f30e88e1c07b06c6fdc11213bea99ef203e929783f8b5137d71e67969550c021`
- Required entry point：`find_Index(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `9`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_Index","len","str"]`

公開 task contract：

```text
"""
Write a python function to find the index of smallest triangular number with n digits.
assert find_Index(2) == 4
"""
```

Required function完整 source（原行 1–7）：

```python
def find_Index(n):
    k = 1
    while True:
        t = k * (k + 1) // 2
        if len(str(t)) == n:
            return k - 1
        k += 1
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert find_Index(2) == 4
```

Diagnostic最少必要前後文：

```text
7:         k += 1
8:
9: assert find_Index(2) == 4
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example directly fixes the required index convention.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function returns k-1 after finding the first n-digit triangular number and conflicts with the public value; its copied assertion then interrupts module execution.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/739","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=200edc3e0eec7ea9c2f029ace4027b019b020d97c66d503db848f9ff332ffc06;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=f30e88e1c07b06c6fdc11213bea99ef203e929783f8b5137d71e67969550c021","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 09. `20eb64bfb9e51b94a4d68b6dc2bbbc981199b59d0671e34d0df1695b0d261879`

- Identity：task `Mbpp/430`；seed `11`；cell `d7db6cb73b9f5f7c5693a194dcc4d3738bade6d02d719e50008a12429c1b0d7c`
- Required entry point：`parabola_directrix(a, b, c)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `11`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["ValueError","abs","int","parabola_directrix"]`

公開 task contract：

```text
"""
Write a function to find the directrix of a parabola.
assert parabola_directrix(5,3,2)==-198
"""
```

Required function完整 source（原行 1–9）：

```python
def parabola_directrix(a,b,c):
    if a == 0: raise ValueError("Coefficient 'a' cannot be zero for a parabola.")
    discriminant = b**2 - 4*a*c
    if discriminant < 0: return None
    x_vertex = -b / (2 * a)
    y_vertex = c + (discriminant) / (4 * a)
    p = 1.0 / (4 * abs(a))
    directrix_y = y_vertex - p if a > 0 else y_vertex + p
    return int(directrix_y)
```

Module-level executable statement完整內容：

```python
lines 11-11:
assert parabola_directrix(5,3,2)==-198
```

Diagnostic最少必要前後文：

```text
9:     return int(directrix_y)
10:
11: assert parabola_directrix(5,3,2)==-198
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"control_flow_failure","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","control_flow_failure","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public contract is terse, but the negative-discriminant early return visibly conflicts with the supplied example.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function returns None for the public parameters before computing a directrix, so the copied assertion exposes a semantic/control-flow failure at module load.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/430","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=20eb64bfb9e51b94a4d68b6dc2bbbc981199b59d0671e34d0df1695b0d261879;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=d7db6cb73b9f5f7c5693a194dcc4d3738bade6d02d719e50008a12429c1b0d7c","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 10. `225def7e7fc2e4f0bdbede03a1813db354a4eff641e2de7b042c07a5608f106e`

- Identity：task `Mbpp/581`；seed `44`；cell `2c8a29019eddb8bc7e24251236af213d7f100c8bcb4513e7f17aa8c9b6fa5c84`
- Required entry point：`surface_Area(base_edge, height)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `8`；AST `Assert/Constant`
- Imports：`["math"]`
- API calls：`["int","math.log10","math.sqrt","round","surface_Area"]`

公開 task contract：

```text
"""
Write a python function to find the surface area of a square pyramid with a given base edge and height.
assert surface_Area(3,4) == 33
"""
```

Required function完整 source（原行 1–6）：

```python
def surface_Area(base_edge, height):
    import math
    slant_height = math.sqrt(height**2 + (base_edge / 2)**2)
    base_area = base_edge ** 2
    lateral_area = 4 * (0.5 * base_edge * slant_height)
    return round(base_area + lateral_area, -int(math.log10(lateral_area))) if lateral_area > 0 else base_area
```

Module-level executable statement完整內容：

```python
lines 8-8:
assert surface_Area(3, 4) == 33
```

Diagnostic最少必要前後文：

```text
6:     return round(base_area + lateral_area, -int(math.log10(lateral_area))) if lateral_area > 0 else base_area
7:
8: assert surface_Area(3, 4) == 33
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"mathematical_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The benchmark's integer-valued public example constrains the requested result, while general rounding policy is not described.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function applies a magnitude-dependent rounding operation that does not satisfy the public surface-area example; the module assertion exposes the numerical error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/581","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=225def7e7fc2e4f0bdbede03a1813db354a4eff641e2de7b042c07a5608f106e;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=2c8a29019eddb8bc7e24251236af213d7f100c8bcb4513e7f17aa8c9b6fa5c84","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 11. `29c5dc38a71e4bf24dadf515e157b833b8a0d1b304c47bf98d36a325fbbe4342`

- Identity：task `Mbpp/739`；seed `44`；cell `d9af9e684995ae0fd31339af9a56a8984950683d6a2d1f208414807da68a7e69`
- Required entry point：`find_Index(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `9`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_Index","len","str"]`

公開 task contract：

```text
"""
Write a python function to find the index of smallest triangular number with n digits.
assert find_Index(2) == 4
"""
```

Required function完整 source（原行 1–7）：

```python
def find_Index(n):
    k = 1
    while True:
        t = k * (k + 1) // 2
        if len(str(t)) == n:
            return k - 1
        k += 1
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert find_Index(2) == 4
```

Diagnostic最少必要前後文：

```text
7:         k += 1
8:
9: assert find_Index(2) == 4
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example directly fixes the required index convention.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function returns k-1 for the first n-digit triangular number and conflicts with the public example; the assertion exposes this during module execution.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/739","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=29c5dc38a71e4bf24dadf515e157b833b8a0d1b304c47bf98d36a325fbbe4342;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=d9af9e684995ae0fd31339af9a56a8984950683d6a2d1f208414807da68a7e69","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 12. `34f117accef513aaccebfa5edabc725dbc78ef1301e0ac16b4fb794b619a477b`

- Identity：task `Mbpp/125`；seed `33`；cell `81b1b9916304cfbcfd7cf807cbc1ee2f749ea3ca71ed1310e7db39569bccbcbf`
- Required entry point：`find_length(s: str)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `18`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["abs","find_length","max"]`

公開 task contract：

```text
"""
Write a function to find the maximum difference between the number of 0s and number of 1s in any sub-string of the given binary string.
assert find_length("11000010001") == 6
"""
```

Required function完整 source（原行 1–15）：

```python
def find_length(s: str) -> int:
    max_diff = 0
    current_sum = 0

    for char in s:
        if char == '1':
            current_sum -= 1
        else:
            current_sum += 1

        # Track maximum difference seen so far (absolute value of sum)
        diff = abs(current_sum)
        max_diff = max(max_diff, diff)

    return max_diff
```

Module-level executable statement完整內容：

```python
lines 18-18:
assert find_length("11000010001") == 6
```

Diagnostic最少必要前後文：

```text
16:
17: # Test case from the prompt
18: assert find_length("11000010001") == 6
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","edge_case_omission","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：Only the public example is used; no hidden cases are consulted.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The implementation tracks absolute prefix imbalance rather than the maximum imbalance over every substring, and its public assertion exposes the algorithmic mismatch.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/125","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=34f117accef513aaccebfa5edabc725dbc78ef1301e0ac16b4fb794b619a477b;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=81b1b9916304cfbcfd7cf807cbc1ee2f749ea3ca71ed1310e7db39569bccbcbf","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 13. `375d13b5bd61ef0ee7c0e92979f8c002d2ac3e98adb41426e8b9d6e27b176399`

- Identity：task `Mbpp/410`；seed `33`；cell `8125ee6ba4083e73589b37f3bfd5b38b4b0f8dba482e530d889dad5b93078b36`
- Required entry point：`min_val(lst)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `43`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["ValueError","float","int","isinstance","min","min_val","nums.append"]`

公開 task contract：

```text
"""
Write a function to find the minimum value in a given heterogeneous list.
assert min_val(['Python', 3, 2, 4, 5, 'version'])==2
"""
```

Required function完整 source（原行 1–28）：

```python
def min_val(lst):
    if not lst:
        raise ValueError("List cannot be empty")

    # Initialize minimum with first element converted to float for comparison
    try:
        current_min = float(lst[0])
    except (TypeError, ValueError):
        return None

    for item in lst[1:]:
        try:
            val = float(item)
        except (TypeError, ValueError):
            continue

        if val < current_min:
            # If we find a numeric value smaller than current min,
            # check if original list has non-numeric items.
            # Since the problem implies finding minimum in mixed types where numbers are comparable,
            # and strings can't be numerically compared directly without conversion logic that might fail,
            # we assume only numeric values participate or return None for invalid comparisons.

            # However, looking at the test case: ['Python', 3, 2, 4, 5, 'version'] -> returns 2
            # This implies non-numeric items are ignored in comparison logic if they can't be converted to float.
            current_min = val

    return int(current_min) if isinstance(lst[0], (int, float)) and not lst[-1] == current_min else current_min
```

Module-level executable statement完整內容：

```python
lines 43-43:
assert min_val(['Python', 3, 2, 4, 5, 'version'])==2
```

Diagnostic最少必要前後文：

```text
41:     return int(min(nums))
42:
43: assert min_val(['Python', 3, 2, 4, 5, 'version'])==2
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"control_flow_failure","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","control_flow_failure","semantic_goal_drift","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：An alternate helper appears later, but the contract names only min_val; no alias inference is needed.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The required function returns None immediately when the first heterogeneous item is nonnumeric, so it never considers later numeric values required by the public example. The unused min_val_v2 does not change the required entry-point result.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/410","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=375d13b5bd61ef0ee7c0e92979f8c002d2ac3e98adb41426e8b9d6e27b176399;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=8125ee6ba4083e73589b37f3bfd5b38b4b0f8dba482e530d889dad5b93078b36","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 14. `3ad5d1b48a0b82e99b69138c0bbead12450913eb8b7b049c8c101fb9acc5a34b`

- Identity：task `Mbpp/777`；seed `55`；cell `814ae99fa94821a1c45cba8ccc28c1265070d5d60c28cb6ab46dd8e21e82fd84`
- Required entry point：`find_sum(lst)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `6`；AST `Assert/Constant`
- Imports：`["collections:Counter"]`
- API calls：`["Counter","find_sum","sum"]`

公開 task contract：

```text
"""
Write a python function to find the sum of non-repeated elements in a given list.
assert find_sum([1,2,3,1,1,4,5,6]) == 21
"""
```

Required function完整 source（原行 1–4）：

```python
def find_sum(lst):
    from collections import Counter
    counts = Counter(lst)
    return sum(num for num in lst if counts[num] == 1)
```

Module-level executable statement完整內容：

```python
lines 6-6:
assert find_sum([1,2,3,1,1,4,5,6]) == 21
```

Diagnostic最少必要前後文：

```text
4:     return sum(num for num in lst if counts[num] == 1)
5:
6: assert find_sum([1,2,3,1,1,4,5,6]) == 21
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"semantic_goal_drift","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","semantic_goal_drift","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The phrase 'non-repeated elements' is potentially ambiguous in isolation, but the public expected sum resolves duplicate-value treatment for this contract.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function sums only values occurring once, whereas the public example requires each distinct value once; the copied assertion exposes the semantic interpretation error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/777","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=3ad5d1b48a0b82e99b69138c0bbead12450913eb8b7b049c8c101fb9acc5a34b;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=814ae99fa94821a1c45cba8ccc28c1265070d5d60c28cb6ab46dd8e21e82fd84","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 15. `4583ad1011027d81314ddfb74bc8ec4cf1ae4feb9a37bac42da76177416c62c7`

- Identity：task `Mbpp/739`；seed `11`；cell `a1e491b6023eff1ff01bce581fcb87e45ab99377ee7e4ff34a09184291c24ade`
- Required entry point：`find_Index(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `12`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_Index","len","str"]`

公開 task contract：

```text
"""
Write a python function to find the index of smallest triangular number with n digits.
assert find_Index(2) == 4
"""
```

Required function完整 source（原行 1–10）：

```python
def find_Index(n):
    k = 1
    while True:
        t = (k * (k + 1)) // 2
        if len(str(t)) == n:
            return k - 1
        elif len(str(t)) > n and len(str((k-1) * k // 2)) < n:
            return k - 1
        else:
            k += 1
```

Module-level executable statement完整內容：

```python
lines 12-12:
assert find_Index(2) == 4
```

Diagnostic最少必要前後文：

```text
10:             k += 1
11:
12: assert find_Index(2) == 4
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The second branch does not alter the public off-by-one result.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：Both return branches use k-1 for the first n-digit triangular number, conflicting with the public index; the assertion then interrupts module execution.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/739","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=4583ad1011027d81314ddfb74bc8ec4cf1ae4feb9a37bac42da76177416c62c7;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=a1e491b6023eff1ff01bce581fcb87e45ab99377ee7e4ff34a09184291c24ade","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 16. `4f6a1f242e4b63146785d435f3e0bcf3a50933bc9aec8a6045795b5d4e998a4b`

- Identity：task `Mbpp/279`；seed `55`；cell `2e5a247ec2d18722e45b386bc657ccf5fe0e38f2d3acc8861945f152c09b8eac`
- Required entry point：`is_num_decagonal(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `7`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["abs","int","is_num_decagonal"]`

公開 task contract：

```text
"""
Write a function to find the nth decagonal number.
assert is_num_decagonal(3) == 27
"""
```

Required function完整 source（原行 1–5）：

```python
def is_num_decagonal(n):
    if n <= 0:
        return False
    k = int((2 * (n - 1) ** 0.5 + 1)) / 2
    return abs(k**3 // 4 - n) < 1e-9
```

Module-level executable statement完整內容：

```python
lines 7-7:
assert is_num_decagonal(3) == 27
```

Diagnostic最少必要前後文：

```text
5:     return abs(k**3 // 4 - n) < 1e-9
6:
7: assert is_num_decagonal(3) == 27
```

Provisional adjudication：

- Primary：`L2`；secondary：`["L4"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G3s","layer":"L2","mechanism":"numeric_output_contract_as_boolean","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_required_function_output"},{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"}]`
- Mechanisms：`["schema_mismatch","semantic_goal_drift","module_level_executable_assertion","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The function name starts with is_, but the explicit task description and numeric public result control the contract.
- Proposed Healer eligibility／decision：`abstain`／`not_run`
- Rationale：The public contract requires the nth decagonal number, while every normal path returns a boolean predicate. This is an observable numeric-output contract violation; the module assertion is a later failure-chain stage. Fixing it requires replacing the algorithm, not a thin wrapper.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/279","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=4f6a1f242e4b63146785d435f3e0bcf3a50933bc9aec8a6045795b5d4e998a4b;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=2e5a247ec2d18722e45b386bc657ccf5fe0e38f2d3acc8861945f152c09b8eac","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 17. `525f723f9a1c4712fdebc06ccdc6418f4de3a6e8651646cbec99288c5fee64b2`

- Identity：task `Mbpp/432`；seed `22`；cell `cbd27e8a1e95b28f9cde9964ae558596c8371767b9b25addd1612a57c646aa5f`
- Required entry point：`median_trapezium(a: int, b: int, c: int)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `6`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["median_trapezium","sorted"]`

公開 task contract：

```text
"""
Write a function to find the median length of a trapezium.
assert median_trapezium(15,25,35)==20
"""
```

Required function完整 source（原行 1–4）：

```python
def median_trapezium(a: int, b: int, c: int) -> float:
    """Calculate the median length of a trapezium given three side lengths."""
    sides = sorted([a, b, c])
    return (sides[0] + sides[-1]) / 2
```

Module-level executable statement完整內容：

```python
lines 6-6:
assert median_trapezium(15, 25, 35) == 20
```

Diagnostic最少必要前後文：

```text
4:     return (sides[0] + sides[-1]) / 2
5:
6: assert median_trapezium(15, 25, 35) == 20
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"parameter_semantics_swap","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","parameter_semantics_swap","mathematical_error","model_assembly_failure"]`
- Confidence：`MEDIUM`
- Uncertainty：The natural-language contract does not label the three parameters, but the public example establishes the required observable result.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function averages the smallest and largest of three values, which yields a value inconsistent with the public median-length example; the assertion exposes that parameter/geometry interpretation error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/432","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=525f723f9a1c4712fdebc06ccdc6418f4de3a6e8651646cbec99288c5fee64b2;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=cbd27e8a1e95b28f9cde9964ae558596c8371767b9b25addd1612a57c646aa5f","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 18. `629708e02e0157509188afabd3e23e38bf52328c6ba811dcf12363d83c7621a6`

- Identity：task `Mbpp/432`；seed `55`；cell `a731cf5bdf05e1ed765711e887b3b1b9b46159ada72943ebdd5a79475b2afef3`
- Required entry point：`median_trapezium(a, b, c)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `4`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["median_trapezium"]`

公開 task contract：

```text
"""
Write a function to find the median length of a trapezium.
assert median_trapezium(15,25,35)==20
"""
```

Required function完整 source（原行 1–2）：

```python
def median_trapezium(a,b,c):
    return (a+c)/2 if a+b==c else None
```

Module-level executable statement完整內容：

```python
lines 4-4:
assert median_trapezium(15,25,35)==20
```

Diagnostic最少必要前後文：

```text
2:     return (a+c)/2 if a+b==c else None
3:
4: assert median_trapezium(15,25,35)==20
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"control_flow_failure","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","control_flow_failure","parameter_semantics_swap","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The meaning of the third parameter is terse, but the added equality guard is unsupported by the public contract and rejects its example.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function adds an a+b==c guard and returns None for the public inputs, so the copied assertion exposes an unsupported control-flow condition.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/432","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=629708e02e0157509188afabd3e23e38bf52328c6ba811dcf12363d83c7621a6;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=a731cf5bdf05e1ed765711e887b3b1b9b46159ada72943ebdd5a79475b2afef3","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 19. `6367b7adf0dcc6a964ff129d3713184a0bf42b89530700ec8c0e33b1d14d5849`

- Identity：task `Mbpp/440`；seed `22`；cell `66dc9424d0a8471a861baeb69b47d429a130b1b96057f1b01327de9794c8a0a6`
- Required entry point：`find_adverb_position(sentence: str)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `10`；AST `Assert/Constant`
- Imports：`["re"]`
- API calls：`["ValueError","find_adverb_position","match.end","match.group","match.start","re.search"]`

公開 task contract：

```text
"""
Write a function to find the first adverb and their positions in a given sentence.
assert find_adverb_position("clearly!! we can see the sky")==(0, 7, 'clearly')
"""
```

Required function完整 source（原行 1–8）：

```python
def find_adverb_position(sentence: str):
    import re
    pattern = r'\b[a-zA-Z]+ly\b'
    match = re.search(pattern, sentence)
    if match:
        return (match.start(), match.end() - 1, match.group())
    else:
        raise ValueError("No adverb found in the given sentence.")
```

Module-level executable statement完整內容：

```python
lines 10-10:
assert find_adverb_position("clearly!! we can see the sky") == (0, 7, 'clearly')
```

Diagnostic最少必要前後文：

```text
8:         raise ValueError("No adverb found in the given sentence.")
9:
10: assert find_adverb_position("clearly!! we can see the sky") == (0, 7, 'clearly')
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"edge_case_omission","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","edge_case_omission","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public tuple fixes the position convention for the punctuation-bearing example; no hidden position cases are used.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The regex finds the public adverb, but the function returns an inclusive end index while the public contract expects 7; the copied assertion exposes the position-semantics error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/440","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=6367b7adf0dcc6a964ff129d3713184a0bf42b89530700ec8c0e33b1d14d5849;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=66dc9424d0a8471a861baeb69b47d429a130b1b96057f1b01327de9794c8a0a6","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 20. `730042eea50b8ad4aae34728ece3f1ab16b2bb97771f5b3ddd5e5745c7e71585`

- Identity：task `Mbpp/742`；seed `22`；cell `37c96fcf4dff81d30e88b15c50d3c05aabb3a98c13caefc114e14671b73670b9`
- Required entry point：`area_tetrahedron(edge)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `7`；AST `Assert/Constant`
- Imports：`["math"]`
- API calls：`["abs","area_tetrahedron","math.sqrt"]`

公開 task contract：

```text
"""
Write a function to caluclate the area of a tetrahedron.
assert area_tetrahedron(3)==15.588457268119894
"""
```

Required function完整 source（原行 3–5）：

```python
def area_tetrahedron(edge):
    """Calculate the surface area of a regular tetrahedron given its edge length."""
    return (math.sqrt(3) / 2) * (edge ** 2) * 4
```

Module-level executable statement完整內容：

```python
lines 7-7:
assert abs(area_tetrahedron(3) - 15.588457268119894) < 1e-9
```

Diagnostic最少必要前後文：

```text
5:     return (math.sqrt(3) / 2) * (edge ** 2) * 4
6:
7: assert abs(area_tetrahedron(3) - 15.588457268119894) < 1e-9
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"mathematical_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The tolerance assertion is a model-added variant, but it preserves the public numeric target.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The source multiplies a tetrahedron-area expression by four and produces a value inconsistent with the public example; the executable tolerance assertion exposes the formula error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/742","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=730042eea50b8ad4aae34728ece3f1ab16b2bb97771f5b3ddd5e5745c7e71585;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=37c96fcf4dff81d30e88b15c50d3c05aabb3a98c13caefc114e14671b73670b9","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 21. `7738db7659ec9333e7d321294197cb3c3fef5d5fc72f77a196e819256f5ed8b9`

- Identity：task `Mbpp/739`；seed `33`；cell `27db6ce43b7b468c4a4cc5c34b2386007cf54430f457ac5cbbf18c2331b4c114`
- Required entry point：`find_Index(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `9`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_Index","len","str"]`

公開 task contract：

```text
"""
Write a python function to find the index of smallest triangular number with n digits.
assert find_Index(2) == 4
"""
```

Required function完整 source（原行 1–7）：

```python
def find_Index(n):
    k = 1
    while True:
        t = (k * (k + 1)) // 2
        if len(str(t)) == n:
            return k - 1
        k += 1
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert find_Index(2) == 4
```

Diagnostic最少必要前後文：

```text
7:         k += 1
8:
9: assert find_Index(2) == 4
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example directly fixes the required index convention.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function returns k-1 after finding the first n-digit triangular number and conflicts with the public index; the copied assertion exposes the error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/739","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=7738db7659ec9333e7d321294197cb3c3fef5d5fc72f77a196e819256f5ed8b9;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=27db6ce43b7b468c4a4cc5c34b2386007cf54430f457ac5cbbf18c2331b4c114","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 22. `77ac3b8fbd623bdf0762d2ed6082720197b57f51a53b8c77fcd77523604f047d`

- Identity：task `Mbpp/777`；seed `44`；cell `e6edb29d32c7593fd9774360eb7e1f43e89004d741348a9d207eb3239ea11186`
- Required entry point：`find_sum(lst)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `6`；AST `Assert/Constant`
- Imports：`["collections:Counter"]`
- API calls：`["Counter","find_sum","sum"]`

公開 task contract：

```text
"""
Write a python function to find the sum of non-repeated elements in a given list.
assert find_sum([1,2,3,1,1,4,5,6]) == 21
"""
```

Required function完整 source（原行 1–4）：

```python
def find_sum(lst):
    from collections import Counter
    counts = Counter(lst)
    return sum(num for num in lst if counts[num] == 1)
```

Module-level executable statement完整內容：

```python
lines 6-6:
assert find_sum([1,2,3,1,1,4,5,6]) == 21
```

Diagnostic最少必要前後文：

```text
4:     return sum(num for num in lst if counts[num] == 1)
5:
6: assert find_sum([1,2,3,1,1,4,5,6]) == 21
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"semantic_goal_drift","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","semantic_goal_drift","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public expected sum resolves the possible ambiguity in 'non-repeated elements' for this task.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function excludes every repeated value instead of counting each distinct value once as required by the public example; the assertion exposes the semantic mismatch.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/777","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=77ac3b8fbd623bdf0762d2ed6082720197b57f51a53b8c77fcd77523604f047d;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=e6edb29d32c7593fd9774360eb7e1f43e89004d741348a9d207eb3239ea11186","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 23. `84f71b53c98028b255fd361fab6deec391cb7e68bf49bd27e8a27950260897d1`

- Identity：task `Mbpp/279`；seed `33`；cell `164e4d0b000ecd095f5ef3bfcf49984ab69dc951caabe5be7b141ce585100586`
- Required entry point：`is_num_decagonal(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `9`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["int","is_num_decagonal"]`

公開 task contract：

```text
"""
Write a function to find the nth decagonal number.
assert is_num_decagonal(3) == 27
"""
```

Required function完整 source（原行 1–6）：

```python
def is_num_decagonal(n):
    if n <= 0:
        return False
    # Formula for nth decagonal number: D_n = (5n^2 - 3n) / 2
    val = (5 * n**2 - 3 * n) // 2
    return val == int(val) and val > 0
```

Module-level executable statement完整內容：

```python
lines 9-9:
assert is_num_decagonal(3) == 27
```

Diagnostic最少必要前後文：

```text
7:
8: # Example usage to verify the assertion from the prompt
9: assert is_num_decagonal(3) == 27
```

Provisional adjudication：

- Primary：`L2`；secondary：`["L4"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G3s","layer":"L2","mechanism":"numeric_output_contract_as_boolean","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_required_function_output"},{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"}]`
- Mechanisms：`["schema_mismatch","semantic_goal_drift","module_level_executable_assertion","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：Although the entry-point name is predicate-like, the task description and public expected value explicitly require a number.
- Proposed Healer eligibility／decision：`abstain`／`not_run`
- Rationale：The function computes the decagonal value but returns only a boolean about it, violating the public numeric return contract. The executable assertion is a later G2 failure-chain stage; correcting the output requires semantic code change.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/279","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=84f71b53c98028b255fd361fab6deec391cb7e68bf49bd27e8a27950260897d1;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=164e4d0b000ecd095f5ef3bfcf49984ab69dc951caabe5be7b141ce585100586","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 24. `c9972dbd1c76e4805401c1f08a4e25bf32b46c73b3be0befe79c623426dce6b2`

- Identity：task `Mbpp/735`；seed `55`；cell `4aeefd4c8d0dd04bf99b77cacba54999f01b80870a920ed6f3997c932ab6960d`
- Required entry point：`toggle_middle_bits(n)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `39`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["n.bit_length","toggle_middle_bits"]`

公開 task contract：

```text
"""
Write a python function to toggle bits of the number except the first and the last bit.
assert toggle_middle_bits(9) == 15
"""
```

Required function完整 source（原行 1–36）：

```python
def toggle_middle_bits(n):
    if n < 3:
        return n

    # Create a mask with all bits set except first (MSB) and last (LSB) of the current bit width
    num_bits = n.bit_length()

    # Mask for middle bits only:
    # We want to keep MSB as is, LSB as is, and toggle everything in between.
    # Create a mask where all bits are 1 except first and last positions relative to actual number

    # Actually simpler approach:
    # Toggle all bits from bit index 0 up to num_bits-2 (excluding the very last bit)
    # But we need to exclude both MSB and LSB of the original number's width.

    # Let's use a different strategy:
    # Create mask with all ones, then remove first and last bit positions from consideration for toggling

    if n == 0 or n == 1:
        return n

    num_bits = n.bit_length()

    # Mask to keep only middle bits (not MSB at position num_bits-1, not LSB at position 0)
    # We want to toggle bits from position 1 to num_bits-2 inclusive

    if num_bits <= 3:
        return n

    mask = ((1 << (num_bits - 2)) - 1) & ~((1 << (num_bits - 2))) | (((1 << (num_bits - 2)) - 1) >> 1) * 0

    # Simpler approach using XOR with a pattern
    # Toggle bits from position 1 to num_bits-2
    toggle_mask = ((1 << (num_bits - 3 + 1)) - 1) if num_bits > 3 else 0

    return n ^ toggle_mask
```

Module-level executable statement完整內容：

```python
lines 39-39:
assert toggle_middle_bits(9) == 15
```

Diagnostic最少必要前後文：

```text
37:
38: # Test the function
39: assert toggle_middle_bits(9) == 15
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example is sufficient to show the mask is wrong; broader bit-width behavior remains for later correctness evaluation.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The constructed XOR mask toggles the wrong bit positions for the public input, and the copied assertion exposes the bit-mask algorithm error during module execution.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/735","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=c9972dbd1c76e4805401c1f08a4e25bf32b46c73b3be0befe79c623426dce6b2;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=4aeefd4c8d0dd04bf99b77cacba54999f01b80870a920ed6f3997c932ab6960d","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 25. `f59c91131c769f305f410b20a5738e70c14be1ba72df0eba0fb4f7efe6af1987`

- Identity：task `Mbpp/581`；seed `22`；cell `9ccb1020e50b2e30f846dd029b1e8026797288f7bc03943f0fb1a03639628fe2`
- Required entry point：`surface_Area(base_edge: float, height: float)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `14`；AST `Assert/Constant`
- Imports：`["math"]`
- API calls：`["math.sqrt","surface_Area"]`

公開 task contract：

```text
"""
Write a python function to find the surface area of a square pyramid with a given base edge and height.
assert surface_Area(3,4) == 33
"""
```

Required function完整 source（原行 1–12）：

```python
def surface_Area(base_edge: float, height: float) -> float:
    """Calculate the total surface area of a square pyramid."""
    import math
    base_area = base_edge ** 2

    # Calculate slant height using Pythagorean theorem
    half_base = base_edge / 2
    slant_height = math.sqrt(height**2 + half_base**2)

    lateral_surface_area = 4 * (0.5 * base_edge * slant_height)

    return base_area + lateral_surface_area
```

Module-level executable statement完整內容：

```python
lines 14-14:
assert surface_Area(3, 4) == 33
```

Diagnostic最少必要前後文：

```text
12:     return base_area + lateral_surface_area
13:
14: assert surface_Area(3, 4) == 33
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"mathematical_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","mathematical_error","model_assembly_failure"]`
- Confidence：`MEDIUM`
- Uncertainty：The public expected integer constrains this cell, but the contract does not separately state a rounding convention.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function returns the unrounded geometric expression, which does not equal the public contract value, so the copied assertion exposes a numerical-contract mismatch. A rounding or formula rewrite is not uniquely justified.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/581","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=f59c91131c769f305f410b20a5738e70c14be1ba72df0eba0fb4f7efe6af1987;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=9ccb1020e50b2e30f846dd029b1e8026797288f7bc03943f0fb1a03639628fe2","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 26. `f85bb6c1efa65465700b139dec03e685dcf850a8f10c477b5c882562b3a06bae`

- Identity：task `Mbpp/125`；seed `44`；cell `077f1bf7c9d65bc6221f849123c643fc21faae3c9178720e322d923c3397a603`
- Required entry point：`find_length(s)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `26`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["find_length","max"]`

公開 task contract：

```text
"""
Write a function to find the maximum difference between the number of 0s and number of 1s in any sub-string of the given binary string.
assert find_length("11000010001") == 6
"""
```

Required function完整 source（原行 1–24）：

```python
def find_length(s):
    max_diff = 0
    current_sum = 0

    # Treat '1' as +1 and '0' as -1 to maximize (count_ones - count_zeros)
    for char in s:
        if char == '1':
            current_sum += 1
        else:
            current_sum -= 1

        max_diff = max(max_diff, current_sum)

    # Now treat '0' as +1 and '1' as -1 to maximize (count_zeros - count_ones)
    current_sum = 0
    for char in s:
        if char == '0':
            current_sum += 1
        else:
            current_sum -= 1

        max_diff = max(max_diff, current_sum)

    return max_diff
```

Module-level executable statement完整內容：

```python
lines 26-26:
assert find_length("11000010001") == 6
```

Diagnostic最少必要前後文：

```text
24:     return max_diff
25:
26: assert find_length("11000010001") == 6
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"algorithmic_error","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","algorithmic_error","edge_case_omission","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The public example alone establishes the observed mismatch; hidden substring cases are not used.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The two passes maximize whole-prefix imbalance without resetting at adverse prefixes, so they do not implement a maximum over arbitrary substrings; the public assertion exposes the error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/125","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=f85bb6c1efa65465700b139dec03e685dcf850a8f10c477b5c882562b3a06bae;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=077f1bf7c9d65bc6221f849123c643fc21faae3c9178720e322d923c3397a603","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。

### 27. `fc6b03344724ba3afc143f9306850b95b0a8abbdb043ee45f33e9635ce88f530`

- Identity：task `Mbpp/432`；seed `11`；cell `672aa73645332354b575037f185dc81ac749b5da269822bbc0abd6e2c700fd13`
- Required entry point：`median_trapezium(a, b, c)`
- Diagnostic：phase `G2_module`；class `AssertionError`；candidate line `4`；AST `Assert/Constant`
- Imports：`[]`
- API calls：`["median_trapezium"]`

公開 task contract：

```text
"""
Write a function to find the median length of a trapezium.
assert median_trapezium(15,25,35)==20
"""
```

Required function完整 source（原行 1–2）：

```python
def median_trapezium(a,b,c):
    return (a+b+c)/3
```

Module-level executable statement完整內容：

```python
lines 4-4:
assert median_trapezium(15,25,35)==20
```

Diagnostic最少必要前後文：

```text
2:     return (a+b+c)/3
3:
4: assert median_trapezium(15,25,35)==20
```

Provisional adjudication：

- Primary：`L4`；secondary：`["L5"]`
- Outcome validity：`VALID_MODEL_OUTCOME`
- Failure chain：`[{"gate":"G2","layer":"L4","mechanism":"module_level_executable_assertion","outcome_validity":"VALID_MODEL_OUTCOME","stage":"raw_module_execution"},{"evidence_scope":"public_contract_only","gate":"G4","layer":"L5","mechanism":"parameter_semantics_swap","outcome_validity":"VALID_MODEL_OUTCOME","stage":"required_function_public_contract_observation"}]`
- Mechanisms：`["module_level_executable_assertion","parameter_semantics_swap","mathematical_error","model_assembly_failure"]`
- Confidence：`HIGH`
- Uncertainty：The parameter roles are terse in prose, but averaging all three visibly contradicts the public example.
- Proposed Healer eligibility／decision：`conditional`／`not_run`
- Rationale：The function averages all three inputs rather than the required trapezium median relation indicated by the public result; the copied assertion exposes the parameter-semantics error.
- Evidence references：`["data/mbpp_plus/tasks.jsonl#task_id=Mbpp/432","artifacts/public_benchmark_development/mbpp_candidate_b_development60/runs/mbpp_q35_9b_candidate_b_development60_replay_r003/h0_h1_accounts.jsonl#program_id=fc6b03344724ba3afc143f9306850b95b0a8abbdb043ee45f33e9635ce88f530;healer_account=H0","artifacts/public_benchmark_governance/candidate_b_r003_diagnostics_r002_v3/manual_formal_diagnostics_run_001/coarse_diagnostics.csv#cell_identity_sha256=672aa73645332354b575037f185dc81ac749b5da269822bbc0abd6e2c700fd13","C:/Users/yehya/Downloads/AI 生成程式共同失敗分類標準（實際使用版 v3）.md#sha256=7df8f4472ce048569967436cbc73ede8fd4bd117ad67d0028ddd95af2055a304"]`

Researcher review：`researcher_review_status`、`researcher_notes`、`researcher_id`、`reviewed_at_utc` 均保持空白，等待 ACCEPT／MODIFY／UNRESOLVED 覆核。
