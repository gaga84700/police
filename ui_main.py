import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QListWidget, QProgressBar, QSplitter, 
                               QTextEdit, QComboBox, QSlider, QMessageBox)
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
            # Using deep_translator with explicit zh-TW source
            translated = GoogleTranslator(source='zh-TW', target='en').translate(self.text)
            self.finished.emit(translated)
        except Exception as e:
            # Fallback to original text if translation fails (e.g. no internet)
            logger.log_signal.emit(f"Translation error: {e}")
            # Do NOT emit original text blindly if it's identical to input, 
            # but user sees it anyway. The print will now show in console.
            self.finished.emit(f"[Error: {e}]")



class AnalysisWorker(QThread):
    match_found = Signal(float, object)  # seconds, score
    progress_update = Signal(float)
    finished = Signal(object)  # error or None

    def __init__(self, video_path, prompt, model_handler, threshold=None):
        super().__init__()
        self.video_path = video_path
        self.prompt = prompt
        self.model_handler = model_handler
        self.threshold = threshold
        self.processor = backend.VideoProcessor(model_handler)

    def run(self):
        # Determine prompt format based on threshold
        formatted_prompt = ""
        if self.threshold is not None:
             # Ask for score
             formatted_prompt = f"Rate the confidence that '{self.prompt}' is in this image from 0 to 100. Return ONLY the number."
        else:
             formatted_prompt = f"Is '{self.prompt}' visible in this image? Answer yes or no."
        
        # Log the prompt
        logger.log_signal.emit(f"Starting Analysis with Prompt: [{formatted_prompt}]")
        logger.log_signal.emit(f"Threshold: {self.threshold if self.threshold else 'None (Yes/No mode)'}")

        self.processor.running = True  # Fix: Must enable running flag!
        self.processor._analyze_loop(
            self.video_path, 
            formatted_prompt, 
            self.handle_match, 
            self.handle_progress,
            threshold=self.threshold # Pass threshold to loop
        )
        self.finished.emit(None)

    def handle_match(self, timestamp, score=None):
        self.match_found.emit(timestamp, score)

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
        self.is_slider_drag = False
        self.analysis_start_time = 0.0
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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ===== TECH STYLE CSS =====
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0f;
            }
            QWidget {
                background-color: #0a0a0f;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a3a, stop:1 #1a1a2a);
                border: 1px solid #00d4ff;
                border-radius: 6px;
                padding: 8px 16px;
                color: #00d4ff;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a4a, stop:1 #2a2a3a);
                border: 1px solid #00ffff;
                color: #00ffff;
            }
            QPushButton:pressed {
                background: #00d4ff;
                color: #0a0a0f;
            }
            QPushButton:disabled {
                background: #1a1a1a;
                border: 1px solid #333;
                color: #555;
            }
            QLineEdit {
                background-color: #1a1a2a;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #00ffff;
            }
            QComboBox {
                background-color: #1a1a2a;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                padding: 6px;
                color: #00d4ff;
            }
            QComboBox:hover {
                border: 1px solid #00ffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2a;
                border: 1px solid #00d4ff;
                selection-background-color: #00d4ff;
                selection-color: #0a0a0f;
            }
            QSlider::groove:horizontal {
                background: #1a1a2a;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00d4ff;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #00ff88);
                border-radius: 4px;
            }
            QProgressBar {
                background-color: #1a1a2a;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                text-align: center;
                color: #00d4ff;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #00ff88);
                border-radius: 3px;
            }
            QListWidget {
                background-color: #0f0f1a;
                border: 1px solid #00d4ff;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #00d4ff;
                color: #0a0a0f;
            }
            QListWidget::item:hover {
                background-color: #1a2a3a;
            }
            QLabel {
                color: #00d4ff;
                font-weight: bold;
            }
            QSplitter::handle {
                background-color: #00d4ff;
                width: 2px;
            }
        """)

        # Header: Controls
        header_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("載入影片 (Load Video)")
        self.btn_load.clicked.connect(self.load_video)
        
        # Device Selector (GPU default, no Auto)
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("裝置:"))
        self.combo_device = QComboBox()
        self.combo_device.addItems(["GPU (CUDA)", "CPU"])
        self.combo_device.setToolTip("選擇運算裝置 (Select Device)")
        self.combo_device.setMinimumWidth(120)
        device_layout.addWidget(self.combo_device)
        
        # New Prompt Layout
        prompt_layout = QVBoxLayout()
        
        # Input Area (single input, no translate button)
        self.input_zh = QLineEdit()
        self.input_zh.setPlaceholderText("輸入搜尋關鍵字 (中/英文皆可, 例如: 紅色車子, person in red)...")
        prompt_layout.addWidget(self.input_zh)
        
        # Hidden field for translated prompt (used internally)
        self.input_en = QLineEdit()
        self.input_en.setVisible(False)  # Hidden from UI
        
        # Threshold Slider
        thresh_layout = QHBoxLayout()
        self.lbl_thresh = QLabel("信賴度門檻 (Threshold): 70%")
        self.slider_thresh = QSlider(Qt.Horizontal)
        self.slider_thresh.setRange(0, 100)
        self.slider_thresh.setValue(70)
        self.slider_thresh.valueChanged.connect(self.update_thresh_label)
        
        thresh_layout.addWidget(self.lbl_thresh)
        thresh_layout.addWidget(self.slider_thresh)
        prompt_layout.addLayout(thresh_layout)
        
        self.btn_start = QPushButton("▶ 開始搜尋")
        self.btn_start.clicked.connect(self.start_analysis)
        self.btn_start.setEnabled(False)
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa44, stop:1 #006622);
                border: 1px solid #00ff66;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00cc55, stop:1 #008833);
            }
            QPushButton:disabled {
                background: #1a1a1a;
                border: 1px solid #333;
                color: #555;
            }
        """)
        
        self.btn_stop = QPushButton("■ 停止分析")
        self.btn_stop.clicked.connect(self.stop_analysis)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aa2222, stop:1 #661111);
                border: 1px solid #ff4444;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #cc3333, stop:1 #882222);
            }
            QPushButton:disabled {
                background: #1a1a1a;
                border: 1px solid #333;
                color: #555;
            }
        """)

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
        self.slider_video = QSlider(Qt.Horizontal)
        self.slider_video.setRange(0, 1000)
        self.slider_video.sliderPressed.connect(self.on_slider_pressed)
        self.slider_video.sliderReleased.connect(self.on_slider_released)
        self.slider_video.sliderMoved.connect(self.seek_video)
        
        vid_ctrl_layout = QHBoxLayout()
        self.btn_play = QPushButton("播放/暫停 (Play/Pause)")
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_pause = QPushButton("暫停播放 (Pause)")
        self.btn_pause.clicked.connect(self.pause_video)
        
        vid_ctrl_layout.addWidget(self.btn_play)
        vid_ctrl_layout.addWidget(self.btn_pause)
        
        video_layout.addWidget(self.lbl_video)
        video_layout.addWidget(self.slider_video)
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
        splitter.setStretchFactor(0, 2)  # Video area
        splitter.setStretchFactor(1, 1)  # Results area (wider now)
        splitter.setSizes([600, 400])   # Initial sizes
        
        main_layout.addWidget(splitter)
        
        # Logs
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("系統日誌 (Logs):"))
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumHeight(120)
        self.text_log.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a12;
                color: #00ff88;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #00d4ff;
                border-radius: 4px;
            }
        """)
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
        # Determine device pref (GPU default, no Auto)
        txt = self.combo_device.currentText()
        pref = "cuda" if "GPU" in txt else "cpu"
        
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
                # Update slider if not dragging
                if not self.is_slider_drag:
                    current = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                    total = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if total > 0:
                        val = int((current / total) * 1000)
                        self.slider_video.blockSignals(True)
                        self.slider_video.setValue(val)
                        self.slider_video.blockSignals(False)
            else:
                self.timer.stop()
                self.is_playing = False
                self.btn_play.setText("播放 (Play)")

    def on_slider_pressed(self):
        self.is_slider_drag = True
        if self.is_playing:
            self.timer.stop()

    def on_slider_released(self):
        self.is_slider_drag = False
        if self.is_playing:
            fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 30
            self.timer.start(int(1000/fps))
        self.seek_video(self.slider_video.value())

    def seek_video(self, val):
        if self.cap and self.cap.isOpened():
            total = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if total > 0:
                frame_idx = int((val / 1000) * total)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = self.cap.read()
                if ret:
                    self.display_frame(frame)

    def pause_video(self):
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText("播放 (Play)")

    def toggle_play(self):
        if not self.cap:
            return
        
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.btn_play.setText("播放 (Play)")
        else:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            interval = int(1000/fps)
            self.timer.start(interval)
            self.is_playing = True
            self.btn_play.setText("暫停 (Pause)")

    def start_analysis(self):
        if not self.video_path or not self.model_handler:
            self.status_bar.showMessage("請先載入影片並等待模型載入完成")
            return
        
        # Get user input
        user_input = self.input_zh.text().strip()
        if not user_input:
            self.status_bar.showMessage("請輸入搜尋關鍵字!")
            return
        
        # Check if input is Chinese (contains CJK characters)
        import re
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', user_input))
        
        # Translate if Chinese
        if has_chinese:
            self.status_bar.showMessage("正在翻譯中...")
            QApplication.processEvents()
            try:
                prompt_en = GoogleTranslator(source='zh-TW', target='en').translate(user_input)
            except Exception as e:
                print(f"Translation failed: {e}")
                prompt_en = user_input  # Fallback
        else:
            prompt_en = user_input
        
        # Build the full AI prompt
        thresh = self.slider_thresh.value()
        if thresh > 0:
            full_prompt = f"Rate the confidence that '{prompt_en}' is in this image from 0 to 100. Return ONLY the number."
        else:
            full_prompt = f"Is '{prompt_en}' visible in this image? Answer yes or no."
        
        # Show confirmation dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("確認 AI 提示詞")
        msg.setIcon(QMessageBox.Question)
        msg.setText("即將送出以下提示詞給 AI 模型:")
        msg.setInformativeText(f"\n{full_prompt}\n\n信賴度門檻: {thresh}%")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Ok)
        
        # Style the dialog
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0a0a0f;
            }
            QMessageBox QLabel {
                color: #00d4ff;
                font-size: 12px;
            }
        """)
        
        result = msg.exec()
        if result != QMessageBox.Ok:
            self.status_bar.showMessage("已取消分析")
            return
        
        # Proceed with analysis
        self.list_results.clear()
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("正在分析中...")
        
        import time
        self.analysis_start_time = time.time()
        
        self.worker = AnalysisWorker(self.video_path, prompt_en, self.model_handler, threshold=thresh)
        self.worker.match_found.connect(self.add_match)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        
        # Update UI state
        self.btn_start.setEnabled(False)
        self.btn_load.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.worker.start()

    def stop_analysis(self):
        if self.worker:
            self.status_bar.showMessage("正在停止分析...")
            self.logger_log("User requested stop...") # Helper or direct log
            self.worker.stop()
            self.btn_stop.setEnabled(False) # Prevent multiple clicks

    def add_match(self, seconds, score=None):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time_str = "%02d:%02d:%02d" % (h, m, s)
        
        score_str = f"[Score: {score}] " if score is not None else ""
        item_text = f"{score_str}{time_str} ({int(seconds)}s)"
        
        self.list_results.addItem(item_text)
        self.list_results.scrollToBottom()

    def update_progress(self, val):
        self.progress_bar.setValue(int(val * 100))

    def analysis_finished(self, error=None):
        self.btn_start.setEnabled(True)
        self.btn_load.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        import time
        end_time = time.time()
        elapsed = end_time - self.analysis_start_time
        
        vid_dur = 0
        if self.cap:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps > 0: vid_dur = frames / fps
            
        msg = f"分析完成! 影片長度: {vid_dur:.1f}s, 分析耗時: {elapsed:.1f}s"
        self.status_bar.showMessage(msg)
        logger.log_signal.emit(msg)
        self.worker = None

    def on_result_clicked(self, item):
        if not self.cap:
            return
        
        text = item.text()
        try:
            import re
            match = re.search(r"\((\d+)s\)", text)
            if match:
                seconds = int(match.group(1))
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                if fps > 0:
                    target_frame = int(seconds * fps)
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                else:
                    self.cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
                
                ret, frame = self.cap.read()
                if ret:
                    self.display_frame(frame)
                    total = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if total > 0:
                        pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                        val = int((pos/total)*1000)
                        self.slider_video.blockSignals(True)
                        self.slider_video.setValue(val)
                        self.slider_video.blockSignals(False)
                
                # Auto-play from clicked position
                if not self.is_playing:
                    interval = int(1000/fps) if fps > 0 else 33
                    self.timer.start(interval)
                    self.is_playing = True
                    self.btn_play.setText("暫停 (Pause)")
            
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
        
        self.status_bar.showMessage("正在翻譯 (Translating)...")
        self.btn_trans.setEnabled(False)
        self.btn_trans.setText("翻譯中...")
        
        self.trans_worker = TranslationThread(text)
        self.trans_worker.finished.connect(self.on_translation_finished)
        self.trans_worker.start()

    def on_translation_finished(self, text):
        self.input_en.setText(text)
        self.btn_trans.setEnabled(True)
        self.btn_trans.setText("翻譯 (Translate)")
        
        if text.startswith("[Error"):
             logger.log_signal.emit(f"Translation Failed: {text}")
             self.status_bar.showMessage("翻譯失敗，請檢查網路或是翻譯服務")
        else:
             self.status_bar.showMessage("翻譯完成 (Translated)")

    def update_thresh_label(self, val):
        self.lbl_thresh.setText(f"信賴度門檻 (Threshold): {val}%")

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
