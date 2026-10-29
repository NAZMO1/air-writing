from pathlib import Path
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from src.gestures import fingers_up


class HandTracker:
    def __init__(self, model_path=None, max_hands=1):
        if model_path is None:
            model_path = Path(__file__).resolve().parents[1] / 'data/hand_landmarker.task'
        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None
        self.timestamp_ms = -1

    def find_hand(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.timestamp_ms = max(self.timestamp_ms+1, time.monotonic_ns()//1_000_000)
        self.results = self.detector.detect_for_video(image, self.timestamp_ms)
        return self.results

    def get_landmarks(self, frame):
        h, w = frame.shape[:2]
        if self.results and self.results.hand_landmarks:
            return [(max(0, min(w-1, round(lm.x*w))), max(0, min(h-1, round(lm.y*h))))
                    for lm in self.results.hand_landmarks[0]]
        return []

    def get_fingers_up(self, landmarks):
        return fingers_up(landmarks)

    def close(self):
        self.detector.close()
