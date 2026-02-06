import sys
import os
import json
import time
import re
from tqdm import tqdm
from sqlalchemy import distinct

# ==========================================
# 🚨 確認執行檔案
# ==========================================
print("🔥 RUNNING V13.0 DASHBOARD VERSION:", __file__)

# ==========================================
# 1. 設定路徑
# ==========================================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, SkillInfo, SkillCurriculum, TextbookExample
from core.ai_analyzer import get_model

# ==========================================
# 課程座標 (支援中文解析)
# ==========================================
class CurriculumPosition:
    def __init__(self, grade, volume, chapter, order):
        self.grade_val = self._parse_grade(grade)
        self.volume_val = self._parse_volume(volume)
        self.chapter_val = self._parse_int(chapter)
        self.order = order if order is not None else 9999
        self.raw = f"{volume} | {chapter}"

    def _parse_int(self, v):
        if not v: return 0
        m = re.search(r'\d+', str(v))
        return int(m.group()) if m else 0

    def _parse_grade(self, s):
        s = str(s).strip()
        if not s: return 0
        if '高一' in s or '10' in s: return 10
        if '高二' in s or '11' in s: return 11
        if '高三' in s or '12' in s or '甲' in s or '乙' in s: return 12
        if '7' in s: return 7
        if '8' in s: return 8
        if '9' in s: return 9
        return self._parse_int(s)

    def _parse_volume(self, s):
        v = self._parse_int(s)
        # 權重：下冊 > 上冊，乙 > 甲
        if '下' in str(s): v += 0.5
        if '乙' in str(s): v += 0.2
        if '甲' in str(s): v += 0.1
        return v

    def __lt__(self, other):
        if self.grade_val != other.grade_val: return self.grade_val < other.grade_val
        if self.volume_val != other.volume_val: return self.volume_val < other.volume_val
        if self.chapter_val != other.chapter_val: return self.chapter_val < other.chapter_val
        return self.order < other.order

# ==========================================
# 建立課程座標快取
# ==========================================
def build_curriculum_map():
    curr_map = {}
    rows = db.session.query(SkillCurriculum).all()
    for r in rows:
        curr_map[r.skill_id] = {
            "pos": CurriculumPosition(r.grade, r.volume, r.chapter, r.display_order),
            "name": r.skill_id 
        }
    return curr_map

# ==========================================
# 選單介面
# ==========================================
def get_user_selection(options, title):
    valid_opts = sorted([str(o) for o in options if o is not None])
    print(f"\n{title}")
    print("   [0] ALL (全部處理)")
    for i, o in enumerate(valid_opts, 1):
        print(f"   [{i}] {o}")
    
    while True:
        c = input("👉 ").strip()
        if c == '0': return None
        try:
            val = valid_opts[int(c) - 1]
            return val
        except:
            print("⚠️ 輸入錯誤，請輸入數字")

# ==========================================
# 候選池 (分三區：同章、同冊、跨冊)
# ==========================================
def get_candidate_skills(target_skill, cache):
    t_obj = next((x for x in cache if x['id'] == target_skill.skill_id), None)
    if not t_obj: 
        t_pos = CurriculumPosition("12", "99", "99", 9999) 
    else:
        t_pos = t_obj['pos']

    zone_1 = [] # 同章 (最優先)
    zone_2 = [] # 同冊 (次優先)
    zone_3 = [] # 跨冊 (基礎)

    for s in cache:
        if s['id'] == target_skill.skill_id: continue
        s_pos = s['pos']
        
        # 1. 未來過濾
        if s_pos.grade_val > t_pos.grade_val: continue
        if s_pos.grade_val == t_pos.grade_val:
            # 同年級，比較冊與章節順序
            if s_pos.volume_val > t_pos.volume_val: continue
            if s_pos.volume_val == t_pos.volume_val:
                if s_pos.chapter_val > t_pos.chapter_val: continue
                # 同章節，比較 display_order
                if s_pos.chapter_val == t_pos.chapter_val and s_pos.order >= t_pos.order: continue

        # 2. 分區邏輯
        item = s # 儲存完整物件方便後續處理

        if s_pos.grade_val == t_pos.grade_val:
            if s_pos.volume_val == t_pos.volume_val:
                if s_pos.chapter_val == t_pos.chapter_val:
                    zone_1.append(item) # Zone 1: 同章
                else:
                    zone_2.append(item) # Zone 2: 同冊不同章
            else:
                zone_3.append(item) # 同年級不同冊 (視為 Zone 3)
        else:
            zone_3.append(item) # 以前年級 (Zone 3)

    # 3. 排序：全部由近到遠 (Reverse)
    zone_1.sort(key=lambda x: x['pos'], reverse=True)
    zone_2.sort(key=lambda x: x['pos'], reverse=True)
    zone_3.sort(key=lambda x: x['pos'], reverse=True)

    return zone_1, zone_2, zone_3

