"""
Configuration settings for Grammar Scoring Engine
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
AUDIO_TRAIN_DIR = DATASET_DIR / "audios" / "train"
AUDIO_TEST_DIR = DATASET_DIR / "audios" / "test"
MODELS_DIR = BASE_DIR / "models"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"

# Load environment variables from backend/.env if present.
load_dotenv(BASE_DIR / "backend" / ".env")

# Create directories if they don't exist
MODELS_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Audio processing settings
SAMPLE_RATE = 16000
MAX_AUDIO_DURATION = 60  # seconds
MIN_AUDIO_DURATION = 5   # seconds

# Model settings
MODEL_NAME = "microsoft/deberta-v3-base"
NUM_LABELS = 11  # Scores: 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5
MAX_LENGTH = 512
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
NUM_EPOCHS = 20
WARMUP_RATIO = 0.1

# Whisper settings
WHISPER_MODEL = "base"
WHISPER_DEVICE = "cuda" if os.environ.get("USE_CUDA", "false").lower() == "true" else "cpu"
WHISPER_COMPUTE_TYPE = "float32"

# API settings
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
CORS_ORIGINS = ["*"]

# MongoDB settings
MONGO_URI = os.environ.get("MONGO_URI", "")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "grammar_scoring")

# SMTP settings (currently unused)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:8000")

# Score mapping
SCORE_TO_LABEL = {score: idx for idx, score in enumerate([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])}
LABEL_TO_SCORE = {idx: score for score, idx in SCORE_TO_LABEL.items()}
