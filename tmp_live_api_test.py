"""
Live end-to-end MCRI test.
Calls /api/generate_live for Numbers (Ab3 mode), reports Ab2 vs Ab3 MCRI.
"""
import requests, json, sys, time

BASE = "http://127.0.0.1:5000"
SKILL_ID = "jh_數學1上_FourArithmeticOperationsOfNumbers"

# 原始截圖題目 (帶分數四則運算)
OCR_TEXTS = [
    "-2¾ + 1²⁄₇",          # 負帶分數 + 正帶分數 (截圖例題)
    "(-3½) × 2⅔",           # 帶分數乘法
    "1⅖ ÷ (-2⅓) + ½",       # 混合運算
]

def call_generate(ocr_text, ablation_mode=False, timeout=90):
    payload = {
        "prompt": ocr_text,
        "skill_id": SKILL_ID,
        "ablation_mode": ablation_mode,
        "model_id": "gemini-2.0-flash",
    }
    t0 = time.time()
    resp = requests.post(f"{BASE}/api/generate_live", json=payload, timeout=timeout)
    elapsed = round(time.time() - t0, 2)
    return resp.json(), elapsed

def fmt_mcri(m):
    if not m:
        return "  (no mcri)"
    return (f"  syntax={m.get('syntax_score')}  logic={m.get('logic_score')}  "
            f"render={m.get('render_score')}  stability={m.get('stability_score')}  "
            f"TOTAL={m.get('total_score')}")

print("=" * 65)
print("Live MCRI Verification — Numbers (帶分數 FourArithmeticOperationsOfNumbers)")
print("=" * 65)

results = []
for i, ocr in enumerate(OCR_TEXTS, 1):
    print(f"\n[題目 {i}] {ocr}")
    print("  Calling Ab3 (scaffold + healer)...")
    try:
        data, elapsed = call_generate(ocr, ablation_mode=False)
    except Exception as e:
        print(f"  ERROR: {e}")
        continue

    if not data.get("success"):
        print(f"  FAILED: {data.get('error','unknown')}")
        continue

    ab3_mcri = data.get("mcri", {})
    ab2_result = data.get("ab2_result", {})
    ab2_mcri = ab2_result.get("mcri", {}) if ab2_result else {}

    ab3_total = ab3_mcri.get("total_score", 0)
    ab2_total = ab2_mcri.get("total_score", 0)
    diff = round(ab3_total - ab2_total, 2)
    ok = "✅" if diff >= 0 else "❌"

    ab3_cpu = data.get("cpu_execution_time_sec", "?")
    ab2_cpu = ab2_result.get("cpu_execution_time_sec", "?") if ab2_result else "?"
    fixes = data.get("debug_meta", {}).get("healer_fix_count", 0)

    print(f"  Ab2 MCRI:{fmt_mcri(ab2_mcri)}")
    print(f"  Ab3 MCRI:{fmt_mcri(ab3_mcri)}")
    print(f"  Ab3-Ab2 = {diff:+.2f}  {ok}   fixes={fixes}  Ab2_cpu={ab2_cpu}s  Ab3_cpu={ab3_cpu}s  wall={elapsed}s")

    # Show sympy_ok details
    bd3 = ab3_mcri.get("breakdown", {})
    bd2 = ab2_mcri.get("breakdown", {})
    if bd3 or bd2:
        print(f"  Ab2[sympy_ok={bd2.get('l3_sympy_ok')} l1={bd2.get('l1_syntax')}] "
              f"Ab3[sympy_ok={bd3.get('l3_sympy_ok')} l1={bd3.get('l1_syntax')} "
              f"robust={bd3.get('l5_robust_status', '?')}]")

    # Show generated question text
    q_ab3 = data.get("results", [{}])[0].get("question_text", "") if data.get("results") else ""
    q_ab2 = ab2_result.get("problem", "") if ab2_result else ""
    if q_ab3:
        print(f"  Ab3 question: {q_ab3[:80]}")
    if q_ab2:
        print(f"  Ab2 question: {q_ab2[:80]}")

    results.append({"ocr": ocr, "ab2": ab2_total, "ab3": ab3_total, "diff": diff})

print("\n" + "=" * 65)
print("Summary")
print("=" * 65)
if results:
    all_ok = all(r["diff"] >= 0 for r in results)
    for r in results:
        ok = "✅" if r["diff"] >= 0 else "❌"
        print(f"  {ok}  Ab2={r['ab2']}  Ab3={r['ab3']}  diff={r['diff']:+.2f}  [{r['ocr']}]")
    avg_diff = round(sum(r["diff"] for r in results) / len(results), 2)
    print(f"\n  平均 Ab3-Ab2 = {avg_diff:+.2f}  {'✅ INVARIANT HOLDS' if all_ok else '❌ INVARIANT VIOLATED'}")
