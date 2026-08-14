from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "detections.db"

for folder in (UPLOAD_DIR, OUTPUT_DIR, DB_DIR):
    folder.mkdir(parents=True, exist_ok=True)

MODEL_NAME = os.getenv("YOLO_MODEL", "yolo11n.pt")
CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.35"))
IOU = float(os.getenv("YOLO_IOU", "0.50"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "100"))
CROWD_THRESHOLD = int(os.getenv("CROWD_THRESHOLD", "20"))
LINE_POSITION = float(os.getenv("COUNT_LINE_POSITION", "0.50"))
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "10"))
CAMERA_FPS_LIMIT = int(os.getenv("CAMERA_FPS_LIMIT", "30"))
