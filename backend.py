import cv2
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import threading

class ModelHandler:
    def __init__(self, model_id="vikhyat/moondream2"):
        """
        Initializes the Moondream model.
        """
        print(f"Loading model: {model_id}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load model and tokenizer
        # trust_remote_code=True is required for moondream
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            trust_remote_code=True,
            revision="2024-08-26" # Pinning revision for stability if needed, or remove
        ).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision="2024-08-26")
        print("Model loaded successfully.")

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

    def _analyze_loop(self, video_path, prompt, callback_match, callback_progress):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # We verify 1 frame per second
        current_sec = 0
        
        print(f"Starting analysis: {video_path}, Duration: {duration}s")
        
        while self.running and current_sec < duration:
            # Set position
            cap.set(cv2.CAP_PROP_POS_MSEC, current_sec * 1000)
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to PIL
            # OpenCV is BGR, PIL needs RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            
            # Run model
            # We wrap the user prompt to ask for existence.
            # Or we assume the user knows prompts. 
            # "幫我找門被打開的時候" -> "Is the door being opened?" (Translation needed?)
            # Moondream works best with English. The user prompt might be in Chinese.
            # We might need a small translation layer or ask user to input English.
            # Assuming user inputs English or we match Chinese keywords against generated caption?
            # 
            # WAITING FOR CLARIFICATION OR JUST IMPLEMENT GENERIC
            # Let's assume for now we use the prompt as is, 
            # but maybe we should format it as a Yes/No question if it isn't one.
            
            answer = self.model_handler.analyze_frame(frame_pil, prompt)
            
            # Refined matching logic
            answer_lower = answer.lower().strip()
            # Check if it starts with yes, or constitutes a clear affirmative
            if answer_lower.startswith("yes"):
                print(f"[MATCH] Seconds: {current_sec}, Answer: {answer}")
                callback_match(current_sec)
            else:
                pass
                # print(f"Seconds: {current_sec}, Answer: {answer}")
            
            callback_progress(current_sec / duration)
            current_sec += 1
        
        cap.release()
        self.running = False
        print("Analysis finished.")

if __name__ == "__main__":
    # Test stub
    pass
