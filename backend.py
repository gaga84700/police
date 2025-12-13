import cv2
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import threading

class ModelHandler:
    def __init__(self, model_id="vikhyatk/moondream2", device_pref="auto"):
        """
        Initializes the Moondream model.
        device_pref: 'auto', 'cpu', 'cuda'
        """
        print(f"Loading model: {model_id} with preference: {device_pref}...")
        
        self.device = "cpu"
        
        # Determine target device
        if device_pref == "cpu":
            self.device = "cpu"
        elif device_pref == "cuda":
             if torch.cuda.is_available():
                 self.device = "cuda"
             else:
                 print("CUDA requested but not available. Falling back to CPU.")
                 self.device = "cpu"
        else: # auto
             self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Target device: {self.device}")
        
        # Load model and tokenizer
        # trust_remote_code=True is required for moondream
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, 
                trust_remote_code=True,
                attn_implementation="eager",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            # Test inference if on CUDA to catch "no kernel image" errors early
            if self.device == "cuda":
                 print("Performing self-test on CUDA...")
                 try:
                     # Create a tiny dummy image
                     dummy = Image.new('RGB', (32, 32))
                     enc = self.model.encode_image(dummy)
                     # If we got here, encoding worked
                     print("CUDA self-test passed.")
                 except Exception as e:
                     print(f"CUDA self-test failed: {e}")
                     if device_pref == "auto":
                         print("Auto-fallback to CPU...")
                         self.device = "cpu"
                         # Reload model on CPU
                         self.model = AutoModelForCausalLM.from_pretrained(
                            model_id, 
                            trust_remote_code=True,
                            attn_implementation="eager",
                            torch_dtype=torch.float32
                        ).to(self.device)
                     else:
                         raise e # Re-raise if user specifically asked for CUDA

            print(f"Model loaded successfully on {self.device}.")
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            raise e

    def analyze_frame(self, frame_pil, prompt):
        """
        Analyzes a single frame using the model.
        Returns True if the prompt checks out, or the text answer.
        For this use case, we might want to ask a question that gives a boolean-like answer 
        or just describe the image and do keyword matching.
        
        However, Moondream is good at answering questions.
        Strategy: Ask "Is there {prompt} in this image? Answer yes or no."
        """
        enc_image = self.model.encode_image(frame_pil)
        # Construct a query that forces a yes/no if possible, or just ask normally.
        # Simple prompt appending might be better for flexibility.
        # "Describe this image." -> Text search?
        # "Is {prompt} happening?" -> Yes/No.
        
        # Let's try the direct question approach first, users can type "A man opening a door"
        # We transform it to "Is a man opening a door visible? Answer yes or no."
        
        # Actually, for broader matching, maybe just generating a caption is safer 
        # but slower if we want specific event detection.
        # Let's stick to the user's prompt being the condition.
        
        # For Moondream, the standard usage is model.answer_question(enc_image, question, tokenizer)
        
        answer = self.model.answer_question(enc_image, prompt, self.tokenizer)
        return answer

class VideoProcessor:
    def __init__(self, model_handler: ModelHandler):
        self.model_handler = model_handler
        self.running = False
        self.thread = None

    def start_analysis(self, video_path, prompt, callback_match, callback_progress):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._analyze_loop, args=(video_path, prompt, callback_match, callback_progress))
        self.thread.start()

    def stop_analysis(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _analyze_loop(self, video_path, prompt, callback_match, callback_progress, threshold=None):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # We verify 1 frame per second
        current_sec = 0
        
        print(f"[Analysis Loop] Starting analysis: {video_path}, Duration: {duration}s, Total Frames: {total_frames}, FPS: {fps}")
        
        while self.running and current_sec < duration:
            # Set position
            target_pos = current_sec * 1000
            cap.set(cv2.CAP_PROP_POS_MSEC, target_pos)
            ret, frame = cap.read()
            if not ret:
                print(f"[Analysis Loop] Frame read failed at second {current_sec}. Stopping.")
                break
            
            # Convert to PIL
            # OpenCV is BGR, PIL needs RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            
            print(f"[Analysis Loop] Analyzing frame at {current_sec}s...")
            try:
                answer = self.model_handler.analyze_frame(frame_pil, prompt)
                print(f"[Analysis Loop] Model Answer: {answer}")
                
                is_match = False
                
                if threshold is not None:
                    # Score mode: Expect "85", "Confidence: 90", etc.
                    # Simple heuristic: find the first number in the string
                    import re
                    nums = re.findall(r'\d+', answer)
                    if nums:
                        score = int(nums[0])
                        print(f"  -> Parsed Score: {score}, Threshold: {threshold}")
                        if score >= threshold:
                            is_match = True
                    else:
                        print(f"  -> Could not parse score from '{answer}'")
                
                else:
                    # Legacy Yes/No mode
                    answer_lower = answer.lower().strip()
                    if answer_lower.startswith("yes"):
                        is_match = True
                
                if is_match:
                    # Pass score if available, otherwise assume high confidence for "Yes"
                    final_score = score if (threshold is not None and 'score' in locals()) else None
                    print(f"[MATCH] Seconds: {current_sec}, Answer: {answer}, Score: {final_score}")
                    callback_match(current_sec, final_score)

            except Exception as e:
                print(f"[Analysis Loop] Model Error: {e}")
                
            callback_progress(current_sec / duration)
            current_sec += 1
        
        cap.release()
        self.running = False
        print("Analysis finished.")

if __name__ == "__main__":
    # Test stub
    pass
