from __future__ import annotations
import csv,io,json
from collections import Counter
from scripts import reaudit_candidate_b_r003_taxonomy_v31_batch03_20cell_provisional_v2 as reaudit

def _rows(data:bytes)->list[dict[str,str]]:return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
def test_sha_identity_source_and_complete_delta_closure()->None:
    reaudit.verify_sources(); a=reaudit.build_analysis(); assert len(a["findings"])==20
    assert Counter(r["change_status"] for r in a["findings"])==Counter({"UNCHANGED_AFFIRMED":18,"APPROVED_CHANGE_AFFIRMED":2})
    assert a["summary"]["identity_source_closure"]==20 and a["summary"]["unique_source_sha256"]==19
def test_two_independent_approved_change_verifications()->None:
    a=reaudit.build_analysis(); assert len(a["approved"])==len(a["differences"])==2
    assert {r["program_id"] for r in a["approved"]}==reaudit.TARGET_IDS
    assert all(r["verification_status"]=="AFFIRMED" and r["preserved_fields_status"]=="ALL_NON_MECHANISM_FIELDS_EQUAL" for r in a["approved"])
    assert all(reaudit.NEW_TAG in r["v2_mechanisms_json"] and reaudit.OLD_TAG not in r["v2_mechanisms_json"] for r in a["approved"])
def test_derivatives_statistics_and_no_issues()->None:
    s=reaudit.build_analysis()["summary"]; stats=s["rebuilt_statistics"]
    assert s["affirmed"]==20 and s["non_material"]==s["material"]==s["unauthorized_differences"]==0
    assert stats["primary"]=={"L2":1,"L5":12,"UNRESOLVED":7}; assert stats["secondary"]=={"L5":1,"empty":19}
    assert stats["confidence"]=={"HIGH":13,"LOW":7}; assert stats["outcome"]=={"VALID_MODEL_OUTCOME":20}; assert stats["healer"]=={"eligible":0,"conditional":0,"abstain":20}
    assert stats["mechanisms"][reaudit.NEW_TAG]==2 and reaudit.OLD_TAG not in stats["mechanisms"]
def test_zero_execution_and_deterministic_on_disk_rebuild()->None:
    first=reaudit.build_outputs(); assert first==reaudit.build_outputs()
    for name,data in first.items():assert (reaudit.REPO_ROOT/reaudit.OUTPUT_RELATIVE/name).read_bytes()==data
    assert len(_rows(first["per_cell_v2_reaudit_findings.csv"]))==20; assert len(_rows(first["material_findings.csv"]))==len(_rows(first["non_material_findings.csv"]))==0
    assert all(v==0 for v in json.loads(first["execution_counts.json"]).values()); assert json.loads(first["manifest.json"])["verdict"]=="READY_TO_FREEZE_BATCH03_PROVISIONAL_V2"
