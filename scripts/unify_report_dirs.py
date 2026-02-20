
import os
import shutil
import re

reports_root = r"E:\Python\MathProject_AST_Research\agent_tools\reports"

def slugify(text):
    # Same logic as benchmark.py model_slug
    _slug = text.split(':')[0]
    _slug = re.sub(r'[^a-zA-Z0-9]+', '_', _slug)
    _slug = re.sub(r'_+', '_', _slug).strip('_')
    return _slug

for skill_dir in os.listdir(reports_root):
    skill_path = os.path.join(reports_root, skill_dir)
    if not os.path.isdir(skill_path):
        continue
    
    for model_dir in os.listdir(skill_path):
        model_path = os.path.join(skill_path, model_dir)
        if not os.path.isdir(model_path):
            continue
        
        target_slug = slugify(model_dir)
        if target_slug != model_dir:
            target_path = os.path.join(skill_path, target_slug)
            
            print(f"🔄 Merging {model_path} -> {target_path}")
            
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            
            # Move contents
            for item in os.listdir(model_path):
                s_item = os.path.join(model_path, item)
                t_item = os.path.join(target_path, item)
                
                if os.path.isdir(s_item):
                    # For gen_code, we might need to merge nested
                    if not os.path.exists(t_item):
                        shutil.move(s_item, t_item)
                    else:
                        # Merge files inside
                        for sub_item in os.listdir(s_item):
                            sub_s = os.path.join(s_item, sub_item)
                            sub_t = os.path.join(t_item, sub_item)
                            if not os.path.exists(sub_t):
                                shutil.move(sub_s, sub_t)
                            else:
                                print(f"  ⚠️ Collision: {sub_t} already exists. Skipping.")
                else:
                    if not os.path.exists(t_item):
                        shutil.move(s_item, t_item)
                    else:
                        print(f"  ⚠️ Collision: {t_item} already exists. Skipping.")
            
            # Remove empty source
            try:
                shutil.rmtree(model_path)
                print(f"  ✅ Removed {model_path}")
            except Exception as e:
                print(f"  ❌ Failed to remove {model_path}: {e}")

print("🎉 Directory unification complete.")
