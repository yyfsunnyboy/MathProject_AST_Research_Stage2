#!/usr/bin/env python3
"""Formal immutable freeze of Batch03 provisional adjudication v2.

The v2 records and ledgers are copied byte-for-byte.  This builder performs no
reclassification, review, candidate execution, or model work.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT=Path(__file__).resolve().parents[1]
OUTPUT_RELATIVE=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_frozen_v1")
START_HEAD="923e828b5f0455fd10f5646541f4c9a68a47837b"
STATUS="FORMALLY_FROZEN_AI_ASSISTED_PROVISIONAL_ADJUDICATION"
VERDICT="BATCH03_PROVISIONAL_V2_FROZEN_READY_TO_COMMIT"
FREEZE_BASIS="READY_TO_FREEZE_BATCH03_PROVISIONAL_V2"

ROSTER=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1/batch03_roster.csv")
ROSTER_MANIFEST=ROSTER.with_name("manifest.json")
ROSTER_AUDIT=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_remaining61_batch03_20cell_roster_v1_independent_audit_v1/manifest.json")
V1_DIR=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1")
V1_RECORDS=V1_DIR/"adjudication_records.csv"; V1_MANIFEST=V1_DIR/"manifest.json"
AUDIT_DIR=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v1_independent_audit_v1")
AUDIT_FINDINGS=AUDIT_DIR/"per_cell_audit_findings.csv"; AUDIT_MATERIAL=AUDIT_DIR/"material_findings.csv"; AUDIT_MANIFEST=AUDIT_DIR/"manifest.json"
V2_DIR=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v2")
V2_RECORDS=V2_DIR/"adjudication_records.csv"; V2_MANIFEST=V2_DIR/"manifest.json"; V2_LEDGER=V2_DIR/"approved_difference_ledger.csv"
V2_EVIDENCE=V2_DIR/"per_cell_evidence_ledger.csv"; V2_MECHANISMS=V2_DIR/"mechanism_ledger.csv"; V2_GAPS=V2_DIR/"unresolved_evidence_gaps.csv"; V2_CONDITIONAL=V2_DIR/"conditional_diagnostic_queue.csv"; V2_SUMMARY=V2_DIR/"adjudication_summary.json"
REAUDIT_DIR=Path("artifacts/public_benchmark_governance/candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v2_independent_reaudit_v1")
REAUDIT_FINDINGS=REAUDIT_DIR/"per_cell_v2_reaudit_findings.csv"; REAUDIT_APPROVED=REAUDIT_DIR/"approved_change_verification.csv"; REAUDIT_SUMMARY=REAUDIT_DIR/"reaudit_summary.json"; REAUDIT_MANIFEST=REAUDIT_DIR/"manifest.json"
TAXONOMY=Path("C:/Users/yehya/Downloads/AI_生成程式共同失敗分類標準_實際使用版_v3.1.md")

SOURCE_HASHES={
    ROSTER:"6f772918bb5c16eb1c9ad88e086e936b4e1d12e7e378924cc13a22a812ac1f74",ROSTER_MANIFEST:"42552f07b842b7317e94f162bf6345d2d35761bcd6c4972451344cba3393001c",ROSTER_AUDIT:"ba20a3ab6e3200f2c9c2effbabd27537f6f4b1415637fec5846c80ec90425a4a",
    V1_RECORDS:"dbc19dc8b0a1004013b51c94fe66d24b1def455911b9ac69ea56f611d9e6a0fd",V1_MANIFEST:"8467b8713144182abcb8d21fb40454c80daec89459fb42077d16c549231e2282",AUDIT_FINDINGS:"6660f56ae629775ced6d7ab57b6b5b8d5931413ac00fb0dd7baad469ad5bf133",AUDIT_MATERIAL:"0fe1c7517bdc327fff62fc97fa159d97af3873f2c00a43ea750f40abae5a0a45",AUDIT_MANIFEST:"d0bdab2fa65865958336c063c432b05022acae5905fa1c63c29a971118a8f070",
    V2_RECORDS:"d0f59af50c2e433c7d02546da04a3d3802641077b75c649144f953f3c2b4d80f",V2_MANIFEST:"88c460e1357e637ab10734dedbc416aec579342ad036644258a3b821b37310d2",V2_LEDGER:"9504c93b0f8ed8dd75b044b6526aae832649159fe85f54da0f0c151b53d0aea7",V2_EVIDENCE:"0d1c8f5143eedba9a863ea6b58c247ebfc6397848f3fb04f318970b072472b53",V2_MECHANISMS:"f46b5244416d5bb2aced794181238b7c7ba87ef0f6b6bd28b2f63a630f0eb3ca",V2_GAPS:"f728a5088f3c169969196caceb85258b1045cc48bde0d762ef6b6885715d7c60",V2_CONDITIONAL:"fb82e22dad104d428fbb8e8c66024e742ccdc7c326fffa0e9b6969b6133c1808",V2_SUMMARY:"565c4937f6dbb926b5e3c39ca7145022d8ded5624eab99b32e50ef37ec89e88d",
    REAUDIT_FINDINGS:"cd2872712d19ded8dd0b6b7510b669bebd06f1e491677aba594f5bd418458d4a",REAUDIT_APPROVED:"b2b1036b80617f1fc63b708b97759bdac214e21ae31c37759b455cba869705d1",REAUDIT_SUMMARY:"307b54d62be0a91e7bb114c1d30b61a7a7f6c1e713556edca8252f8a6878ffb0",REAUDIT_MANIFEST:"aa6465e22b40e043f4eee7e097620e8d9eb7ac9aa40a71fb13ff122974495073",TAXONOMY:"93908ec8e4721f0039acc779fb948988b6c25e712c29890bd98aa7c21a8422a0",
}

AUTH_FIELDS=("check_id","expected","observed","status","evidence")

class FreezeError(RuntimeError):pass
def _require(c:bool,m:str)->None:
    if not c:raise FreezeError(m)
def _sha(d:bytes)->str:return hashlib.sha256(d).hexdigest()
def _read_csv(repo:Path,path:Path)->list[dict[str,str]]:
    actual=path if path.is_absolute() else repo/path
    with actual.open(encoding="utf-8",newline="") as h:return list(csv.DictReader(h))
def _csv_bytes(fields:tuple[str,...],rows:list[dict[str,Any]])->bytes:
    s=io.StringIO(newline="");w=csv.DictWriter(s,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows({f:r.get(f,"") for f in fields} for r in rows);return s.getvalue().encode("utf-8")
def _json_bytes(v:Any)->bytes:return (json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
def verify_sources(repo:Path=REPO_ROOT)->None:
    for p,d in SOURCE_HASHES.items():
        actual=p if p.is_absolute() else repo/p
        _require(actual.is_file(),f"missing upstream: {p.as_posix()}");_require(_sha(actual.read_bytes())==d,f"upstream byte drift: {p.as_posix()}")

def build_payload(repo:Path=REPO_ROOT)->dict[str,Any]:
    verify_sources(repo)
    v2_manifest=json.loads((repo/V2_MANIFEST).read_text(encoding="utf-8")); re_manifest=json.loads((repo/REAUDIT_MANIFEST).read_text(encoding="utf-8")); re_summary=json.loads((repo/REAUDIT_SUMMARY).read_text(encoding="utf-8"))
    _require(v2_manifest["verdict"]=="READY_FOR_BATCH03_PROVISIONAL_V2_REAUDIT","v2 verdict drift");_require(re_manifest["verdict"]==FREEZE_BASIS,"reaudit verdict drift")
    _require(re_summary["affirmed"]==20 and re_summary["material"]==0 and re_summary["non_material"]==0,"freeze authorization drift")
    records_bytes=(repo/V2_RECORDS).read_bytes();evidence_bytes=(repo/V2_EVIDENCE).read_bytes();mechanism_bytes=(repo/V2_MECHANISMS).read_bytes();gaps_bytes=(repo/V2_GAPS).read_bytes();conditional_bytes=(repo/V2_CONDITIONAL).read_bytes()
    records=_read_csv(repo,V2_RECORDS);roster=_read_csv(repo,ROSTER);mechanisms=_read_csv(repo,V2_MECHANISMS);gaps=_read_csv(repo,V2_GAPS);conditional=_read_csv(repo,V2_CONDITIONAL)
    _require(len(records)==len(roster)==20,"20-cell count drift");_require([r["program_id"] for r in records]==[r["program_id"] for r in roster],"program order drift");_require([r["cell_identity_sha256"] for r in records]==[r["cell_identity_sha256"] for r in roster],"cell identity drift");_require([r["source_sha256"] for r in records]==[r["source_sha256"] for r in roster],"source drift")
    primary=Counter(r["primary_layer"] for r in records);secondary=Counter(r["secondary_layer"] or "empty" for r in records);confidence=Counter(r["confidence"] for r in records);outcome=Counter(r["outcome_validity"] for r in records);healer=Counter(r["healer_eligibility"] for r in records);mechanism_counts=Counter(r["mechanism_tag"] for r in mechanisms)
    _require(primary==Counter({"L5":12,"UNRESOLVED":7,"L2":1}) and secondary==Counter({"empty":19,"L5":1}),"layer statistics drift");_require(confidence==Counter({"HIGH":13,"LOW":7}) and outcome==Counter({"VALID_MODEL_OUTCOME":20}) and healer==Counter({"abstain":20}),"disposition statistics drift")
    _require(mechanism_counts["frequency_one_instead_of_distinct_value"]==2 and mechanism_counts["dedupe_instead_of_unique_occurrence"]==0 and mechanism_counts["semantic_goal_drift"]==4,"mechanism statistics drift")
    _require(len(gaps)==7 and len(conditional)==0,"gap/conditional drift");_require(len({r["program_id"] for r in records})==len({r["cell_identity_sha256"] for r in records})==20 and len({r["source_sha256"] for r in records})==19,"identity uniqueness drift")
    shared=[r for r in records if r["batch_rank"] in {"4","14"}];_require(len({r["source_sha256"] for r in shared})==1 and len({r["cell_identity_sha256"] for r in shared})==2,"legal shared source drift")
    stats={"primary":dict(sorted(primary.items())),"secondary":dict(sorted(secondary.items())),"confidence":dict(sorted(confidence.items())),"outcome":dict(sorted(outcome.items())),"healer":{"eligible":0,"conditional":0,"abstain":20},"mechanisms":dict(sorted(mechanism_counts.items()))}
    authorization=[
        {"check_id":"reaudit_verdict","expected":FREEZE_BASIS,"observed":re_manifest["verdict"],"status":"PASS","evidence":REAUDIT_MANIFEST.as_posix()},
        {"check_id":"reaudit_affirmed","expected":"20","observed":str(re_summary["affirmed"]),"status":"PASS","evidence":REAUDIT_SUMMARY.as_posix()},
        {"check_id":"reaudit_material","expected":"0","observed":str(re_summary["material"]),"status":"PASS","evidence":REAUDIT_SUMMARY.as_posix()},
        {"check_id":"records_byte_identity","expected":SOURCE_HASHES[V2_RECORDS],"observed":_sha(records_bytes),"status":"PASS","evidence":V2_RECORDS.as_posix()},
        {"check_id":"identity_source_closure","expected":"20/20; unique source=19","observed":"20/20; unique source=19","status":"PASS","evidence":ROSTER.as_posix()},
        {"check_id":"derived_statistics_closure","expected":"records-derived","observed":"records-derived","status":"PASS","evidence":V2_SUMMARY.as_posix()},
    ]
    summary={"revision":OUTPUT_RELATIVE.name,"status":STATUS,"verdict":VERDICT,"cells":20,"freeze_basis":FREEZE_BASIS,"freeze_authorized":True,"reaudit_affirmed":20,"reaudit_material":0,"previously_frozen":137,"newly_frozen":20,"total_frozen":157,"remaining":41,"unique_program_id":20,"unique_cell_identity":20,"unique_source_sha256":19,"rank4_rank14_legal_shared_source":True,"statistics":stats,"frozen_records_byte_identical_to_v2":True,"eligible_zero_is_formal_safety_result":True,"verified_healer_rescues_claimed":0,"upstream_modified":False}
    return {"records_bytes":records_bytes,"evidence_bytes":evidence_bytes,"mechanism_bytes":mechanism_bytes,"gaps_bytes":gaps_bytes,"conditional_bytes":conditional_bytes,"authorization":authorization,"summary":summary}

def _report(s:dict[str,Any])->str:
    return "\n".join(["# Frozen Batch03：Candidate B r003 taxonomy v3.1","",f"**狀態：`{STATUS}`**","","Batch03共有20格，frozen records與provisional v2逐byte一致。","","- 1格primary L2且secondary L5，因此Healer abstain","- 12格primary L5","- 7格因現有靜態證據不足而UNRESOLVED","- eligible=0不是搜尋失敗，而是安全標準下的正式結果","- 本批不得用來宣稱Healer有成功修復案例","- 本批可支持「錯誤層級不等於可安全修復性」","",f"- Primary：{s['statistics']['primary']}",f"- Secondary：{s['statistics']['secondary']}",f"- Confidence：{s['statistics']['confidence']}",f"- Outcome：{s['statistics']['outcome']}",f"- Healer：{s['statistics']['healer']}","","本freeze未重新分類、重新審查或執行candidate、tests、diagnostics、Healer或模型；未開始Batch04。",""])

def build_outputs(repo:Path=REPO_ROOT)->dict[str,bytes]:
    p=build_payload(repo);execution={"model_calls":0,"candidate_executions":0,"candidate_imports":0,"public_test_executions":0,"hidden_test_executions":0,"evalplus_correctness_executions":0,"diagnostics_executions":0,"validation_executions":0,"healer_executions":0,"programs_executed":0}
    outputs={"frozen_adjudication_records.csv":p["records_bytes"],"frozen_per_cell_evidence_ledger.csv":p["evidence_bytes"],"frozen_mechanism_ledger.csv":p["mechanism_bytes"],"frozen_unresolved_evidence_gaps.csv":p["gaps_bytes"],"frozen_conditional_queue.csv":p["conditional_bytes"],"frozen_summary.json":_json_bytes(p["summary"]),"freeze_authorization_closure_ledger.csv":_csv_bytes(AUTH_FIELDS,p["authorization"]),"report_zh.md":_report(p["summary"]).encode("utf-8"),"execution_counts.json":_json_bytes(execution)}
    provenance={**p["summary"],**execution,"start_head":START_HEAD,"provenance_chain":[{"stage":"roster","sha256":SOURCE_HASHES[ROSTER]},{"stage":"roster_audit","sha256":SOURCE_HASHES[ROSTER_AUDIT]},{"stage":"provisional_v1","sha256":SOURCE_HASHES[V1_RECORDS]},{"stage":"v1_independent_audit","sha256":SOURCE_HASHES[AUDIT_MANIFEST]},{"stage":"provisional_v2","sha256":SOURCE_HASHES[V2_RECORDS]},{"stage":"v2_independent_reaudit","sha256":SOURCE_HASHES[REAUDIT_MANIFEST]},{"stage":"frozen_batch03"}],"source_hashes":{path.as_posix():digest for path,digest in SOURCE_HASHES.items()},"no_new_adjudication":True,"batch04_started":False}
    outputs["provenance.json"]=_json_bytes(provenance);sha_ledger={"taxonomy_sha256":SOURCE_HASHES[TAXONOMY],"roster_sha256":SOURCE_HASHES[ROSTER],"provisional_v2_records_sha256":SOURCE_HASHES[V2_RECORDS],"provisional_v2_manifest_sha256":SOURCE_HASHES[V2_MANIFEST],"reaudit_findings_sha256":SOURCE_HASHES[REAUDIT_FINDINGS],"reaudit_approved_change_sha256":SOURCE_HASHES[REAUDIT_APPROVED],"reaudit_manifest_sha256":SOURCE_HASHES[REAUDIT_MANIFEST],"frozen_records_sha256":_sha(p["records_bytes"])};outputs["sha_ledger.json"]=_json_bytes(sha_ledger)
    manifest={"revision":OUTPUT_RELATIVE.as_posix(),"status":STATUS,"verdict":VERDICT,"start_head":START_HEAD,"cells":20,"freeze_basis_verdict":FREEZE_BASIS,"freeze_authorized":True,"reaudit_affirmed":20,"reaudit_material":0,"frozen_records_byte_identical_to_v2":True,"frozen_records_sha256":_sha(p["records_bytes"]),"provisional_v2_records_sha256":SOURCE_HASHES[V2_RECORDS],"provisional_v2_manifest_sha256":SOURCE_HASHES[V2_MANIFEST],"reaudit_manifest_sha256":SOURCE_HASHES[REAUDIT_MANIFEST],"previously_frozen":137,"newly_frozen":20,"total_frozen":157,"remaining":41,"outputs_sha256_excluding_manifest":{n:_sha(d) for n,d in outputs.items()},**execution};outputs["manifest.json"]=_json_bytes(manifest);return outputs
def write_outputs(repo:Path=REPO_ROOT)->Path:
    out=repo/OUTPUT_RELATIVE;out.mkdir(parents=True,exist_ok=True)
    for n,d in build_outputs(repo).items():(out/n).write_bytes(d)
    return out
def main()->None:
    out=write_outputs();m=json.loads((out/"manifest.json").read_text(encoding="utf-8"));print(f"wrote {out}");print(f"frozen_records_sha256={m['frozen_records_sha256']}");print(f"manifest_sha256={_sha((out/'manifest.json').read_bytes())}");print(f"verdict={m['verdict']}")
if __name__=="__main__":main()
