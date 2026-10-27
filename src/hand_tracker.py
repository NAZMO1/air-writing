import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandTracker:
    def __init__(self, model_path="data/hand_landmarker.task", max_hands=1):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.results = None

    def find_hand(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.results = self.detector.detect(mp_image)
        return self.results

    def get_landmarks(self, frame):
        landmarks = []
        h, w, _ = frame.shape
        if self.results and self.results.hand_landmarks:
            for hand_lms in self.results.hand_landmarks:
                for lm in hand_lms:
                    landmarks.append((int(lm.x * w), int(lm.y * h)))
        return landmarks

    def get_fingers_up(self, landmarks):
        if not landmarks:
            return [False] * 5

        fingers = []
        # Pouce (axe X : main face caméra)
        fingers.append(landmarks[4][0] > landmarks[3][0])

        # Index (8), Majeur (12), Annulaire (16), Auriculaire (20)
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for tip, pip in zip(tips, pips):
            fingers.append(landmarks[tip][1] < landmarks[pip][1])

        return fingers