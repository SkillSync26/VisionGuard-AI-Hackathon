# VisionGuard AI — Object Detection & Intelligent Monitoring

A real YOLO + OpenCV + FastAPI + SQLite hackathon project.

## Features

- Live browser webcam detection through WebSocket
- YOLO object detection
- Object tracking IDs
- Object counting by class
- Crowd threshold alerts
- Image detection and download
- MP4/video processing and download
- SQLite detection history
- Dashboard analytics
- CSV and PDF reports
- CPU fallback and GPU support when PyTorch/Ultralytics detects a supported GPU
- No fake detection data

## Architecture

Camera / Image / Video
→ OpenCV
→ YOLO
→ Tracking
→ Counting
→ Alerts
→ SQLite
→ Analytics
→ Web dashboard

## Windows installation

Install Python 3.11 or 3.12.

Open PowerShell in this project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

http://127.0.0.1:8000

The first YOLO inference downloads the configured pretrained model automatically if it is not already present. Internet is therefore required for the first model download.

## Camera

Use the Live page and click Start Camera. Your browser will ask for camera permission.

The browser sends JPEG frames to `/ws/live`; FastAPI passes each frame to the same loaded YOLO model and returns an annotated JPEG plus JSON statistics.

## API

- GET `/health`
- POST `/detect/image`
- POST `/detect/video`
- GET `/detections`
- GET `/statistics`
- GET `/alerts`
- DELETE `/history`
- GET `/reports/csv`
- GET `/reports/pdf`
- WebSocket `/ws/live`

## Configuration

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Useful settings:

- `YOLO_MODEL=yolo11n.pt`
- `YOLO_CONFIDENCE=0.35`
- `CROWD_THRESHOLD=20`
- `COUNT_LINE_POSITION=0.50`
- `MAX_UPLOAD_MB=100`

## Hackathon demo flow

### 1. Problem — 30 seconds

Continuous manual monitoring is difficult. Operators need quick information about people, vehicles, objects and unusual crowd levels.

### 2. Solution — 45 seconds

Show the pipeline: camera → OpenCV → YOLO → tracking → counting → alerts → database → analytics.

### 3. Live demo — 90 seconds

1. Open Live Detection.
2. Start the webcam.
3. Put people/objects in view.
4. Show bounding boxes and confidence.
5. Show tracking IDs.
6. Show live FPS and class counts.
7. Demonstrate the crowd alert by placing more than the configured threshold of people in view, or lower `CROWD_THRESHOLD` in `.env` for a controlled demo.

### 4. Image/video — 45 seconds

Upload an image and download the processed result. Then process an MP4 and download the annotated output.

### 5. Analytics — 30 seconds

Open Dashboard and show real SQLite-backed detections, alerts, CSV and PDF reports.

### 6. Impact/future — 30 seconds

Explain adaptations for smart classrooms, campuses, traffic, retail and workplace safety.

## What to say to judges

YOLO predicts object classes and bounding boxes in an image. Tracking adds temporal identity so an object can keep an ID across frames. Counting uses tracked object positions and a configurable line. The database turns raw detections into historical analytics.

Do not claim an accuracy percentage unless you have evaluated a specific dataset.

## Testing checklist

- [ ] Backend starts
- [ ] `/health` returns `status: ok`
- [ ] Landing page opens
- [ ] Webcam permission works
- [ ] Bounding boxes appear
- [ ] Confidence values appear
- [ ] Tracking IDs appear when supported
- [ ] Image detection works
- [ ] Video detection works
- [ ] SQLite history updates
- [ ] Dashboard uses real data
- [ ] Alerts are stored
- [ ] CSV report downloads
- [ ] PDF report downloads
- [ ] CPU mode works

## Troubleshooting

### `python` is not recognized

Install Python and make sure "Add Python to PATH" was selected, then reopen PowerShell.

### PowerShell activation error

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Camera does not open

Allow camera permission in the browser. Close other apps using the webcam.

### YOLO model download fails

Run:

```powershell
pip install -U ultralytics
```

Then restart the server with an internet connection.

### CPU is slow

Use the nano model (`yolo11n.pt`), reduce webcam resolution in `live.js`, or use a supported NVIDIA GPU environment.

### Video output cannot be played

OpenCV writes MP4 using `mp4v`. If your browser/player rejects it, test the file in VLC. For production deployment, add an FFmpeg conversion pipeline.

## Privacy

The live webcam stream is processed frame-by-frame and is not intentionally saved as raw video. Detection records are stored in SQLite. Users can delete detection history. No facial recognition or identity recognition is included.
