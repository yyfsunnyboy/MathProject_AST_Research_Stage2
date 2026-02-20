
import subprocess
import os

def merge_docs():
    try:
        # 1. Get V2 content from git (Historical) - using unicode escape for safety
        print("Reading V2 content from git...")
        # Note: git outputs bytes. We assume utf-8 for markdown files.
        try:
            v2_bytes = subprocess.check_output(['git', 'show', 'HEAD:docs/競賽文件/02_技術細節/02_技術細節.md'])
            v2_content = v2_bytes.decode('utf-8')
        except UnicodeDecodeError:
            print("Warning: V2 content is not utf-8, trying cp950 or similar...")
            try:
                v2_content = v2_bytes.decode('cp950')
            except:
                print("Failed to decode V2 content.")
                raise

        # 2. Get V3 content from local file (Deep Dive)
        print("Reading V3 content from local file...")
        try:
            with open(r'docs/競賽文件/02_技術細節/02_技術細節_V3_DeepDive.md', 'r', encoding='utf-8') as f:
                v3_content = f.read()
        except FileNotFoundError:
            print("V3 file not found! Attempting to read current content instead.")
            # If V3 doesn't exist separately, assume current content IS V3 (Deep Dive)
            with open(r'docs/競賽文件/02_技術細節/02_技術細節.md', 'r', encoding='utf-8') as f:
                v3_content = f.read()
        
        # 3. Define separator
        separator = '\n\n<br>\n<br>\n<br>\n\n---\n---\n\n# Part II: 2026-02-20 技術深度剖析 (Deep Dive Update)\n\n> **說明**: 以下內容為 V3.0 新增的深度技術剖析。請注意，本部分將使用更精確的術語 **"Scaffolding Prompt (鷹架 Prompt)"** 來取代 Part I 中的 "Golden Prompt" / "Engineered Prompt"，以符合最新的架構定義。\n\n---\n\n'

        # 4. Write merged content
        print("Writing merged content...")
        target_file = r'docs/競賽文件/02_技術細節/02_技術細節.md'
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(str(v2_content) + separator + str(v3_content))
            
        print("Merge successful!")
        
    except Exception as e:
        print(f"Error during merge: {e}")
        exit(1)

if __name__ == "__main__":
    merge_docs()
