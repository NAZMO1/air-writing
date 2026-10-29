import unittest
import math
import numpy as np
import cv2
from src.gestures import StrokeTracker, fingers_up
from src.preprocessing import normalize_letter
from src.classifier import LetterClassifier
from train_model import generate_augmented_dataset


class PipelineTests(unittest.TestCase):
    def test_thin_letter_and_empty_canvas(self):
        image = np.zeros((100,100),np.uint8)
        self.assertIsNone(normalize_letter(image))
        cv2.line(image,(50,10),(50,90),255,2)
        features = normalize_letter(image,20)
        self.assertEqual(features.shape,(784,))
        self.assertGreater(features.sum(),0)
        self.assertLessEqual(features.max(),1)

    def test_translation_invariance(self):
        a = np.zeros((120,120),np.uint8)
        b = a.copy()
        cv2.putText(a,'A',(10,70),cv2.FONT_HERSHEY_SIMPLEX,2,255,3)
        cv2.putText(b,'A',(40,90),cv2.FONT_HERSHEY_SIMPLEX,2,255,3)
        np.testing.assert_allclose(normalize_letter(a),normalize_letter(b))

    def test_pen_lift_and_jump_do_not_bridge(self):
        pen = StrokeTracker()
        self.assertIsNone(pen.update((20,20),True,0,(640,480)))
        self.assertIsNotNone(pen.update((30,20),True,.1,(640,480)))
        self.assertIsNone(pen.update(None,False,.15,(640,480)))
        self.assertIsNone(pen.update((50,20),True,.2,(640,480)))
        self.assertIsNone(pen.update((500,400),True,.3,(640,480)))
        pen.reset()
        self.assertIsNone(pen.previous)

    def test_finger_geometry_rotation_and_mirror(self):
        points = [(0,0)]*21
        for base,x in zip((5,9,13,17),(-3,-1,1,3)):
            points[base:base+4] = [(x,3),(x,5),(x,7),(x,9)]
        self.assertTrue(all(fingers_up(points)[1:]))
        for theta in (0, .8, math.pi):
            transformed = [(-x*math.cos(theta)-y*math.sin(theta),-x*math.sin(theta)+y*math.cos(theta)) for x,y in points]
            self.assertEqual(fingers_up(points), fingers_up(transformed))
        for base,x in zip((5,9,13,17),(-3,-1,1,3)):
            points[base:base+4] = [(x,3),(x,5),(x+1,4),(x+1,3)]
        self.assertFalse(any(fingers_up(points)[1:]))

    def test_ambiguous_prediction_rejected(self):
        class Model:
            classes_ = np.array([1,2])
            def predict_proba(self, data):
                return np.array([[.53,.47]])
        clf = LetterClassifier.__new__(LetterClassifier)
        clf.model = Model()
        clf.min_confidence, clf.min_margin = .6,.15
        canvas = np.zeros((100,100),np.uint8)
        cv2.line(canvas,(10,10),(80,80),255,3)
        self.assertEqual(clf.predict(canvas),'')

    def test_training_data_all_classes_and_reproducible(self):
        x,y = generate_augmented_dataset(2)
        xx,yy = generate_augmented_dataset(2)
        self.assertEqual(x.shape,(52,784))
        self.assertEqual(len(set(y)),26)
        np.testing.assert_array_equal(x,xx)
        np.testing.assert_array_equal(y,yy)


if __name__ == '__main__':
    unittest.main()
