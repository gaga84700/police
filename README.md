# 🚓 AI Video Search Tool

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![Moondream2](https://img.shields.io/badge/AI-Moondream2-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**English** | [繁體中文](README_zh-TW.md)

A local AI-powered video analysis tool using **Moondream2** Vision Language Model. Search surveillance footage using natural language queries like "person in red" or "white car" - all completely offline.

> **Privacy First**: All processing runs 100% locally. No cloud uploads, no data leakage.

---

## ✨ Features

- 🔒 **Fully Offline** - Sensitive footage never leaves your machine
- 🔍 **Natural Language Search** - Describe what you're looking for in plain text
- 🌐 **Chinese Support** - Auto-translation from Chinese to English via `deep-translator`
- 📊 **Confidence Scores** - Filter results by AI confidence threshold (0-100%)
- 🎬 **Video Controls** - Timeline slider, play/pause, click-to-seek
- ⏱️ **Time Stats** - See video duration and analysis time
- 🎞️ **Multi-format** - Supports MP4, AVI, MKV

## 📸 Screenshot

```
┌─────────────────────────────────────────────────────────────┐
│ [Load Video] [Device: Auto ▼] [中文輸入] [Threshold: 70%]  │
│ [Start Search] [Stop]                                       │
├─────────────────────────────────────┬───────────────────────┤
│                                     │ Search Results:       │
│         Video Preview               │ [Score: 85] 00:01:23  │
│                                     │ [Score: 92] 00:02:45  │
│    ══════════●══════════            │ [Score: 78] 00:05:12  │
│    [Play/Pause] [Pause]             │                       │
├─────────────────────────────────────┴───────────────────────┤
│ System Logs                                                 │
│ > Model loaded on: cuda                                     │
│ > Analysis Complete! Video: 120.0s, Time: 15.4s             │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.10+
- **GPU**: NVIDIA GPU with CUDA recommended (CPU works but slower)
- **VRAM**: 4GB+ for smooth operation

## ✅ Tested Configurations

| Status | GPU | Python | PyTorch | CUDA | Notes |
|--------|-----|--------|---------|------|-------|
| ✅ Working | RTX 5070 Ti | 3.13.9 | 2.9.1+cu130 | 13.0 | Blackwell/SM120 support |
| ✅ Working | RTX 3090 | 3.10.x | 2.1.0+cu118 | 11.8 | Ampere |
| ❌ Failed | RTX 5070 Ti | 3.10.9 | 2.6.0+cu124 | 12.4 | `no kernel image` error |

> ⚠️ **RTX 50 Series Users**: Requires PyTorch 2.9+ with CUDA 13.0 for SM120 architecture support.

## 🚀 Installation

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/ai-video-search.git
cd ai-video-search

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. GPU Support (Optional but Recommended)

For NVIDIA GPU acceleration, install PyTorch with CUDA:

```bash
# Check your CUDA version first, then install matching PyTorch
# Example for CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Run

```bash
# Windows
run.bat

# Or directly
python ui_main.py
```

> **Note**: First run downloads the Moondream2 model (~3GB). Please wait.

## 📖 Usage

1. **Load Video**: Click `Load Video` button
2. **Enter Keywords**: Type in Chinese (e.g., "紅色車子") or English
3. **Set Threshold**: Adjust confidence slider (70% default)
4. **Start Search**: Click `Start` - AI analyzes frame-by-frame
5. **View Results**: 
   - Click any result to jump to that timestamp
   - Video auto-plays from clicked position
   - Scores show AI confidence level

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| GUI | PySide6 (Qt for Python) |
| AI Model | [Moondream2](https://huggingface.co/vikhyatk/moondream2) (~1.87B params) |
| Video | OpenCV |
| Translation | deep-translator (Google Translate) |

## 📁 Project Structure

```
ai-video-search/
├── ui_main.py      # Main GUI application
├── backend.py      # AI model & video processing
├── run.bat         # Windows launcher
├── requirements.txt
└── README.md
```

## ⚠️ Limitations

- Model accuracy is lower than GPT-4V (but runs locally!)
- Complex scene understanding may be limited
- English prompts work better than Chinese (auto-translation helps)

## 📄 License

MIT License - Free for personal and commercial use.

## 🙏 Acknowledgments

- [Moondream2](https://huggingface.co/vikhyatk/moondream2) by vikhyatk
- [PySide6](https://www.qt.io/qt-for-python)
- [deep-translator](https://github.com/nidhaloff/deep-translator)
