import cv2
from ultralytics import YOLO
from Adafruit_IO import Client, RequestError
import sys
import time

# --- 1. ADAFRUIT IO SETUP ---
# ▼▼▼ EDIT THESE! ▼▼▼
AIO_USERNAME = "groupproject5555"
AIO_KEY = "aio_XHYq38adl33ZKs7ejLZYl815pEz7"
# ▼▼▼ ----------------- ▼▼▼

AIO_FEED_KEY = "studystatus"

# --- 2. CONNECT TO ADAFRUIT IO ---
try:
    aio = Client(AIO_USERNAME, AIO_KEY)
except RequestError:
    print("❌ Failed to connect to Adafruit IO. Check username/key.")
    sys.exit()
print("✅ Connected to Adafruit IO.")

# --- 3. YOLO and WEBCAM SETUP ---
try:
    model = YOLO("yolov8n.pt") 
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION) 
    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")
        sys.exit()
    print("✅ Webcam opened. Starting tracker...")
    print("👉 Press 'q' in the video window to quit.")
except Exception as e:
    print(f"❌ Error setting up model or webcam: {e}")
    sys.exit()

last_sent_status = ""
last_sent_time = 0
UPDATE_COOLDOWN = 3 # Send updates every 3 seconds

# --- 4. MAIN LOOP ---
while True:
    success, frame = cap.read()
    if not success:
        print("Webcam frame read failed. Exiting.")
        break

    results = model(frame) # Run AI model

    # --- 5. DETECTION LOGIC ---
    found_person = False
    found_phone = False
    found_book = False
    
    detected_names = [model.names[int(cls)] for cls in results[0].boxes.cls]
    
    if "person" in detected_names: found_person = True
    if "cell phone" in detected_names: found_phone = True
    if "book" in detected_names: found_book = True

    # --- 6. DETERMINE AND SEND STATUS ---
    current_status = "Away"
    if found_person:
        if found_phone:
            current_status = "On Phone"
        elif found_book:
            current_status = "Studying"
        else:
            current_status = "At Desk"
            
    current_time = time.time()
    
    # Only send an update if status has changed or cooldown has passed
    if (current_status != last_sent_status) or (current_time - last_sent_time > UPDATE_COOLDOWN):
        print(f"Current Status: {current_status}")
        try:
            aio.send(AIO_FEED_KEY, current_status)
            last_sent_status = current_status
            last_sent_time = current_time
        except RequestError:
            print("⚠️ Could not send to Adafruit IO. Will retry.")

    # --- 7. DISPLAY (Optional) ---
    annotated_frame = results[0].plot() # Draws boxes
    cv2.imshow("YOLOv8 Study Tracker", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 8. CLEAN UP ---
cap.release()
cv2.destroyAllWindows()
print("Tracker stopped.")