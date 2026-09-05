from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FRONTEND_DIR = ROOT / "frontend"
SALES_FILE = DATA_DIR / "sales.csv"
PRODUCTS_FILE = DATA_DIR / "products.csv"
STORES_FILE = DATA_DIR / "stores.csv"
DOCS_DIR = DATA_DIR / "documents"
INDEX_FILE = DATA_DIR / "embedding_index.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBED_MODEL = "gemini-embedding-001"
