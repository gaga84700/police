import sys
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QListWidget, QProgressBar, QSplitter)
from PySide6.QtCore import Qt, QTimer, Slot, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
import backend
from deep_translator import GoogleTranslator

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
            self.finished.emit(self.text)


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
        
        header_layout.addWidget(self.btn_load)
        header_layout.addLayout(prompt_layout)
        header_layout.addWidget(self.btn_start)
        
        # Header layout stretch
        header_layout.setStretch(1, 1) # Give prompt area more space
        
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
        
        # Footer: Progress
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("準備就緒 (系統初始化中，請稍候模型載入...)")

    def load_model(self):
        self.status_bar.showMessage("正在載入 AI 模型 (Moondream2)... 這可能需要一點時間")
        QApplication.processEvents()
        try:
            self.model_handler = backend.ModelHandler()
            self.status_bar.showMessage("模型載入完成。請載入影片。")
        except Exception as e:
            self.status_bar.showMessage(f"模型載入失敗: {e}")

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
        if not prompt:
            self.status_bar.showMessage("請輸入 Prompt!")
            return

        self.list_results.clear()
        self.progress_bar.setValue(0)
        self.btn_start.setEnabled(False)
        self.status_bar.showMessage("正在分析中...")
        
        self.worker = AnalysisWorker(self.video_path, prompt, self.model_handler)
        self.worker.match_found.connect(self.add_match)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.start()

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
