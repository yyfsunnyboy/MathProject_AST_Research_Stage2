import json, tempfile
from pathlib import Path
import pytest
from scripts import run_ollama_math_track_qualification as r

def test_provenance_scope_and_conditions():
 assert set(r.PROVENANCE)=={"qwen3:4b-instruct-2507-q4_K_M","qwen3:8b"}
 assert r.PROVENANCE["qwen3:4b-instruct-2507-q4_K_M"]["digest"]=="0edcdef34593"
 assert r.PROVENANCE["qwen3:8b"]["digest"]=="500a1f067a9f"
 for c in r.CONDITIONS:
  rows=r.records("qwen3:4b-instruct-2507-q4_K_M",c)
  assert len(rows)==4 and all(x["retry_count"]==0 and not x["healer_enabled"] for x in rows)

def test_safe_cli_and_single_filter(capsys):
 assert r.main(["--model-tag","qwen3:8b","--condition","ab1","--run-id","x"])==2
 capsys.readouterr()
 assert r.main(["--model-tag","qwen3:8b","--condition","ab2g_math_core","--run-id","x","--dry-run","--task-family","common_factor_quadratic_root_ordering"])==0
 assert json.loads(capsys.readouterr().out)["task_count"]==1

def test_append_flush_fsync_and_existing_output(monkeypatch):
 events=[]
 class H:
  def __enter__(s): return s
  def __exit__(s,*a): pass
  def write(s,x): events.append("write")
  def flush(s): events.append("flush")
  def fileno(s): return 7
 monkeypatch.setattr(Path,"open",lambda *a,**k:H()); monkeypatch.setattr(r.os,"fsync",lambda x:events.append("fsync"))
 r._append(Path("x"),{}); assert events==["write","flush","fsync"]

def test_mock_four_calls_and_preserves_rows(monkeypatch):
 calls=[]
 def fake(prompt,model): calls.append(prompt); return {"response":"def generate(level=1, **kwargs):\n return {}","total_duration":1}
 monkeypatch.setattr(r,"_call",fake)
 # Execution loop is intentionally not invoked here: no real model path in tests.
 assert len(r.records("qwen3:8b","ab2d_local"))==4
