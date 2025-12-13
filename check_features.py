import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image

try:
    model_id = "vikhyatk/moondream2"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    # We need to use the ComfyUI path trick implicitly or assumed standard env
    # Since we are running with the ComfyUI python which has the libs, standard import works
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    ).to(device)
    
    print(f"Has detect: {hasattr(model, 'detect')}")
    
    if hasattr(model, 'detect'):
        print("Testing detect...")
        img = Image.new('RGB', (64, 64), color='red')
        # Detect requires (image, prompt, tokenizer)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Assuming detect signature
        try:
             res = model.detect(img, "red color", tokenizer)
             print(f"Detect Result: {res}")
        except Exception as e:
             print(f"Detect failed: {e}")

except Exception as e:
    print(f"Error: {e}")
