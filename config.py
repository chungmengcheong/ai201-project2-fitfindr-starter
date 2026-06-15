import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
TEMPERATURE_SUGGEST_OUTFT = 1.0
TEMPERATURE_FIT_CARD = 0.7

# --- Data ---
DATA_PATH = "./data"
