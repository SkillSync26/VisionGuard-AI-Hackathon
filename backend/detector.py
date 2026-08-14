import threading
import time
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

from .config import MODEL_NAME, CONFIDENCE, IOU, LINE_POSITION, CROWD_THRESHOLD
from .database import add_detection, add_alert

class ObjectDetector:
    def __init__(self):
        self.model = YOLO(MODEL_NAME)
        self.lock = threading.Lock()
        self.last_alert_time = {}
        self.count_state = {}

    def _alert(self, key, message, source):
        now = time.time()
        last = self.last_alert_time.get(key, 0)
        if now - last >= 10:
            add_alert(key, message, "warning")
            self.last_alert_time[key] = now

    def process_frame(self, frame, source="webcam", tracking=True,
                      save_db=False, line_count=True):
        start = time.perf_counter()

        with self.lock:
            if tracking:
                result = self.model.track(
                    frame, persist=True, conf=CONFIDENCE, iou=IOU,
                    verbose=False
                )[0]
            else:
                result = self.model(
                    frame, conf=CONFIDENCE, iou=IOU, verbose=False
                )[0]

        annotated = result.plot()
        names = self.model.names
        detections = []
        centers = []

        boxes = result.boxes
        if boxes is not None:
            xyxy = boxes.xyxy.cpu().numpy() if boxes.xyxy is not None else []
            confs = boxes.conf.cpu().numpy() if boxes.conf is not None else []
            classes = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else []
            ids = (
                boxes.id.cpu().numpy().astype(int)
                if boxes.id is not None else [None] * len(classes)
            )

            for i, cls_id in enumerate(classes):
                x1, y1, x2, y2 = map(int, xyxy[i])
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                class_name = str(names[int(cls_id)])
                confidence = float(confs[i])
                track_id = int(ids[i]) if ids[i] is not None else None

                detections.append({
                    "class": class_name,
                    "confidence": round(confidence, 4),
                    "track_id": track_id,
                    "bbox": [x1, y1, x2, y2],
                    "center": [cx, cy],
                })
                centers.append((class_name, track_id, cx, cy))

                if save_db:
                    add_detection(
                        class_name, confidence, source,
                        object_count=1, track_id=track_id
                    )

        class_counts = Counter(d["class"] for d in detections)
        people = class_counts.get("person", 0)

        # Crowd alert
        if people > CROWD_THRESHOLD:
            self._alert(
                "crowd_threshold",
                f"Crowd threshold exceeded: {people} people detected.",
                source
            )

        # Draw configurable horizontal counting line.
        line_y = int(frame.shape[0] * LINE_POSITION)
        cv2.line(
            annotated, (0, line_y), (frame.shape[1], line_y),
            (0, 255, 255), 2
        )

        if line_count:
            for class_name, track_id, cx, cy in centers:
                if track_id is None:
                    continue
                key = (source, track_id)
                previous = self.count_state.get(key)
                if previous is not None:
                    old_y = previous
                    if old_y < line_y <= cy:
                        self.count_state[key] = cy
                    elif old_y > line_y >= cy:
                        self.count_state[key] = cy
                else:
                    self.count_state[key] = cy

        fps = 1.0 / max(time.perf_counter() - start, 1e-6)
        avg_conf = (
            sum(d["confidence"] for d in detections) / len(detections)
            if detections else 0.0
        )

        stats = {
            "fps": round(fps, 2),
            "total_objects": len(detections),
            "people": people,
            "average_confidence": round(avg_conf, 4),
            "counts": dict(class_counts),
            "line_y": line_y,
        }
        return annotated, detections, stats

    def process_image(self, image_path, output_path):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError("Could not read image.")
        annotated, detections, stats = self.process_frame(
            frame, source="image", tracking=False, save_db=True, line_count=False
        )
        if not cv2.imwrite(str(output_path), annotated):
            raise IOError("Could not save processed image.")
        return detections, stats

    def process_video(self, input_path, output_path):
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise ValueError("Could not open video.")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        fps_in = cap.get(cv2.CAP_PROP_FPS)
        if not fps_in or fps_in <= 0:
            fps_in = 25.0

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps_in, (width, height))
        if not writer.isOpened():
            cap.release()
            raise IOError("Could not create output video.")

        total_frames = 0
        total_detections = 0
        last_stats = {}

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                annotated, detections, stats = self.process_frame(
                    frame, source="video", tracking=True, save_db=False, line_count=True
                )
                writer.write(annotated)
                total_frames += 1
                total_detections += len(detections)
                last_stats = stats
        finally:
            cap.release()
            writer.release()

        return {
            "frames": total_frames,
            "total_detections": total_detections,
            "last_stats": last_stats,
            "output": str(output_path),
        }

detector = ObjectDetector()
