import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyBL3Yw3d3a5zT5C_OGQ5_drfLk5Q68DrWI'

from core.ai_wrapper import GoogleAIClient

client = GoogleAIClient('gemini-3-flash-preview', 0.1, max_tokens=65536)
print(f'SDK Type: {"New" if client.is_new_sdk else "Old"}')
print(f'Client: {type(client.client if hasattr(client, "client") else client.model)}')
