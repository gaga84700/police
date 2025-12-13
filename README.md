# 🚓 AI Video Search Tool (Police Edition)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![Moondream2](https://img.shields.io/badge/AI-Moondream2-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

這是一個專為警察與調查人員設計的單機版影片分析工具。利用輕量級的視覺語言模型 (VLM) `vikhyat/moondream2`，讓使用者能透過自然語言（如「有人開門」、「紅色車子」）快速搜尋長時間監視器畫面中的特定關鍵事件。

> **隱私聲明**: 本工具所有運算皆在本地端 (Local) 執行，無需上傳影片至雲端，確保案件資料絕對安全。

---

## ✨ 功能特色 (Features)

- 🔒 **完全離線執行**: 確保機敏影片資料不會外流。
- 🔍 **自然語言搜尋**: 整合 `deep-translator`，支援直接輸入中文關鍵字，系統自動翻譯並進行 AI 語意搜尋。
- ⚡ **快速驗證機制**: 搜尋結果以時間軸列表呈現，點擊即可瞬間跳轉至該片段進行人工確認。
- 🎞️ **支援多種格式**: 支援 MP4, AVI, MKV 等常見監控影片格式。
- 🖥️ **直觀介面**: 基於 PySide6 的極簡介面，專注於案件分析工作。

## 🛠️ 安裝需求 (Requirements)

- **OS**: Windows 10 / 11
- **Python**: 3.10 或更高版本
- **GPU**: 建議使用 NVIDIA 顯示卡並安裝 CUDA 驅動程式以獲得最佳效能（CPU 亦可運行但速度較慢）。

## 🚀 快速開始 (Quick Start)

### 1. 複製專案與安裝依賴

```bash
# 建立並啟動虛擬環境 (建議)
python -m venv venv
venv\Scripts\activate

# 安裝所需套件
pip install -r requirements.txt
```

### 2. 啟動程式

直接執行目錄下的批次檔：
```bash
run.bat
```
或使用指令：
```bash
python ui_main.py
```

*注意：首次執行時，系統會自動下載 moondream2 模型 (約 3GB)，請耐心等候。*

## 📖 使用教學 (Usage)

1. **載入影片**: 點擊左上角的 `載入影片 (Load Video)` 按鈕。
2. **輸入關鍵字**: 在上方輸入框輸入您想尋找的畫面描述（支援中文，例如：「白色休旅車」、「戴帽子的男人」）。
3. **自動翻譯**: 系統會自動將中文翻譯為英文顯示於下方唯讀欄位，確認翻譯無誤後即可搜尋。
4. **開始搜尋**: 點擊 `開始搜尋`，程式將逐秒分析影片內容。
5. **查看結果**: 
   - 右側列表 "Found at..." 顯示發現目標的時間點。
   - 點擊列表項目，左側預覽視窗將自動跳轉至該時間點。

## 🔧 技術棧 (Tech Stack)

- **Frontend**: PySide6 (Qt for Python)
- **Backend AI**: HuggingFace Transformers, Moondream2 (Tiny VLM)
- **Video Processing**: OpenCV
- **Translation**: deep-translator (Google Translate API)

## 📄 License

This project is licensed under the MIT License.
