import sys
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QListWidget, QProgressBar, QSplitter, 
                               QTextEdit, QComboBox)
from PySide6.QtCore import Qt, QTimer, Slot, Signal, QThread, QObject
from PySide6.QtGui import QImage, QPixmap
import backend
import sys # ensures sys is available
from deep_translator import GoogleTranslator

# Global signal for logging
class Logger(QObject):
    log_signal = Signal(str)

logger = Logger()

# Redirect stdout to logger
class StreamRedirector:
    def write(self, text):
        if text.strip():
            logger.log_signal.emit(str(text))
    def flush(self):
        pass

sys.stdout = StreamRedirector()
sys.stderr = StreamRedirector()


class TranslationThread(QThread):
    finished = Signal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            # Using deep_translator
            translated = GoogleTranslator(source='auto', target='en').translate(self.text)
            self.finished.emit(translated)
        except Exception as e:
            # Fallback to original text if translation fails (e.g. no internet)
            print(f"Translation error: {e}")
            # Do NOT emit original text blindly if it's identical to input, 
            # but user sees it anyway. The print will now show in console.
            self.finished.emit(f"[Error: {e}]")



class AnalysisWorker(QThread):
    match_found = Signal(float)
    progress_update = Signal(float)
    finished = Signal()

    def __init__(self, video_path, prompt, model_handler):
        super().__init__()
        self.video_path = video_path
        self.prompt = prompt
        self.model_handler = model_handler
        self.processor = backend.VideoProcessor(model_handler)

    def run(self):
        # Determine strict or flexible matching
        # For now, we append instructions to the prompt to get a yes/no
        # User prompt: "Door opening"
        # Query: "Is 'Door opening' visible in this image? Answer yes or no."
        formatted_prompt = f"Is '{self.prompt}' visible in this image? Answer yes or no."
        
        self.processor.running = True  # Fix: Must enable running flag!
        self.processor._analyze_loop(
            self.video_path, 
            formatted_prompt, 
            self.handle_match, 
            self.handle_progress
        )
        self.finished.emit()

    def handle_match(self, timestamp):
        self.match_found.emit(timestamp)

    def handle_progress(self, progress):
        self.progress_update.emit(progress)
    
    def stop(self):
        self.processor.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Video Search Tool - 警察專用版")
        self.resize(1200, 800)
        
        # Data
        self.video_path = None
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_video_frame)
        self.is_playing = False
        
        self.model_handler = None # Lazy load or async load
        self.worker = None

        # Translation
        self.translate_timer = QTimer()
        self.translate_timer.setSingleShot(True)
        self.translate_timer.timeout.connect(self.perform_translation)
        self.trans_worker = None


        self.init_ui()
        
        # Load model in background
        QTimer.singleShot(100, self.load_model)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Header: Controls
        header_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("載入影片 (Load Video)")
        self.btn_load.clicked.connect(self.load_video)
        
        # Device Selector
        device_layout = QVBoxLayout()
        self.combo_device = QComboBox()
        self.combo_device.addItems(["Auto", "CPU", "GPU (CUDA)"])
        self.combo_device.setToolTip("選擇運算裝置 (Select Device)")
        
        self.btn_reload = QPushButton("重載模型 (Reload)")
        self.btn_reload.clicked.connect(self.load_model)
        self.btn_reload.setMaximumWidth(100)
        
        device_layout.addWidget(QLabel("Device:"))
        device_layout.addWidget(self.combo_device)
        device_layout.addWidget(self.btn_reload)
        
        # New Prompt Layout
        prompt_layout = QVBoxLayout()
        
        self.input_zh = QLineEdit()
        self.input_zh.setPlaceholderText("在此輸入中文關鍵字 (例如: 紅色車子, 有人開門)...")
        self.input_zh.textChanged.connect(self.on_zh_text_changed)
        
        self.input_en = QLineEdit()
        self.input_en.setPlaceholderText("Translation (English) will appear here...")
        self.input_en.setReadOnly(True)
        # Style to look like read-only
        self.input_en.setStyleSheet("background-color: #2b2b2b; color: #aaaaaa; font-style: italic;")
        
        prompt_layout.addWidget(self.input_zh)
        prompt_layout.addWidget(self.input_en)
        
        self.btn_start = QPushButton("開始搜尋 (Start)")
        self.btn_start.clicked.connect(self.start_analysis)
        self.btn_start.setEnabled(False) # Enable after video load
        self.btn_start.setMinimumHeight(50) # Make it bigger
        
        self.btn_stop = QPushButton("停止分析 (Stop)")
        self.btn_stop.clicked.connect(self.stop_analysis)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumHeight(50)
        self.btn_stop.setStyleSheet("background-color: #8b0000; color: white;") # Dark red to indicate stop

        header_layout.addWidget(self.btn_load)
        header_layout.addLayout(device_layout)
        header_layout.addLayout(prompt_layout)
        header_layout.addWidget(self.btn_start)
        header_layout.addWidget(self.btn_stop)
        
        # Header layout stretch
        header_layout.setStretch(2, 1) # Give prompt area more space (index changed due to insert)
        
        main_layout.addLayout(header_layout)


        # Body: Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Video Player
        video_container = QWidget()
        video_layout = QVBoxLayout(video_container)
        self.lbl_video = QLabel("影片預覽區")
        self.lbl_video.setAlignment(Qt.AlignCenter)
        self.lbl_video.setStyleSheet("background-color: black; color: white;")
        self.lbl_video.setMinimumSize(640, 360)
        
        # Video Controls
        vid_ctrl_layout = QHBoxLayout()
        self.btn_play = QPushButton("播放/暫停")
        self.btn_play.clicked.connect(self.toggle_play)
        vid_ctrl_layout.addWidget(self.btn_play)
        
        video_layout.addWidget(self.lbl_video)
        video_layout.addLayout(vid_ctrl_layout)
        
        # Right: Results
        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.addWidget(QLabel("搜尋結果 (點擊跳轉):"))
        self.list_results = QListWidget()
        self.list_results.itemClicked.connect(self.on_result_clicked)
        result_layout.addWidget(self.list_results)
        
        splitter.addWidget(video_container)
        splitter.addWidget(result_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Logs
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("系統日誌 (Logs):"))
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumHeight(150)
        self.text_log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        log_layout.addWidget(self.text_log)
        main_layout.addLayout(log_layout)
        
        # Connect logger
        logger.log_signal.connect(self.append_log)

        
        # Footer: Progress
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("準備就緒 (系統初始化中，請稍候模型載入...)")

    def load_model(self):
        # Determine device pref
        txt = self.combo_device.currentText()
        pref = "auto"
        if "CPU" in txt: pref = "cpu"
        if "GPU" in txt: pref = "cuda"
        
        self.status_bar.showMessage(f"正在載入 AI 模型 ({pref})...")
        QApplication.processEvents()
        
        try:
            # If re-loading, clean up old (optional, but good practice)
            if self.model_handler:
                del self.model_handler
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            self.model_handler = backend.ModelHandler(device_pref=pref)
            
            # Update UI to reflect actual device used
            actual = self.model_handler.device
            self.status_bar.showMessage(f"模型載入完成。使用裝置: {actual}")
            logger.log_signal.emit(f"Model loaded on: {actual}")
            
        except Exception as e:
            self.status_bar.showMessage(f"模型載入失敗: {e}")
            logger.log_signal.emit(f"Model Load Error: {e}")

    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇影片", "", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            self.video_path = file_path
            self.cap = cv2.VideoCapture(file_path)
            
            # Show first frame
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Reset
            
            self.btn_start.setEnabled(True)
            self.status_bar.showMessage(f"已載入: {file_path}")

    def display_frame(self, frame):
        # Resize to fit label while keeping aspect ratio
        h, w, ch = frame.shape
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale
        lbl_w = self.lbl_video.width()
        lbl_h = self.lbl_video.height()
        p = convert_to_Qt_format.scaled(lbl_w, lbl_h, Qt.KeepAspectRatio)
        self.lbl_video.setPixmap(QPixmap.fromImage(p))

    def update_video_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
            else:
                self.timer.stop()
                self.is_playing = False

    def toggle_play(self):
        if not self.cap:
            return
        
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
        else:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            interval = int(1000/fps)
            self.timer.start(interval)
            self.is_playing = True

    def start_analysis(self):
        if not self.video_path or not self.model_handler:
            return
        
        # Use the English prompt if available, otherwise just use whatever is in zh (or mixed)
        # But per requirements, we send the English style.
        prompt = self.input_en.text()
        if not prompt:
             # Fallback if user didn't wait for translation or input empty
             prompt = self.input_zh.text()

        if not prompt:
            self.status_bar.showMessage("請輸入 Prompt!")
            return

        self.list_results.clear()
        self.progress_bar.setValue(0)
        self.worker = AnalysisWorker(self.video_path, prompt, self.model_handler)
        self.worker.match_found.connect(self.add_match)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        
        # Update UI state
        self.btn_start.setEnabled(False)
        self.btn_load.setEnabled(False) # Prevent changing video while analyzing
        self.btn_stop.setEnabled(True)
        
        self.worker.start()

    def stop_analysis(self):
        if self.worker:
            self.status_bar.showMessage("正在停止分析...")
            self.logger_log("User requested stop...") # Helper or direct log
            self.worker.stop()
            self.btn_stop.setEnabled(False) # Prevent multiple clicks

    def add_match(self, timestamp):
        # Convert seconds to HH:MM:SS
        m, s = divmod(timestamp, 60)
        h, m = divmod(m, 60)
        time_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        
        self.list_results.addItem(f"Found at {time_str} ({int(timestamp)}s)")
        # Scroll to bottom
        self.list_results.scrollToBottom()

    def update_progress(self, val):
        self.progress_bar.setValue(int(val * 100))

    def analysis_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_bar.showMessage("分析完成")
        self.worker = None

    def on_result_clicked(self, item):
        if not self.cap:
            return
        
        text = item.text()
        # Parse timestamp from text "Found at ... (123s)"
        try:
            sec_str = text.split("(")[-1].replace("s)", "")
            seconds = int(sec_str)
            
            self.cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
            # Show that frame immediately
            ret, frame = self.cap.read()
            if ret:
                self.display_frame(frame)
            
            # Pause playback if playing
            if self.is_playing:
                self.toggle_play()
                
        except Exception as e:
            print(f"Error seeking: {e}")

    def on_zh_text_changed(self):
        # Debounce
        self.translate_timer.start(800)

    def perform_translation(self):
        text = self.input_zh.text()
        if not text:
            self.input_en.clear()
            return
        
        # self.status_bar.showMessage("正在翻譯 (Translating)...")
        self.trans_worker = TranslationThread(text)
        self.trans_worker.finished.connect(self.on_translation_finished)
        self.trans_worker.start()

    def on_translation_finished(self, text):
        self.input_en.setText(text)
        # self.status_bar.showMessage("翻譯完成 (Translated)")

    def append_log(self, text):
        self.text_log.append(text)
        self.text_log.verticalScrollBar().setValue(self.text_log.verticalScrollBar().maximum())
        
    def logger_log(self, text):
         # Creating a valid Log message manually if needed
         self.append_log(text)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load theme?
    try:
        import qdarktheme
        app.setStyleSheet(qdarktheme.load_stylesheet())
    except:
        pass
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
