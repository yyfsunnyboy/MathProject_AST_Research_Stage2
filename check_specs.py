
import psutil
import platform

def get_system_info():
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"CPU: {platform.processor()}")
    
    mem = psutil.virtual_memory()
    print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    
    try:
        import subprocess
        # Try to check NVIDIA GPU
        try:
            nvidia_smi = subprocess.check_output("nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader", shell=True).decode()
            print(f"NVIDIA GPU Info:\n{nvidia_smi}")
        except:
            print("No NVIDIA GPU detected via nvidia-smi")
            
    except Exception as e:
        print(f"Error checking GPU: {e}")

if __name__ == "__main__":
    get_system_info()
