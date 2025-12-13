import torch
import cv2
import PIL
import transformers
import PySide6.QtWidgets
import qdarktheme

print("Environment Verified.")
print(f"Torch: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
print(f"OpenCV: {cv2.__version__}")
