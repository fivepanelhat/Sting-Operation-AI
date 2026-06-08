# -*- coding: utf-8 -*-
"""Sting Operation AI Colab

Automatically converted from Jupyter Notebook.
"""

"""
# Sting Operation AI: Bee & Wasp Detection (Google Colab)

This notebook mounts your Google Drive, pulls the latest clean and optimized repository from GitHub, configures your Roboflow credentials, and sets up training on Colab's GPU.
"""

"""
### 1. Mount Google Drive
"""

from google.colab import drive
drive.mount('/content/drive')

"""
### 2. Navigate and Sync with GitHub
Navigate to your project directory inside Google Drive. If the project isn't cloned yet, clone it. Otherwise, pull the latest changes we made (class mapping fixes, enhanced scripts, and full dataset).
"""

import os
# Gracefully handle Google Colab and IPython imports when running locally
import sys
import os

try:
    from google.colab import drive, userdata, files
except ImportError:
    class MockDrive:
        def mount(self, *args, **kwargs):
            print("[INFO] Running locally: Google Drive mount bypassed.")
    
    class MockUserdata:
        def get(self, key, default=None):
            return os.environ.get(key, default)
            
    class MockFiles:
        def upload(self):
            print("[INFO] Running locally: File upload bypassed.")
            return {}
            
    sys.modules['google.colab'] = type(sys)('google_colab')
    sys.modules['google.colab'].drive = MockDrive()
    sys.modules['google.colab'].userdata = MockUserdata()
    sys.modules['google.colab'].files = MockFiles()
    from google.colab import drive, userdata, files

try:
    from IPython.display import display, Image
except ImportError:
    def display(*args, **kwargs):
        for arg in args:
            print(arg)
    class Image:
        def __init__(self, filename=None, *args, **kwargs):
            self.filename = filename
        def __repr__(self):
            return f"Image({self.filename})"

project_path = '/content/drive/MyDrive/Sting_Operation_AI'

if not os.path.exists(project_path):
    # Clone the repository if it doesn't exist
    import os; os.chdir(r"/content/drive/MyDrive/") # converted cd magic
    # !git clone https://github.com/fivepanelhat/Sting-Operation-AI.git Sting_Operation_AI # commented shell command
else:
    print("Project directory found. Pulling latest updates...")
    import os; os.chdir(r"{project_path}") # converted cd magic
    # !git pull # commented shell command

"""
### 3. Install Dependencies
Install the required libraries (ultralytics, roboflow, and python-dotenv) inside the Google Colab VM.
"""

import os; os.chdir(r"{project_path}") # converted cd magic
# !pip install ultralytics roboflow python-dotenv # commented shell command

"""
### 4. Configure Roboflow API Key
Run this cell and paste your Roboflow Private API Key (`NQNQbsiMxbU33fU0UvbC`). This will write it to a local `.env` file so the cloud inference script can access it securely.
"""

import getpass

api_key = getpass.getpass("Paste your Roboflow Private API Key here: ").strip()
if api_key:
    with open(".env", "w") as f:
        f.write(f"ROBOFLOW_API_KEY={api_key}\n")
    print("API Key saved to .env file successfully!")
else:
    print("API Key cannot be empty.")

"""
### 5. Verify Dataset and Configuration
Run our verification script to ensure the folder structure, YAML paths, and class indices (bees = 0, wasps = 1) are correct.
"""

# !python tools/verify_setup.py # commented shell command

"""
### 6. Run Model Training (Using Colab GPU)
Train the YOLOv8 model on the unified wasps + bees dataset using Colab's GPU. The script automatically detects hardware acceleration.
"""

# Recommend 50 epochs, but you can adjust as needed
# !python train.py --epochs 50 --imgsz 640 --name v4_final_run --device cuda # commented shell command

"""
### 7. Run Inference / Predictions
Test the model inference locally or via the Roboflow Cloud API client.
"""

# Local inference using the best weights
# !python predict.py data/images/val/vespula-103-_jpg.rf.c9b0524cd875f3a56d58b42afffe9e3d.jpg # commented shell command

# Or hosted cloud inference via Roboflow API
# !python predict.py data/images/val/ -rf

