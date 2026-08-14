import base64
import os
import time
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    BASE_DIR,
    UPLOAD_DIR,
    OUTPUT_DIR,
    MAX_UPLOAD_MB,
    CONFIDENCE,
    MODEL_NAME,
)
from .database import (
    init_db,
    get_detections,
    get_alerts,
    get_statistics,
    clear_history,
    add_alert,
)
from .detector import detector
from .report import create_csv, create_pdf


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AI Object Detection & Intelligent Monitoring",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


# ============================================================
# SMART ALERT CONFIGURATION
# ============================================================

# Prevent the same alert from being stored repeatedly
# every single frame.
ALERT_COOLDOWN = 10

last_alert_time = {}


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    init_db()


# ============================================================
# HOME
# ============================================================

@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "confidence_threshold": CONFIDENCE,
    }


# ============================================================
# FRONTEND PAGES
# ============================================================

@app.get("/page/{page_name}")
def page(page_name: str):

    allowed = {
        "live": "live.html",
        "image": "image.html",
        "video": "video.html",
        "dashboard": "dashboard.html",
        "history": "history.html",
        "about": "about.html",
    }

    filename = allowed.get(page_name)

    if not filename:
        raise HTTPException(
            status_code=404,
            detail="Page not found",
        )

    return FileResponse(FRONTEND_DIR / filename)


# ============================================================
# FILE UPLOAD
# ============================================================

async def save_upload(upload: UploadFile) -> Path:

    if not upload.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided.",
        )

    suffix = Path(upload.filename).suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
    }

    safe_ext = (
        suffix
        if suffix in allowed_extensions
        else ""
    )

    if not safe_ext:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type.",
        )

    data = await upload.read()

    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {MAX_UPLOAD_MB} MB limit.",
        )

    path = UPLOAD_DIR / f"{uuid4().hex}{safe_ext}"

    path.write_bytes(data)

    return path


# ============================================================
# IMAGE DETECTION
# ============================================================

@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):

    input_path = await save_upload(file)

    output_path = (
        OUTPUT_DIR /
        f"{input_path.stem}_detected.jpg"
    )

    try:

        detections, stats = detector.process_image(
            input_path,
            output_path,
        )

        return {
            "success": True,
            "detections": detections,
            "statistics": stats,
            "download_url": f"/files/{output_path.name}",
        }

    finally:

        input_path.unlink(
            missing_ok=True
        )


# ============================================================
# VIDEO DETECTION
# ============================================================

@app.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):

    input_path = await save_upload(file)

    output_path = (
        OUTPUT_DIR /
        f"{input_path.stem}_detected.mp4"
    )

    try:

        result = detector.process_video(
            input_path,
            output_path,
        )

        return {
            "success": True,
            "result": result,
            "download_url": f"/files/{output_path.name}",
        }

    finally:

        input_path.unlink(
            missing_ok=True
        )


# ============================================================
# OUTPUT FILES
# ============================================================

@app.get("/files/{filename}")
def get_file(filename: str):

    path = OUTPUT_DIR / Path(filename).name

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return FileResponse(path)


# ============================================================
# DETECTION HISTORY
# ============================================================

@app.get("/detections")
def detections(
    limit: int = Query(
        200,
        ge=1,
        le=5000,
    ),
    object_type: str | None = None,
    source: str | None = None,
    date: str | None = None,
):

    return {
        "items": get_detections(
            limit,
            object_type,
            source,
            date,
        )
    }


# ============================================================
# ALERT HISTORY
# ============================================================

