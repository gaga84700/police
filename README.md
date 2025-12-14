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
- 🔍 **Natural Language Search** - Describe what you're looking for (Chinese/English)
- 📊 **Confidence Threshold** - Filter results by AI confidence (0-100%)
- ⚡ **Speed Options** - Normal (1s/frame), Fast (2s), Ultra Fast (3s)
- 🎬 **Video Controls** - Timeline slider, play/pause, click-to-seek & auto-play
- ✅ **Prompt Preview** - Confirm AI prompt before analysis starts
- ⏱️ **Time Stats** - Video duration and analysis time display
- 🎞️ **Multi-format** - MP4, AVI, MKV support

## 🤖 About Moondream AI

This project uses [**Moondream**](https://moondream.ai/) - a fast & powerful vision language model.

| Feature | Description |
|---------|-------------|
| **Model Size** | ~1.87B parameters (lightweight) |
| **Speed** | Optimized for continuous processing |
| **Capabilities** | Point, detect, count, reason, describe |
| **License** | Open source, free for local use |
| **Hardware** | CPU or GPU compatible |

### What Moondream Can Do

- 🔍 **Visual Question Answering** - Ask questions about image content
- 🏷️ **Object Detection** - Locate and identify objects
- 📝 **Image Captioning** - Generate descriptions
- 🎯 **Pointing/Localization** - Find specific elements
- 🔢 **Counting** - Count objects in scenes

> 💡 Learn more: [moondream.ai](https://moondream.ai/) | [Documentation](https://docs.moondream.ai) | [Playground](https://moondream.ai/c/playground)

## 🛠️ Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.10+
- **GPU**: NVIDIA GPU with CUDA recommended (CPU works but slower)
- **VRAM**: 4GB+

## ✅ Tested Configurations

| Status | GPU | Python | PyTorch | CUDA | Notes |
|--------|-----|--------|---------|------|-------|
| ✅ Working | RTX 5070 Ti | 3.13.9 | 2.9.1+cu130 | 13.0 | Blackwell/SM120 |
| ✅ Working | RTX 3090 | 3.10.x | 2.1.0+cu118 | 11.8 | Ampere |
| ❌ Failed | RTX 5070 Ti | 3.10.9 | 2.6.0+cu124 | 12.4 | `no kernel image` |

> ⚠️ **RTX 50 Series**: Requires PyTorch 2.9+ with CUDA 13.0

## ⚡ Performance Benchmarks

Tested on **RTX 5070 Ti** with a **120-second video**:

| Speed Mode | Interval | Analysis Time | Frames Analyzed |
|------------|----------|---------------|-----------------|
| 正常 (Normal) | 1s/frame | ~30 seconds | 120 frames |
| 快速 (Fast) | 2s/frame | ~15 seconds | 60 frames |
| 極速 (Ultra) | 3s/frame | ~10 seconds | 40 frames |

> 💡 **Tip**: Use "Fast" or "Ultra" for initial scanning, then "Normal" for detailed analysis.

## 🚀 Installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-video-search.git
cd ai-video-search

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### GPU Support (Optional)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Run

```bash
run.bat          # Windows
python ui_main.py  # Direct
```

> First run downloads Moondream2 model (~3GB)

## 📖 Usage

1. **Load Video** - Click load button
2. **Enter Keywords** - Chinese or English (e.g., "紅色車子", "person running")
3. **Set Threshold** - Adjust confidence slider (default 70%)
4. **Set Speed** - Normal/Fast/Ultra Fast
5. **Start Search** - Review AI prompt in dialog → Confirm
6. **View Results** - Click any result to jump & auto-play

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| GUI | PySide6 |
| AI Model | [Moondream2](https://huggingface.co/vikhyatk/moondream2) (~1.87B params) |
| Video | OpenCV |
| Translation | deep-translator |

## 📁 Project Structure

```
├── ui_main.py        # GUI application
├── backend.py        # AI & video processing
├── run.bat           # Windows launcher
├── requirements.txt
├── README.md
└── README_zh-TW.md
```

## 📄 License

MIT License

## 🙏 Acknowledgments

- [Moondream2](https://huggingface.co/vikhyatk/moondream2) by vikhyatk
- [PySide6](https://www.qt.io/qt-for-python)
- [deep-translator](https://github.com/nidhaloff/deep-translator)
