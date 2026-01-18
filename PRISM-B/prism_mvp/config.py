"""
PRISM Configuration
===================
Centralized configuration for API keys and settings.

API keys are loaded from environment variables for security.
Create a .env file in the project root with your keys.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# ============== API KEYS ==============
# Groq API (Script Generation + Fallback Code Gen)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini API (Primary Code Generation)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Available: gemini-2.0-flash, gemini-2.0-flash-lite, gemini-2.5-flash

# ============== PATHS ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
MEDIA_DIR = os.path.join(SCRIPT_DIR, "media")
MUSIC_DIR = os.path.join(MEDIA_DIR, "music")
DB_PATH = os.path.join(BASE_DIR, "vector_db")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")
GENERATED_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "generated_scene.py")

# ============== RENDERING ==============
RENDER_QUALITY = "l"  # l=480p (fast), m=720p (default), h=1080p
QUALITY_PRESETS = {
    "l": ("480p15", 15),
    "m": ("720p30", 30),
    "h": ("1080p60", 60),
}

# ============== AUDIO ==============
BGM_ENABLED = False  # Disable background music for clearer educational content
BGM_VOLUME = 0.0  # Background music volume (disabled)
AUDIO_BUFFER = 0.5  # Extra time after each segment for clarity
MAX_WORKERS = 8  # Parallel audio generation workers

# ============== RAG ==============
COLLECTION_NAME = "prism_codebase"
DEFAULT_N_RESULTS = 3

# ============== BGM URLs ==============
BGM_URLS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3",
]
