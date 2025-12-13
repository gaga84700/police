from huggingface_hub import model_info

ids = ["vikhyat/moondream2", "vikhyatk/moondream2"]

for mid in ids:
    try:
        info = model_info(mid)
        print(f"[SUCCESS] Found model: {mid}")
        print(f"  - Author: {info.author}")
        print(f"  - Downloads: {info.downloads}")
    except Exception as e:
        print(f"[FAILED] Could not find model: {mid}")
        # print(f"  Reason: {e}")
