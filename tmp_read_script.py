import glob, os

files = sorted(glob.glob('generated_scripts/*ab2*.py'), key=os.path.getmtime, reverse=True)
if files:
    fname = files[0]
    print(f'=== FILE: {fname} ===')
    with open(fname, encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(content)
else:
    print("No ab2 files found.")
