"""Application settings loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
MOCK_DATA_DIR = BASE_DIR / "mock_data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
MOCK_DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
(LOGS_DIR / "emails").mkdir(exist_ok=True)
(LOGS_DIR / "calls").mkdir(exist_ok=True)
(LOGS_DIR / "alerts").mkdir(exist_ok=True)

# API Keys (real)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "renewai-project")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")

# Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Mock tuning
MOCK_PAYMENT_SUCCESS_RATE = float(os.getenv("MOCK_PAYMENT_SUCCESS_RATE", "0.35"))
MOCK_EMAIL_OPEN_RATE = float(os.getenv("MOCK_EMAIL_OPEN_RATE", "0.42"))
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
