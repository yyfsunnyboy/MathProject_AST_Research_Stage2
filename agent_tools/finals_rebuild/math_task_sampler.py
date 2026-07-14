"""Deterministic local-RNG sampler for CE115 task contracts."""
import hashlib
import random
from fractions import Fraction

def _rng(task_id, seed):
    return random.Random(int.from_bytes(hashlib.sha256(f"{task_id}:{seed}".encode()).digest()[:8], "big"))

def _pick(rng, spec):
    if "allowed_values" in spec: return rng.choice(spec["allowed_values"])
    step=spec.get("step",1); return rng.randrange(spec["min"],spec["max"]+1,step)

def _decimal_text(units, scale):
    """Exact decimal string for units/scale where scale is 10 or 100."""
    sign="-" if units<0 else ""; units=abs(units); digits=2 if scale==100 else 1
    return f"{sign}{units//scale}.{units%scale:0{digits}d}"

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
    elif skill=="radical_simplification":
        for _ in range(100):
            k=_pick(rng,r["square_coefficient"]); m=_pick(rng,r["square_free_part"])
            if k<2 or m<2: continue
            payload={"radicand":k*k*m}
            if "outer_coefficient" in r:
                payload["outer_coefficient"]=_pick(rng,r["outer_coefficient"])
            break
        else: raise ValueError("unable to sample radical parameters")
    elif skill=="exact_rational_expression":
        for _ in range(200):
            right=_decimal_text(_pick(rng,r["right_tenths"]),10)
            products=[]
            if "pair_sum" in r:
                total_units=_pick(rng,r["pair_sum"])*100; p2=_pick(rng,r["left_hundredths"])
                p1=total_units-p2
                if p1<=0 or p1==p2: continue
                products=[{"sign":1,"left":_decimal_text(p1,100),"right":right},
                          {"sign":-1,"left":_decimal_text(-p2,100),"right":right}]
            else:
                count=_pick(rng,r["product_count"])
                share="share_right_factor" in r
                for _i in range(count):
                    left=_decimal_text(_pick(rng,r["left_hundredths"])*rng.choice([-1,1]),100)
                    factor=right if share else _decimal_text(_pick(rng,r["right_tenths"]),10)
                    products.append({"sign":rng.choice([-1,1]),"left":left,"right":factor})
            total=sum(p["sign"]*Fraction(p["left"])*Fraction(p["right"]) for p in products)
            if total!=0:
                payload={"products":products}; break
        else: raise ValueError("unable to sample rational expression parameters")
    elif skill=="polynomial_division_general":
        deg=_pick(rng,r["dividend_degree"])
        for _ in range(200):
            a=_pick(rng,r["divisor_leading"]); b=_pick(rng,r["divisor_constant"])
            if a==0: continue
            coeffs=[_pick(rng,r["coefficient"]) for _ in range(deg+1)]
            if coeffs[0]==0: continue
            if "missing_term_count" in r and deg>=2:
                for idx in rng.sample(range(1,deg),k=min(_pick(rng,r["missing_term_count"]),deg-1)):
                    coeffs[idx]=0
            payload={"dividend_coefficients":coeffs,"divisor_coefficients":[a,b]}; break
        else: raise ValueError("unable to sample polynomial division parameters")
    elif skill=="polynomial_factor_roots":
        for _ in range(300):
            p1=_pick(rng,r["root1_den"]); q1=_pick(rng,r["root1_num"])
            p2=_pick(rng,r["root2_den"]); q2=_pick(rng,r["root2_num"])
            if p1<=0 or p2<=0: continue
            if Fraction(q1,p1)==Fraction(q2,p2): continue
            scale=_pick(rng,r["overall_factor"])
            if scale==0: continue
            payload={"quadratic_coefficients":[scale*p1*p2,scale*(-(p1*q2+p2*q1)),scale*q1*q2]}; break
        else: raise ValueError("unable to sample factor-roots parameters")
    else:
        count=_pick(rng,r["claim_count"]); vals=[6,10,12,15,18,21,22,24,26,30,33,35,39,42,44,45,50,55,60,66,70,78,84,90,105,110,120]; vals=[v for v in vals if r["largest_proper_divisor"]["min"]<=v<=r["largest_proper_divisor"]["max"]]
        declared={}; claims=[]
        for i in range(count):
            l=rng.choice(vals); declared[chr(65+i)]=l; candidate=2 if i%2==0 else next(x for x in range(r["candidate_factor"]["min"],r["candidate_factor"]["max"]+1) if l%x)
            claims.append({"subject":chr(65+i),"candidate_factor":candidate,"asks_necessity":True})
        payload={"largest_proper_divisors":declared,"claims":claims}
    return {"task_id":task_spec["task_id"],"difficulty_level":task_spec["difficulty_level"],"seed":seed,"oracle_payload":payload,"sampled_parameters":payload.copy()}