@app.get("/alerts")
def alerts(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
    )
):

    return {
        "items": get_alerts(limit)
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/statistics")
def statistics():

    return get_statistics()


# ============================================================
# DELETE HISTORY
# ============================================================

@app.delete("/history")
def delete_history():

    clear_history()

    return {
        "success": True,
        "message": "Detection history deleted.",
    }


# ============================================================
# CSV REPORT
# ============================================================

@app.get("/reports/csv")
def csv_report():

    path = OUTPUT_DIR / "detection_report.csv"

    create_csv(path)

    return FileResponse(
        path,
        filename="detection_report.csv",
        media_type="text/csv",
    )


# ============================================================
# PDF REPORT
# ============================================================

@app.get("/reports/pdf")
def pdf_report():

    path = OUTPUT_DIR / "detection_report.pdf"

    create_pdf(path)

    return FileResponse(
        path,
        filename="detection_report.pdf",
        media_type="application/pdf",
    )


# ============================================================
# SMART ALERT ENGINE
# ============================================================

def generate_alerts(
    detections,
    statistics,
):

    """
    Analyze YOLO detections and generate
    meaningful alerts.

    Alert types:

    1. PHONE_DETECTED
    2. CROWD_DETECTED
    """

    now = time.time()

    alerts = []


    # ========================================================
    # PHONE DETECTION
    # ========================================================

    phone_detections = [
        detection
        for detection in detections
        if detection.get(
            "class",
            ""
        ).lower()
        in {
            "cell phone",
            "phone",
            "mobile phone",
        }
    ]

    if phone_detections:

        confidence = max(
            float(
                detection.get(
                    "confidence",
                    0,
                )
            )
            for detection in phone_detections
        )

        # Check cooldown
        if (
            now -
            last_alert_time.get(
                "phone",
                0,
            )
            >= ALERT_COOLDOWN
        ):

            message = (
                "Cell phone detected "
                f"({confidence * 100:.1f}% confidence)"
            )

            # Save to database
            add_alert(
                "PHONE_DETECTED",
                message,
                "warning",
            )

            last_alert_time["phone"] = now

            alerts.append(
                {
                    "type": "PHONE_DETECTED",
                    "message": message,
                    "severity": "warning",
                }
            )


    # ========================================================
    # CROWD DETECTION
    # ========================================================

    people_count = int(
        statistics.get(
            "people",
            0,
        )
    )

    # Crowd threshold
    if people_count > 20:

        if (
            now -
            last_alert_time.get(
                "crowd",
                0,
            )
            >= ALERT_COOLDOWN
        ):

            message = (
                "Crowd threshold exceeded: "
                f"{people_count} people detected"
            )

            add_alert(
                "CROWD_DETECTED",
                message,
                "critical",
            )

            last_alert_time["crowd"] = now

            alerts.append(
                {
                    "type": "CROWD_DETECTED",
                    "message": message,
                    "severity": "critical",
                }
            )


    return alerts


# ============================================================
# LIVE WEBCAM WEBSOCKET
# ============================================================

@app.websocket("/ws/live")
async def live_detection(
    websocket: WebSocket,
):

    await websocket.accept()

    try:

        while True:

            # ------------------------------------------------
            # Receive webcam frame
            # ------------------------------------------------

            message = (
                await websocket.receive_text()
            )

            if not message.startswith(
                "data:image"
            ):
                continue


            # ------------------------------------------------
            # Decode image
            # ------------------------------------------------

            encoded = message.split(
                ",",
                1,
            )[1]

            raw = base64.b64decode(
                encoded
            )

            array = np.frombuffer(
                raw,
                dtype=np.uint8,
            )

            frame = cv2.imdecode(
                array,
                cv2.IMREAD_COLOR,
            )


            # ------------------------------------------------
            # Invalid frame
            # ------------------------------------------------

            if frame is None:

                await websocket.send_json(
                    {
                        "error":
                        "Invalid image frame."
                    }
                )

                continue


            # ------------------------------------------------
            # YOLO DETECTION
            # ------------------------------------------------

            annotated, detections, stats = (
                detector.process_frame(
                    frame,
                    source="webcam",
                    tracking=True,
                    save_db=True,
                    line_count=True,
                )
            )


            # ------------------------------------------------
            # SMART ALERTS
            # ------------------------------------------------

            live_alerts = generate_alerts(
                detections,
                stats,
            )


            # ------------------------------------------------
            # Encode processed frame
            # ------------------------------------------------

            ok, buffer = cv2.imencode(
                ".jpg",
                annotated,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    82,
                ],
            )

            if not ok:
                continue


            encoded_out = (
                base64.b64encode(
                    buffer
                ).decode("ascii")
            )


            # ------------------------------------------------
            # Send result to browser
            # ------------------------------------------------

            await websocket.send_json(
                {
                    "image":
                        f"data:image/jpeg;base64,{encoded_out}",

                    "detections":
                        detections,

                    "statistics":
                        stats,

                    "alerts":
                        live_alerts,
                }
            )


    except WebSocketDisconnect:

        pass


    except Exception as exc:

        try:

            await websocket.send_json(
                {
                    "error": str(exc)
                }
            )

        except Exception:

            pass

        try:

            await websocket.close()

        except Exception:

            pass