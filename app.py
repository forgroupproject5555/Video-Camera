from flask import Flask, render_template, Response, jsonify, request
import cv2
from ultralytics import YOLO
from Adafruit_IO import Client, RequestError
import mediapipe as mp
import time
import sys
import os
import json
import datetime
import math
import threading

app = Flask(__name__)

# --- 1. ADAFRUIT SETUP ---
# ▼▼▼ PASTE YOUR KEYS HERE ▼▼▼
AIO_USERNAME = "groupproject5555"
AIO_KEY = "aio_PHxo83cpnPXG4vmGlN62BKdmNu4O"
# ▼▼▼ ----------------- ▼▼▼

try:
    aio = Client(AIO_USERNAME, AIO_KEY)
    print("✅ Connected to Adafruit IO.")
except Exception as e:
    print(f"❌ Failed to connect to Adafruit IO: {e}")

# Feeds
FEED_STATUS = "devicestatus"
FEED_PERCENT_STUDY = "time-studying"
FEED_PERCENT_PHONE = "time-phone"
FEED_PERCENT_DESK = "time-desk"
FEED_PERCENT_SLOUCH = "time-slouching"
FEED_PERCENT_DISTRACTED = "time-distracted"

# --- 2. CONFIG & VARIABLES ---
# Robust Model Loading
try:
    model = YOLO("yolo11n.pt", task="detect")
except Exception as e:
    print(f"⚠️ Model load error: {e}. Attempting re-download.")
    if os.path.exists("yolo11n.pt"): os.remove("yolo11n.pt")
    model = YOLO("yolo11n.pt", task="detect")

# --- MEDIAPIPE SETUP ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5)

# ⚠️ CALIBRATION
SLOUCH_THRESHOLD = 0.15 
GAZE_THRESHOLD_LEFT = 0.40  
GAZE_THRESHOLD_RIGHT = 0.60 

LOG_FOLDER = "logs"
SAVE_FILE = "current_session_save.json"
CURRENT_LOG_FILE = "current_log.csv"

if not os.path.exists(LOG_FOLDER): os.makedirs(LOG_FOLDER)

# Default Stats
default_stats = {
    "status": "Idle",
    "study_time": 0.0,
    "phone_time": 0.0,
    "desk_time": 0.0,
    "slouch_time": 0.0,
    "distracted_time": 0.0,
    "away_time": 0.0,
    "hands_detected": False 
}
stats = default_stats.copy()
is_running = False

# --- 3. HELPER FUNCTIONS ---
def save_state_to_json():
    try:
        with open(SAVE_FILE, 'w') as f: json.dump(stats, f)
    except Exception as e: print(f"⚠️ Save failed: {e}")

def load_previous_state():
    global stats
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                loaded_data = json.load(f)
            stats = default_stats.copy()
            stats.update(loaded_data)
            print(f"📂 Loaded previous session data: {stats}")
        except Exception as e:
            stats = default_stats.copy()
    else:
        stats = default_stats.copy()

def log_to_csv(status):
    filepath = os.path.join(LOG_FOLDER, CURRENT_LOG_FILE)
    need_header = not os.path.exists(filepath)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(filepath, 'a') as f:
            if need_header: 
                f.write("Timestamp,Status,Study,Phone,Desk,Slouch,Distracted\n")
            f.write(f"{now},{status},{int(stats['study_time'])},{int(stats['phone_time'])},{int(stats['desk_time'])},{int(stats['slouch_time'])},{int(stats['distracted_time'])}\n")
    except Exception as e: print(f"⚠️ Log error: {e}")

def archive_old_session():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    old_log = os.path.join(LOG_FOLDER, CURRENT_LOG_FILE)
    if os.path.exists(old_log):
        try: os.rename(old_log, os.path.join(LOG_FOLDER, f"archive_log_{timestamp}.csv"))
        except OSError: pass
    if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)

def get_gaze_ratio(eye_points, landmarks):
    left_corner = landmarks[eye_points[0]]
    right_corner = landmarks[eye_points[1]]
    iris_center = landmarks[eye_points[2]]
    eye_width = math.hypot(right_corner.x - left_corner.x, right_corner.y - left_corner.y)
    dist_to_left = math.hypot(iris_center.x - left_corner.x, iris_center.y - left_corner.y)
    if eye_width == 0: return 0.5
    return dist_to_left / eye_width

# --- 4. THREADED CAMERA CLASS ---
class CameraStream:
    def __init__(self):
        self.stream = cv2.VideoCapture(0)
        if not self.stream.isOpened(): self.stream = cv2.VideoCapture(1)
        
        # Optimize camera settings
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# Global camera instance
camera_stream = None

