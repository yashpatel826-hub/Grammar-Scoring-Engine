# 🗣️ Grammar Scoring Engine for Spoken Audio

> A Deep Learning-based system that predicts grammar quality scores from spoken English audio recordings using pretrained language models.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- (Optional) NVIDIA GPU with CUDA for faster processing

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd Grammar-Scoring-Engine-for-Spoken-Audio
   ```

2. **Run the setup script (Windows)**
   ```bash
   setup.bat
   ```

   Or manually:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend\requirements.txt
   cd frontend && npm install
   ```

3. **Train the model**
   ```bash
   train_model.bat
   ```
   Or:
   ```bash
   python backend\train.py --epochs 20 --batch-size 8
   ```

4. **Start the full end-to-end app (frontend + backend)**
   ```bash
   run_server.bat
   ```

5. **Open the app**
   - Main app: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

---

## Overview

The goal of this project is to build a **Grammar Scoring Engine** that can evaluate the grammatical quality of spoken audio inputs. The model takes a **45–60 second `.wav` audio file** and predicts a **continuous score between 0 and 5**, based on the **MOS Likert Grammar Scale**.

### Features

- 🎙️ **Audio Recording** - Record audio directly in the browser
- 📁 **File Upload** - Upload WAV, MP3, M4A, OGG, or FLAC files
- 🔊 **Speech-to-Text** - Automatic transcription using Whisper ASR
- 📊 **Grammar Scoring** - DeBERTa-v3 based scoring with confidence levels
- 🎨 **Modern UI** - Beautiful, responsive web interface
- ⚡ **Fast API** - High-performance REST API with FastAPI

---

## Project Structure

```
Grammar-Scoring-Engine-for-Spoken-Audio/
├── backend/
│   ├── config.py          # Configuration settings
│   ├── preprocessing.py   # Audio preprocessing pipeline
│   ├── transcription.py   # Whisper ASR integration
│   ├── model.py           # DeBERTa-v3 classifier
│   ├── train.py           # Training script
│   ├── api.py             # FastAPI REST API
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/               # React pages/components
│   ├── public/            # Static assets
│   ├── package.json       # Frontend dependencies
│   └── vite.config.ts     # Vite configuration
├── Dataset/
│   ├── audios/
│   │   ├── train/         # Training audio files
│   │   └── test/          # Test audio files
│   ├── train.csv          # Training labels
│   └── test.csv           # Test filenames
├── models/                 # Saved model weights
├── transcripts/           # Cached transcriptions
├── setup.bat              # Windows setup script
├── run_server.bat         # Start API server
├── train_model.bat        # Train model
└── Readme.md              # This file
```

---

## 🗃️ Dataset

The dataset consists of:

### 🔊 Audio Files
- Stored in `.wav` format
- Sample rate: 16 kHz (converted during preprocessing)
- Duration: 45–60 seconds per clip

### 📄 CSV Files

| File Name | Description |
|-----------|-------------|
| `train.csv` | 444 audio filenames with MOS grammar scores |
| `test.csv` | 195 test audio filenames |

---

##  Methodology

### 🧼 Preprocessing
- **Peak Normalization** of audio signals
- **Voice Activity Detection (VAD)** for silence trimming
- Conversion to mono 16kHz for Whisper/ASR models

### 🗣️ Transcription
- Uses [`faster-whisper`](https://github.com/guillaumekln/faster-whisper) for high-quality ASR
- Transcripts cached as JSON for efficiency

### 🔡 Model Architecture
- **Base Model**: `microsoft/deberta-v3-base`
- **Task**: 11-class classification (0, 0.5, 1, ..., 5)
- **Output**: Weighted score + confidence

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/models/info` | Model information |
| POST | `/api/predict` | Upload audio and get score |
| POST | `/api/transcribe` | Transcribe audio only |
| POST | `/api/score-text` | Score text directly |

### Example Usage

```python
import requests

# Upload and score audio
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/predict",
        files={"file": f}
    )
    result = response.json()
    print(f"Score: {result['score']}/5.0")
    print(f"Transcript: {result['transcript']}")
```

---

## 📈 Evaluation Metrics

- **Cross-Entropy Loss** (classification)
- **RMSE** (regression evaluation)
- **Validation Accuracy**
- **Confusion Matrix** (saved as `models/confusion_matrix.png`)

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| ML Framework | PyTorch + Transformers |
| ASR | faster-whisper |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite + TypeScript |
| Model | DeBERTa-v3-base |

---

## Deployment

The frontend is ready for Vercel deployment. The backend should be deployed on Render using the included Docker setup so the FastAPI app has `ffmpeg` and other audio dependencies available.

### Deploy the frontend to Vercel

1. Import the repository into Vercel.
2. Set the Root Directory to `frontend`.
3. Set the build command to `npm run build`.
4. Set the output directory to `dist`.
5. Add an environment variable named `VITE_API_BASE_URL` and point it to your deployed backend URL.
6. Deploy.

The frontend includes a `vercel.json` rewrite so client-side routes like `/dashboard` and `/results` resolve correctly on refresh.

### Deploy the backend to Render

1. Create a new Web Service in Render from this repository.
2. Use the repository root and let Render detect `render.yaml`, or point it to the included Dockerfile.
3. Set `MONGO_URI` to your MongoDB connection string.
4. Keep `USE_CUDA=false` unless you are using a GPU-backed Render environment.
5. Set `FRONTEND_BASE_URL` to your Vercel site URL.
6. Deploy the service.

The backend service uses `backend/Dockerfile`, which installs `ffmpeg` and `libsndfile` for audio processing and Whisper decoding.

### Environment variables

If your backend is deployed at `https://your-backend.example.com`, set:

```text
VITE_API_BASE_URL=https://your-backend.example.com
```

For Render, set the backend variables:

```text
MONGO_URI=<your-mongodb-connection-string>
MONGO_DB_NAME=grammar_scoring
USE_CUDA=false
FRONTEND_BASE_URL=https://your-vercel-site.vercel.app
```

During local development, leaving `VITE_API_BASE_URL` empty continues to use the Vite dev proxy.

## � License

This project is for educational purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
