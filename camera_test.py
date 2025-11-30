import cv2
import sys

def test_camera(index):
    print(f"\n--- Testing camera at index {index} ---")
    
    # Try to open the camera using the native AVFoundation backend
    # This is the most important change
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open camera at index {index}.")
        return

    print(f"✅ Camera {index} opened. Trying to read a frame...")

    # Try to read one frame
    success, frame = cap.read()

    if not success:
        print(f"❌ Error: Could not read a frame from camera {index}.")
    else:
        print(f"✅ Success! Read one frame from camera {index}.")
        print("👉 A window should pop up. Press 'q' in that window to quit.")
        
        # Show the frame in a window
        while True:
            # Continuously read and show frames
            success, frame = cap.read()
            if not success:
                print("Lost connection to camera.")
                break
                
            cv2.imshow(f"Camera Test (Index {index}) - Press 'q' to quit", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    print(f"--- Test for index {index} finished ---")

# --- Run the Test ---
# We will test both index 0 (usually built-in) and index 1 (sometimes built-in)
test_camera(0)
test_camera(1)

print("\nAll camera tests complete.")