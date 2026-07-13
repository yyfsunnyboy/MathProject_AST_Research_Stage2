"""Deterministic local-RNG sampler for CE115 task contracts."""
import hashlib
import random

def _rng(task_id, seed):
    return random.Random(int.from_bytes(hashlib.sha256(f"{task_id}:{seed}".encode()).digest()[:8], "big"))

def _pick(rng, spec):
    if "allowed_values" in spec: return rng.choice(spec["allowed_values"])
    step=spec.get("step",1); return rng.randrange(spec["min"],spec["max"]+1,step)

def sample_task_parameters(task_spec, seed):
    rng=_rng(task_spec["task_id"],seed); r=task_spec["parameter_ranges"]; skill=task_spec["skill_id"]
    if skill=="polynomial_division_quotient_remainder":
        for _ in range(100):
            a=_pick(rng,r["leading_coefficient"]); root=_pick(rng,r["divisor_root"]); q=rng.randint(-6,6); rem=0 if task_spec["difficulty_level"]==1 else rng.choice([x for x in range(-6,7) if x])
            b=q-root*a; c=rem-root*q
            if r["linear_coefficient"]["min"]<=b<=r["linear_coefficient"]["max"] and r["constant_coefficient"]["min"]<=c<=r["constant_coefficient"]["max"]:
                payload={"dividend_coefficients":[a,b,c],"divisor_root":root}; break
        else: raise ValueError("unable to sample polynomial parameters")
    elif skill=="rpm_circumference_to_kph":
        c=_pick(rng,r["circumference_cm"]); payload={"circumference_cm":c,"rpm_symbol":"rpm","requested_unit":"km/h"}
    elif skill=="alternating_training_progression_threshold":
        for _ in range(100):
            t=_pick(rng,r["track_length_m"]); a=_pick(rng,r["initial_first_day_laps"]); inc=_pick(rng,r["same_week_increment_laps"]); threshold=_pick(rng,r["threshold_km"]); week=_pick(rng,r["specified_week"])
            if next((i for i in range(30) if (a+inc*(i//2+i%2))*t>threshold*1000),None) is not None:
                payload={"track_length_m":t,"initial_first_day_laps":a,"same_week_increment_laps":inc,"threshold_km":threshold,"specified_week":week,"specified_day":"Thursday","day_labels":["Monday","Thursday"]}; break
        else: raise ValueError("unable to sample training parameters")
    else:
        count=_pick(rng,r["claim_count"]); vals=[6,10,12,15,18,21,22,24,26,30,33,35,39,42,44,45,50,55,60,66,70,78,84,90,105,110,120]; vals=[v for v in vals if r["largest_proper_divisor"]["min"]<=v<=r["largest_proper_divisor"]["max"]]
        declared={}; claims=[]
        for i in range(count):
            l=rng.choice(vals); declared[chr(65+i)]=l; candidate=2 if i%2==0 else next(x for x in range(r["candidate_factor"]["min"],r["candidate_factor"]["max"]+1) if l%x)
            claims.append({"subject":chr(65+i),"candidate_factor":candidate,"asks_necessity":True})
        payload={"largest_proper_divisors":declared,"claims":claims}
    return {"task_id":task_spec["task_id"],"difficulty_level":task_spec["difficulty_level"],"seed":seed,"oracle_payload":payload,"sampled_parameters":payload.copy()}
