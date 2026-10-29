"""Same normalization for training and inference: white ink on black."""
import cv2
import numpy as np


def normalize_letter(image, min_extent=8):
    points = cv2.findNonZero(np.asarray(image, dtype=np.uint8))
    if points is None:
        return None
    x, y, w, h = cv2.boundingRect(points)
    if max(w, h) < min_extent:  # Preserve thin letters such as I.
        return None
    scale = 20 / max(w, h)
    nw, nh = max(1, round(w*scale)), max(1, round(h*scale))
    roi = cv2.resize(image[y:y+h, x:x+w], (nw, nh), interpolation=cv2.INTER_AREA)
    padded = np.zeros((28, 28), dtype=np.uint8)
    px, py = (28-nw)//2, (28-nh)//2
    padded[py:py+nh, px:px+nw] = roi
    return cv2.GaussianBlur(padded, (3, 3), 0).astype(np.float32).reshape(-1)/255