# --- 5. PROCESSING LOOP ---
def generate_frames():
    global is_running, stats, camera_stream
    
    if camera_stream is None:
        camera_stream = CameraStream().start()
        time.sleep(2.0)

    last_sent_status_time = 0
    last_sent_stats_time = 0
    last_autosave_time = 0
    
    frame_count = 0
    SKIP_FRAMES = 3 
    last_loop_time = time.time()
    
    cached_results_yolo = None
    cached_results_pose = None
    cached_results_face = None
    cached_results_hands = None
    
    gaze_score = 0.5
    vertical_dist = 0.2
    is_slouching = False
    is_looking_away = False
    hand_action = "None"
    
    current_status = stats["status"]
    previous_status = stats["status"]

    while True:
        frame = camera_stream.read()
        if frame is None: break
        
        display_frame = cv2.resize(frame, (640, 480))
        
        if is_running:
            current_time = time.time()
            dt = current_time - last_loop_time
            last_loop_time = current_time
            frame_count += 1
            
            # --- AI PROCESSING ---
            if frame_count % (SKIP_FRAMES + 1) == 0:
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                
                cached_results_pose = pose.process(frame_rgb)
                cached_results_face = face_mesh.process(frame_rgb)
                cached_results_hands = hands.process(frame_rgb) 
                
                try:
                    cached_results_yolo = model(display_frame, verbose=False)
                    detected_names = [model.names[int(cls)] for cls in cached_results_yolo[0].boxes.cls]
                except:
                    detected_names = []
                    cached_results_yolo = None
                
                # --- LOGIC ---
                is_slouching = False
                if cached_results_pose.pose_landmarks:
                    lm = cached_results_pose.pose_landmarks.landmark
                    nose_y = lm[mp_pose.PoseLandmark.NOSE.value].y
                    shoulder_y = (lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y + lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2
                    vertical_dist = shoulder_y - nose_y
                    if vertical_dist < SLOUCH_THRESHOLD: is_slouching = True

                is_looking_away = False
                if cached_results_face.multi_face_landmarks:
                    mesh_points = cached_results_face.multi_face_landmarks[0].landmark
                    gaze_r = get_gaze_ratio([33, 133, 468], mesh_points)
                    gaze_l = get_gaze_ratio([362, 263, 473], mesh_points)
                    gaze_score = (gaze_r + gaze_l) / 2
                    if gaze_score < GAZE_THRESHOLD_LEFT or gaze_score > GAZE_THRESHOLD_RIGHT: is_looking_away = True

                hands_visible = False
                hand_action = "None"
                if cached_results_hands.multi_hand_landmarks:
                    hands_visible = True
                    for hand_landmarks in cached_results_hands.multi_hand_landmarks:
                        lm = hand_landmarks.landmark
                        thumb_tip = lm[mp_hands.HandLandmark.THUMB_TIP]
                        index_tip = lm[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                        
                        if pinch_dist < 0.04: 
                            hand_action = "Writing"
                            break 
                        
                        wrist = lm[mp_hands.HandLandmark.WRIST]
                        index_mcp = lm[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                        pinky_mcp = lm[mp_hands.HandLandmark.PINKY_MCP]
                        index_tip = lm[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        middle_tip = lm[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                        
                        if wrist.y > 0.4:
                            if index_mcp.y < wrist.y and pinky_mcp.y < wrist.y:
                                if index_tip.y > index_mcp.y and middle_tip.y > lm[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y:
                                    hand_action = "Typing"
                stats["hands_detected"] = hands_visible

                found_person = "person" in detected_names
                found_phone = "cell phone" in detected_names
                found_study_obj = any(x in detected_names for x in ["book", "laptop", "keyboard", "mouse"])

                # --- FINAL STATUS DECISION (Priority Order) ---
                # Priority 1: Phone (Always Bad) - Overrides everything
                if found_phone:
                    current_status = "On Phone"
                
                # Priority 2: Distracted (Looking Away or Slouching) - Overrides Studying!
                # If you are writing but looking at the ceiling, you are distracted.
                elif is_looking_away or is_slouching:
                     # Looking away OR Slouching = Distracted
                    current_status = "Distracted"
                
                # Priority 3: Studying (Action or Object)
                # Only if NOT looking away and NOT slouching
                elif hand_action in ["Writing", "Typing"] or found_study_obj:
                    current_status = "Studying"
                
                # Priority 4: At Desk but doing nothing (Also Distracted/Idle)
                elif found_person:
                    current_status = "Distracted"
                
                else:
                    current_status = "Away"
                
                stats["status"] = current_status

            # --- TIME ACCUMULATION ---
            current_status = stats["status"]
            if current_status == "On Phone": stats["phone_time"] += dt
            elif current_status == "Studying": stats["study_time"] += dt
            elif current_status == "Distracted": 
                stats["distracted_time"] += dt
                stats["desk_time"] += dt
            elif current_status == "Slouching": 
                stats["slouch_time"] += dt
                stats["distracted_time"] += dt # Slouching counts as distracted time in consolidation
            elif current_status == "At Desk": stats["desk_time"] += dt
            elif current_status == "Away": stats["away_time"] += dt

            # Logging
            if current_status != previous_status:
                log_to_csv(current_status)
                previous_status = current_status

            if current_time - last_autosave_time > 5.0:
                save_state_to_json()
                last_autosave_time = current_time

            # Upload
            try:
                if (current_time - last_sent_status_time > 3.0):
                    aio.send(FEED_STATUS, current_status)
                    last_sent_status_time = current_time
                
                if (current_time - last_sent_stats_time > 30.0):
                    total = stats["study_time"] + stats["phone_time"] + stats["distracted_time"]
                    if total > 0:
                        aio.send(FEED_PERCENT_STUDY, int((stats["study_time"]/total)*100))
                        aio.send(FEED_PERCENT_PHONE, int((stats["phone_time"]/total)*100))
                        aio.send(FEED_PERCENT_DISTRACTED, int((stats["distracted_time"]/total)*100))
                    last_sent_stats_time = current_time
            except: pass

            # --- DRAWING ---
            if cached_results_yolo:
                try: display_frame = cached_results_yolo[0].plot(img=display_frame)
                except: pass
                
                color = (0, 255, 0)
                if current_status == "On Phone": color = (0, 0, 255)
                elif current_status == "Distracted": color = (0, 165, 255)
                
                cv2.putText(display_frame, f"Status: {current_status}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                if current_status == "Distracted":
                    reason = ""
                    if is_slouching: reason = "Slouching"
                    elif is_looking_away: reason = "Looking Away"
                    else: reason = "Idle"
                    cv2.putText(display_frame, f"Reason: {reason}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
                if cached_results_hands.multi_hand_landmarks:
                    for hl in cached_results_hands.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(display_frame, hl, mp_hands.HAND_CONNECTIONS)
                    if hand_action != "None":
                        cv2.putText(display_frame, f"Action: {hand_action}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                # Draw Gaze Points (Face) - INDEPENDENT DRAWING
                if cached_results_face and cached_results_face.multi_face_landmarks:
                    mesh = cached_results_face.multi_face_landmarks[0].landmark
                    eye_color = (0, 0, 255) if is_looking_away else (0, 255, 0)
                    
                    h, w, _ = display_frame.shape
                    
                    # Draw Left Iris (473)
                    cx_l = int(mesh[473].x * w); cy_l = int(mesh[473].y * h)
                    cv2.circle(display_frame, (cx_l, cy_l), 4, eye_color, -1)
                    cv2.circle(display_frame, (cx_l, cy_l), 6, (255, 255, 255), 1) # White border
                    
                    # Draw Right Iris (468)
                    cx_r = int(mesh[468].x * w); cy_r = int(mesh[468].y * h)
                    cv2.circle(display_frame, (cx_r, cy_r), 4, eye_color, -1)
                    cv2.circle(display_frame, (cx_r, cy_r), 6, (255, 255, 255), 1) # White border
                    
                    # Draw Gaze Text
                    cv2.putText(display_frame, f"Gaze Score: {gaze_score:.2f}", (w - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)

                # Draw Slouch Line (Pose) - INDEPENDENT DRAWING
                if cached_results_pose and cached_results_pose.pose_landmarks:
                     lm = cached_results_pose.pose_landmarks.landmark
                     if (lm[mp_pose.PoseLandmark.NOSE.value].visibility > 0.5):
                        h, w, _ = display_frame.shape
                        nose_pt = (int(lm[mp_pose.PoseLandmark.NOSE.value].x * w), int(lm[mp_pose.PoseLandmark.NOSE.value].y * h))
                        sh_y = int((lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y + lm[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2 * h)
                        l_color = (0, 0, 255) if is_slouching else (0, 255, 0)
                        cv2.line(display_frame, nose_pt, (nose_pt[0], sh_y), l_color, 4)
                        cv2.putText(display_frame, f"Posture: {vertical_dist:.2f}", (nose_pt[0] + 10, nose_pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, l_color, 2)

        try:
            ret, buffer = cv2.imencode('.jpg', display_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except: pass

# --- WEB ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/video_feed')
def video_feed(): return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/continue_session', methods=['POST'])
def continue_session():
    global is_running
    load_previous_state()
    is_running = True
    log_to_csv("SESSION RESUMED")
    return jsonify({"message": "Resumed"})

@app.route('/new_session', methods=['POST'])
def new_session():
    global is_running, stats
    archive_old_session()
    stats = default_stats.copy()
    is_running = True
    save_state_to_json()
    log_to_csv("NEW SESSION STARTED")
    return jsonify({"message": "New Session"})

@app.route('/stop_session', methods=['POST'])
def stop_session():
    global is_running
    is_running = False
    save_state_to_json()
    log_to_csv("SESSION PAUSED")
    return jsonify({"message": "Stopped"})

@app.route('/get_stats')
def get_stats(): return jsonify(stats)

if __name__ == '__main__':
    try: app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    finally: 
        if camera_stream: camera_stream.stop()