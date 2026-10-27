import cv2

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# Forcer le format YUYV (format brut standard des webcams PC portables)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Désactiver les buffers pour éviter les trames corrompues en attente
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erreur de lecture")
        break
    
    cv2.imshow("Test Cam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()