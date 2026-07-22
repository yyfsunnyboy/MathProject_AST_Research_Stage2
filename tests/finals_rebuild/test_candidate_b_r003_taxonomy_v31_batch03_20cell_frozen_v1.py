from __future__ import annotations
import csv,io,json
from collections import Counter
from scripts import freeze_candidate_b_r003_taxonomy_v31_batch03_20cell_v1 as freeze
def _rows(data:bytes)->list[dict[str,str]]:return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
def test_source_sha_authorization_and_byte_identity()->None:
    freeze.verify_sources();p=freeze.build_payload();assert p["records_bytes"]==(freeze.REPO_ROOT/freeze.V2_RECORDS).read_bytes();assert all(r["status"]=="PASS" for r in p["authorization"]);assert p["summary"]["reaudit_affirmed"]==20 and p["summary"]["reaudit_material"]==0
def test_identity_statistics_mechanisms_and_shared_source()->None:
    p=freeze.build_payload();s=p["summary"];stats=s["statistics"];rows=_rows(p["records_bytes"])
    assert len(rows)==20 and len({r["program_id"] for r in rows})==len({r["cell_identity_sha256"] for r in rows})==20 and len({r["source_sha256"] for r in rows})==19
    assert stats["primary"]=={"L2":1,"L5":12,"UNRESOLVED":7};assert stats["secondary"]=={"L5":1,"empty":19};assert stats["confidence"]=={"HIGH":13,"LOW":7};assert stats["outcome"]=={"VALID_MODEL_OUTCOME":20};assert stats["healer"]=={"eligible":0,"conditional":0,"abstain":20};assert stats["mechanisms"]["frequency_one_instead_of_distinct_value"]==2 and "dedupe_instead_of_unique_occurrence" not in stats["mechanisms"] and stats["mechanisms"]["semantic_goal_drift"]==4;assert s["rank4_rank14_legal_shared_source"] is True
def test_all_frozen_source_ledgers_are_byte_copies()->None:
    outputs=freeze.build_outputs();pairs={"frozen_adjudication_records.csv":freeze.V2_RECORDS,"frozen_per_cell_evidence_ledger.csv":freeze.V2_EVIDENCE,"frozen_mechanism_ledger.csv":freeze.V2_MECHANISMS,"frozen_unresolved_evidence_gaps.csv":freeze.V2_GAPS,"frozen_conditional_queue.csv":freeze.V2_CONDITIONAL}
    for name,source in pairs.items():assert outputs[name]==(freeze.REPO_ROOT/source).read_bytes()
def test_zero_execution_deterministic_on_disk_and_manifest()->None:
    first=freeze.build_outputs();assert first==freeze.build_outputs()
    for name,data in first.items():assert (freeze.REPO_ROOT/freeze.OUTPUT_RELATIVE/name).read_bytes()==data
    assert all(v==0 for v in json.loads(first["execution_counts.json"]).values());m=json.loads(first["manifest.json"]);assert m["verdict"]=="BATCH03_PROVISIONAL_V2_FROZEN_READY_TO_COMMIT" and m["frozen_records_byte_identical_to_v2"] is True and m["frozen_records_sha256"]==freeze.SOURCE_HASHES[freeze.V2_RECORDS]
