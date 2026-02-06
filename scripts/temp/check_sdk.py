try:
    from google import genai
    print("Version 2 SDK found")
except ImportError:
    print("Version 2 SDK NOT found")
