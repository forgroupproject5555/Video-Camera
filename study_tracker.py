import cv2
from ultralytics import YOLO
from Adafruit_IO import Client, RequestError
import sys
import time

# --- 1. ADAFRUIT IO SETUP ---
# ▼▼▼ PASTE YOUR KEY HERE ▼▼▼
AIO_USERNAME = "groupproject5555"
AIO_KEY = "aio_yJPh16jIXSVawbRxwtmFN7cntNKr"
# ▼▼▼ ----------------- ▼▼▼

try:
    aio = Client(AIO_USERNAME, AIO_KEY)
    FEED_STATUS = "devicestatus"
    FEED_PERCENT_STUDY = "time-studying"
    FEED_PERCENT_PHONE = "time-phone"
    FEED_PERCENT_DESK = "time-desk"
    FEED_AVG_STUDY = "avg-study-rate"
    FEED_AVG_PHONE = "avg-phone-rate"
    FEED_AVG_DESK = "avg-desk-rate"
except RequestError:
    print("❌ Failed to connect to Adafruit IO.")
    sys.exit()
print("✅ Connected to Adafruit IO.")

# --- 2. YOLO and WEBCAM SETUP ---
try:
    model = YOLO("yolo11n.pt") 
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION) 
    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")
        sys.exit()
    print("✅ Webcam opened. Starting tracker...")
except Exception as e:
    print(f"❌ Error setting up: {e}")
    sys.exit()

# --- 3. VARIABLES ---
seconds_studying = 0
seconds_phone = 0
seconds_desk = 0
seconds_away = 0

last_sent_status_time = 0
last_sent_stats_time = 0
last_detection_time = 0
last_sent_status_val = ""

# CONFIGURATION
DETECTION_INTERVAL = 1.0   
STATS_UPLOAD_INTERVAL = 30 # Back to 30 seconds (Faster updates)
STATUS_COOLDOWN = 3.0      # Keep cooldown to prevent flickering

print("👉 Press 'q' in the video window to quit.")

# --- 4. MAIN LOOP ---
while True:
    success, frame = cap.read()
    if not success:
        break

    current_time = time.time()

    # ▼▼▼ RUN DETECTION EVERY 1 SECOND ▼▼▼
    if current_time - last_detection_time >= DETECTION_INTERVAL:
        last_detection_time = current_time
        
        # 1. Run AI
        results = model(frame, verbose=False)

        # 2. Check Objects
        detected_names = [model.names[int(cls)] for cls in results[0].boxes.cls]
        
        found_person = "person" in detected_names
        found_phone = "cell phone" in detected_names
        
        is_studying_object = False
        if "book" in detected_names: is_studying_object = True
        if "laptop" in detected_names: is_studying_object = True
        if "keyboard" in detected_names: is_studying_object = True
        if "mouse" in detected_names: is_studying_object = True

        # 3. Determine Status
        current_status = "Away"

        if found_person:
            if found_phone:
                current_status = "On Phone"
                seconds_phone += DETECTION_INTERVAL
            elif is_studying_object:
                current_status = "Studying"
                seconds_studying += DETECTION_INTERVAL
            else:
                current_status = "At Desk"
                seconds_desk += DETECTION_INTERVAL
        else:
            seconds_away += DETECTION_INTERVAL

        # 4. SEND STATUS (With Cooldown)
        if (current_status != last_sent_status_val) and (current_time - last_sent_status_time > STATUS_COOLDOWN):
            print(f"--- Status Changed: {current_status} ---")
            try:
                aio.send(FEED_STATUS, current_status)
                last_sent_status_val = current_status
                last_sent_status_time = current_time 
            except Exception as e:
                print(f"⚠️ Status Upload Skipped: {e}")

        # 5. SEND STATS (Every 30 seconds)
        if current_time - last_sent_stats_time > STATS_UPLOAD_INTERVAL:
            print("\n--- 📊 UPLOADING STATS ---")
            
            total_time = seconds_studying + seconds_phone + seconds_desk + seconds_away
            if total_time == 0: total_time = 1 
            
            # Calculations
            rate_study = (seconds_studying / total_time) * 60
            rate_phone = (seconds_phone / total_time) * 60
            rate_desk = (seconds_desk / total_time) * 60

            pct_study = (seconds_studying / total_time) * 100
            pct_phone = (seconds_phone / total_time) * 100
            pct_desk = (seconds_desk / total_time) * 100
            
            print(f"Rates (m/hr): Study={int(rate_study)} | Phone={int(rate_phone)} | Desk={int(rate_desk)}")

            try:
                # We add sleeps to prevent "Burst" throttling
                aio.send(FEED_AVG_STUDY, int(rate_study))
                time.sleep(0.5) 
                aio.send(FEED_AVG_PHONE, int(rate_phone))
                time.sleep(0.5)
                aio.send(FEED_AVG_DESK, int(rate_desk))
                time.sleep(0.5)
                
                aio.send(FEED_PERCENT_STUDY, int(pct_study))
                time.sleep(0.5)
                aio.send(FEED_PERCENT_PHONE, int(pct_phone))
                time.sleep(0.5)
                aio.send(FEED_PERCENT_DESK, int(pct_desk))
                
                print("✅ Stats sent successfully.")
                last_sent_stats_time = current_time
            except Exception as e:
                print(f"⚠️ Stats Upload Skipped: {e}")

        annotated_frame = results[0].plot() 
        cv2.imshow("YOLOv8 Study Tracker", annotated_frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Tracker stopped.")