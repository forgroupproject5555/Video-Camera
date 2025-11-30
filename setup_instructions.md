Hey team, here is exactly how to get the Computer Vision (Python) code running on your laptop.

**Prerequisites:**

  * You must have **VS Code** installed.
  * You must have **Python** installed.

-----

## 🚀 Phase 1: Get the Code

1.  Open **VS Code**.
2.  Open our project folder.
3.  Open the Terminal (`Ctrl + ~` or `View > Terminal`).
4.  Run this command to download the latest changes (including the new YOLO11 model updates):
    ```bash
    git pull
    ```

-----

## 📦 Phase 2: Create Your Sandbox (Virtual Environment)

We need a "virtual environment" to install our libraries so we don't break our laptops. You only need to do this **once**.

### **For Mac Users:**

Run these two commands in the terminal:

```bash
python3 -m venv venv
source venv/bin/activate
```

### **For Windows Users:**

Run these two commands:

```bash
python -m venv venv
venv\Scripts\activate
```

### **✅ Check if it worked:**

Look at the start of your terminal line. You should see `(venv)` in parentheses.

  * If you see `(venv)`, you are good\!
  * If you don't, ask Brendon for help.

-----

## 📥 Phase 3: Install the Ingredients

We need to install the AI (YOLO), the Camera tool (OpenCV), and the Cloud tool (Adafruit IO). I created a list so you don't have to guess.

**Make sure you see `(venv)`**, then run this exact command:

```bash
pip install -r requirements.txt
```

*Note: This might take 1-2 minutes to download everything.*

-----

## 🔑 Phase 4: The Keys

The code needs to talk to our shared Adafruit IO dashboard.

1.  Open the file **`study_tracker.py`**.
2.  Look at the top for `AIO_USERNAME` and `AIO_KEY`.
3.  **If those are empty or say "PASTE KEY HERE":**
      * Ask Brendon for the keys (or check our group chat).
      * Paste them inside the quotation marks `" "`.
      * **DO NOT** commit the keys back to GitHub if you can avoid it (security risk), but for now just get it working.

-----

## 🎥 Phase 5: Run the Tracker\!

With your environment active (`(venv)` is showing), run the script:

**Mac:**

```bash
python3 study_tracker.py
```

**Windows:**

```bash
python study_tracker.py
```

-----

## ⚠️ Troubleshooting (If it crashes)

**Problem: "Externally managed environment" error**

  * **Fix:** You forgot to activate your sandbox. Run `source venv/bin/activate` (Mac) or `venv\Scripts\activate` (Windows) again.

**Problem: "Camera not authorized" (Mac only)**

  * **Fix:**
    1.  Go to **System Settings \> Privacy & Security \> Camera**.
    2.  Find **VS Code** in the list and turn the toggle **ON**.
    3.  **Restart VS Code completely** (Quit and Re-open).

**Problem: "Webcam frame read failed"**

  * **Fix:** Make sure no other apps are using the camera (Zoom, FaceTime, etc.). If it still fails, restart your computer.

**Problem: "Module not found: ultralytics"**

  * **Fix:** You didn't run the install command. Go back to Phase 3 and run `pip install -r requirements.txt`.