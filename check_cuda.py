import os
import sys

# Add ComfyUI DLL paths
comfy_path = r"f:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded"
torch_lib = r"f:\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded\Lib\site-packages\torch\lib"
os.environ['PATH'] = comfy_path + ";" + torch_lib + ";" + os.environ['PATH']

import torch

print(f"Python: {sys.version}")
print(f"Torch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
