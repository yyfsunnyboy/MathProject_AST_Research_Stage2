import traceback
from PIL import Image

try:
    from pix2text import Pix2Text
    print("Pix2Text Loaded")
    p2t = Pix2Text(device='cpu', formula_config={'model_type':'mfd'})
    print("Instance initialized on CPU")
    img = Image.new('RGB', (100, 100))
    res = p2t.recognize_formula(img)
    print("Result:", type(res))
except Exception as e:
    print(">>> CRASH MSG:", str(e))
    traceback.print_exc()
