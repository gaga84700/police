# 🚓 AI 影片內容搜尋工具

[English](README.md) | **繁體中文**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![Moondream2](https://img.shields.io/badge/AI-Moondream2-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

一個使用 **Moondream2** 視覺語言模型的本地 AI 影片分析工具。透過自然語言（如「紅色車子」、「戴帽子的人」）搜尋監視器畫面 - 完全離線運行。

> **隱私優先**: 所有運算 100% 在本機執行，影片資料絕不上傳雲端。

---

## ✨ 功能特色

- 🔒 **完全離線** - 機敏影片不會外流
- 🔍 **自然語言搜尋** - 用文字描述你要找的畫面
- 🌐 **中文支援** - 自動翻譯中文為英文進行搜尋
- 📊 **信賴度分數** - 依 AI 信心度過濾結果 (0-100%)
- 🎬 **影片控制** - 時間軸滑桿、播放/暫停、點擊跳轉
- ⏱️ **時間統計** - 顯示影片長度與分析耗時
- 🎞️ **多格式支援** - MP4, AVI, MKV

## 📸 介面預覽

```
┌─────────────────────────────────────────────────────────────┐
│ [載入影片] [裝置: Auto ▼] [中文輸入] [信賴度: 70%]          │
│ [開始搜尋] [停止]                                           │
├─────────────────────────────────────┬───────────────────────┤
│                                     │ 搜尋結果:             │
│         影片預覽區                  │ [Score: 85] 00:01:23  │
│                                     │ [Score: 92] 00:02:45  │
│    ══════════●══════════            │ [Score: 78] 00:05:12  │
│    [播放/暫停] [暫停]               │                       │
├─────────────────────────────────────┴───────────────────────┤
│ 系統日誌                                                    │
│ > Model loaded on: cuda                                     │
│ > 分析完成! 影片長度: 120.0s, 分析耗時: 15.4s               │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 系統需求

- **作業系統**: Windows 10/11, Linux, macOS
- **Python**: 3.10+
- **GPU**: 建議使用 NVIDIA 顯示卡 + CUDA（CPU 也可運行但較慢）
- **VRAM**: 4GB 以上

## ✅ 測試過的環境配置

| 狀態 | GPU | Python | PyTorch | CUDA | 備註 |
|------|-----|--------|---------|------|------|
| ✅ 成功 | RTX 5070 Ti | 3.13.9 | 2.9.1+cu130 | 13.0 | Blackwell/SM120 支援 |
| ✅ 成功 | RTX 3090 | 3.10.x | 2.1.0+cu118 | 11.8 | Ampere |
| ❌ 失敗 | RTX 5070 Ti | 3.10.9 | 2.6.0+cu124 | 12.4 | `no kernel image` 錯誤 |

> ⚠️ **RTX 50 系列使用者**: 需要 PyTorch 2.9+ 搭配 CUDA 13.0 才能支援 SM120 架構。

## 🚀 安裝步驟

### 1. 下載與設定

```bash
git clone https://github.com/YOUR_USERNAME/ai-video-search.git
cd ai-video-search

# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
venv\Scripts\activate

# 啟動虛擬環境 (Linux/Mac)
source venv/bin/activate

# 安裝相依套件
pip install -r requirements.txt
```

### 2. GPU 加速 (選用但建議)

安裝支援 CUDA 的 PyTorch：

```bash
# 先確認你的 CUDA 版本，再安裝對應的 PyTorch
# 範例 (CUDA 12.1):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. 執行程式

```bash
# Windows
run.bat

# 或直接執行
python ui_main.py
```

> **注意**: 首次執行會自動下載 Moondream2 模型（約 3GB），請耐心等候。

## 📖 使用教學

1. **載入影片**: 點擊 `載入影片` 按鈕
2. **輸入關鍵字**: 輸入中文（如「紅色車子」）或英文
3. **設定門檻**: 調整信賴度滑桿（預設 70%）
4. **開始搜尋**: 點擊 `開始搜尋`，AI 會逐幀分析
5. **查看結果**: 
   - 點擊結果列表可跳至該時間點
   - 影片會自動從該位置開始播放
   - 分數顯示 AI 的信心程度

## 🔧 技術架構

| 元件 | 技術 |
|------|------|
| 介面 | PySide6 (Qt for Python) |
| AI 模型 | [Moondream2](https://huggingface.co/vikhyatk/moondream2) (~1.87B 參數) |
| 影片處理 | OpenCV |
| 翻譯 | deep-translator (Google Translate) |

## 📁 專案結構

```
ai-video-search/
├── ui_main.py      # 主程式 GUI
├── backend.py      # AI 模型與影片處理
├── run.bat         # Windows 啟動腳本
├── requirements.txt
├── README.md       # English
└── README_zh-TW.md # 繁體中文
```

## ⚠️ 限制

- 模型精度不如 GPT-4V（但可完全離線運行！）
- 複雜場景理解能力有限
- 英文提示效果較好（內建自動翻譯功能）

## 📄 授權條款

MIT License - 可自由用於個人與商業用途。

## 🙏 致謝

- [Moondream2](https://huggingface.co/vikhyatk/moondream2) by vikhyatk
- [PySide6](https://www.qt.io/qt-for-python)
- [deep-translator](https://github.com/nidhaloff/deep-translator)