# ==========================================
# AI 分析
# ==========================================
def identify_prerequisites(model, skill, zones, example=None):
    z1, z2, z3 = zones
    
    # 格式化給 AI 看 (加入 ID)
    def fmt(lst, limit): 
        return chr(10).join([f"[[{x['id']}]] {x['name']} ({x['pos'].raw})" for x in lst[:limit]])

    context_a = fmt(z1, 30) # 同章給 30 個
    context_b = fmt(z2, 40) # 同冊給 40 個
    context_c = fmt(z3, 30) # 以前給 30 個

    prompt = f"""
    You are a Math Logic Engine.
    Task: Pick **3 to 5** prerequisite IDs for the Target.
    
    TARGET:
    {skill.skill_ch_name} (ID: {skill.skill_id})
    Context: {example[:150] if example else "N/A"}

    CANDIDATES:
    [ZONE 1: Direct Parents (Same Chapter)]
    {context_a if context_a else "(None)"}

    [ZONE 2: Related Tools (Same Book)]
    {context_b if context_b else "(None)"}

    [ZONE 3: Foundation (Previous Grades)]
    {context_c if context_c else "(None)"}

    INSTRUCTIONS:
    1. Prioritize Zone 1 for direct flow.
    2. Use Zone 2/3 for inverse operations (e.g. Integral->Derivative) or basic tools.
    3. OUTPUT: JSON list of IDs. Example: ["id1", "id2"]
    """
    try:
        r = model.generate_content(prompt).text.strip()
        match = re.search(r'\[(.*?)\]', r, re.DOTALL)
        if match:
            return json.loads(f"[{match.group(1)}]")
        return []
    except:
        return []

# ==========================================
# 主程式
# ==========================================
def main():
    app = create_app()
    with app.app_context():
        print("🚀 Auto Build Prerequisites (Log Enhanced)")

        base = db.session.query(SkillCurriculum)
        
        # --- 選單 ---
        curr = get_user_selection([r[0] for r in db.session.query(distinct(SkillCurriculum.curriculum))], "選擇課綱")
        if curr: base = base.filter(SkillCurriculum.curriculum == curr)

        grade = get_user_selection([r[0] for r in base.with_entities(distinct(SkillCurriculum.grade))], "選擇年級")
        if grade: base = base.filter(SkillCurriculum.grade == grade)

        volume = get_user_selection([r[0] for r in base.with_entities(distinct(SkillCurriculum.volume))], "選擇冊別")
        if volume: base = base.filter(SkillCurriculum.volume == volume)

        chapter = get_user_selection([r[0] for r in base.with_entities(distinct(SkillCurriculum.chapter))], "選擇章節")
        if chapter: base = base.filter(SkillCurriculum.chapter == chapter)
        # ------------
        
        target_ids = [r[0] for r in base.with_entities(SkillCurriculum.skill_id).distinct()]
        target_skills = SkillInfo.query.filter(SkillInfo.skill_id.in_(target_ids)).order_by(SkillInfo.order_index).all()

        print(f"📋 目標: {len(target_skills)} 個技能")
        if not target_skills: return

        mode = input("模式 [1] Safe (跳過已有) [2] Power (強制覆蓋) : ").strip() or "1"
        if input("確認執行? (y/n): ").lower() != 'y': return

        # Cache
        print("🗺️  Building Cache...")
        curr_map = build_curriculum_map()
        all_skills = SkillInfo.query.filter_by(is_active=True).all()
        
        cache = []
        for s in all_skills:
            info = curr_map.get(s.skill_id)
            pos = info["pos"] if info else CurriculumPosition(0, "", 0, 0)
            cache.append({"id": s.skill_id, "name": s.skill_ch_name, "pos": pos})
        
        skill_map = {s.skill_id: s for s in all_skills}
        model = get_model()

        # Processing
        for skill in tqdm(target_skills, desc="Running"):
            if mode == '1' and skill.prerequisites:
                continue

            # 1. 取得分區候選人
            z1, z2, z3 = get_candidate_skills(skill, cache)
            
            # 🔥 [LOG] 顯示分區數量
            tqdm.write(f"\n[分析] {skill.skill_ch_name}")
            tqdm.write(f"   📊 候選: Z1(同章)={len(z1)} | Z2(同冊)={len(z2)} | Z3(跨冊)={len(z3)}")

            ex = TextbookExample.query.filter_by(skill_id=skill.skill_id).first()
            
            # 2. AI 挑選
            ai_ids = identify_prerequisites(model, skill, (z1, z2, z3), ex.problem_text if ex else None)
            
            # 3. 補位 (Fallback)
            final_ids = []
            seen = set()

            # (A) AI 結果
            for pid in ai_ids:
                if pid in skill_map and pid != skill.skill_id and pid not in seen:
                    final_ids.append(pid)
                    seen.add(pid)
            
            ai_count = len(final_ids)

            # (B) Python 補滿
            # 順序：先 Z1 (同章最近) -> Z2 (同冊最近) -> Z3 (以前最近)
            fallback_pool = z1 + z2 + z3 
            
            for cand in fallback_pool:
                if len(final_ids) >= 5: break
                if cand['id'] not in seen and cand['id'] != skill.skill_id:
                    final_ids.append(cand['id'])
                    seen.add(cand['id'])

            # 4. 寫入
            if final_ids:
                try:
                    skill.prerequisites = []
                    for fid in final_ids:
                        skill.prerequisites.append(skill_map[fid])
                    db.session.commit()
                    
                    # 🔥 [LOG] 顯示更新結果
                    tqdm.write(f"   💾 Update: {len(final_ids)} 筆 (AI:{ai_count} + 補位:{len(final_ids)-ai_count})")
                    
                except Exception as e:
                    db.session.rollback()
                    tqdm.write(f"   ❌ Error: {e}")
            else:
                tqdm.write("   ⚠️ No Candidates found.")
            
            time.sleep(0.5)

        print("\n✅ 完成！")

if __name__ == "__main__":
    main()