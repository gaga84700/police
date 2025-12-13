from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "vikhyatk/moondream2"
print(f"Starting download for {model_id}...")

try:
    # Download Tokenizer
    print("Downloading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    print("Tokenizer downloaded.")

    # Download Model
    print("Downloading Model (this may take a while)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        trust_remote_code=True
    )
    print("Model downloaded.")
    
    print("SUCCESS: Model and Tokenizer are downloaded to local cache.")
    
except Exception as e:
    print(f"ERROR: Download failed. Reason: {e}")
