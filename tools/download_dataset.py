import os
import sys
import shutil
import subprocess
import getpass
import yaml

def install_roboflow():
    """Ensure the roboflow library is installed."""
    try:
        import roboflow
    except ImportError:
        print("Roboflow library not found. Installing via uv...")
        try:
            # Check if uv is available, use venv's python to run pip
            subprocess.run(["uv", "pip", "install", "roboflow"], check=True)
            print("Successfully installed roboflow.")
        except Exception as e:
            print("Failed to install roboflow using uv, trying standard pip...")
            python_exe = sys.executable
            subprocess.run([python_exe, "-m", "pip", "install", "roboflow"], check=True)

def clean_local_dataset(data_dir):
    """Deletes existing images and labels folders to prepare for replacement."""
    print("\nCleaning local dataset directories...")
    folders_to_remove = [
        os.path.join(data_dir, "images", "train"),
        os.path.join(data_dir, "images", "val"),
        os.path.join(data_dir, "images", "test"),
        os.path.join(data_dir, "labels", "train"),
        os.path.join(data_dir, "labels", "val"),
        os.path.join(data_dir, "labels", "test"),
    ]
    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  Removed: {os.path.relpath(folder, os.path.dirname(data_dir))}")

def copy_dataset_files(src_dir, dest_dir):
    """Copies downloaded dataset structure to standard YOLO format location."""
    print("\nCopying new dataset files...")
    splits = ['train', 'valid', 'test']
    
    for split in splits:
        src_split_img = os.path.join(src_dir, split, "images")
        src_split_lbl = os.path.join(src_dir, split, "labels")
        
        # Determine target split name ('valid' -> 'val')
        dest_split = 'val' if split == 'valid' else split
        
        dest_split_img = os.path.join(dest_dir, "images", dest_split)
        dest_split_lbl = os.path.join(dest_dir, "labels", dest_split)
        
        if os.path.exists(src_split_img):
            os.makedirs(dest_split_img, exist_ok=True)
            for file in os.listdir(src_split_img):
                shutil.copy(os.path.join(src_split_img, file), os.path.join(dest_split_img, file))
            print(f"  Copied {len(os.listdir(src_split_img))} images to images/{dest_split}")
            
        if os.path.exists(src_split_lbl):
            os.makedirs(dest_split_lbl, exist_ok=True)
            for file in os.listdir(src_split_lbl):
                shutil.copy(os.path.join(src_split_lbl, file), os.path.join(dest_split_lbl, file))
            print(f"  Copied {len(os.listdir(src_split_lbl))} labels to labels/{dest_split}")

def fix_downloaded_labels(data_dir):
    """Corrects Roboflow exported class 0 to class 1 (Vespula_germanica)."""
    print("\nCorrecting class mappings (0 -> 1 for Vespula)...")
    fixed_count = 0
    
    for split in ['train', 'val', 'test']:
        lbl_dir = os.path.join(data_dir, "labels", split)
        if not os.path.exists(lbl_dir):
            continue
            
        for file in os.listdir(lbl_dir):
            if file.endswith('.txt') and not file.endswith('.cache'):
                path = os.path.join(lbl_dir, file)
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                modified = False
                for line in lines:
                    parts = line.strip().split()
                    if parts and parts[0] == '0':
                        parts[0] = '1'
                        new_lines.append(' '.join(parts) + '\n')
                        modified = True
                    else:
                        new_lines.append(line)
                        
                if modified:
                    with open(path, 'w') as f:
                        f.writelines(new_lines)
                    fixed_count += 1
                    
    print(f"  Successfully corrected {fixed_count} label files.")

def main():
    # Dynamically resolve base directory relative to this script's location
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")
    
    # 1. Install Roboflow SDK if needed
    install_roboflow()
    from roboflow import Roboflow
    
    # 2. Get API key
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        print("\nRoboflow API Key not found in environment variable (ROBOFLOW_API_KEY).")
        api_key = getpass.getpass("Please enter your Roboflow Private API Key: ").strip()
        if not api_key:
            print("ERROR: Private API Key is required to download the dataset.")
            sys.exit(1)
            
    # 3. Authenticate and download
    print("\nAuthenticating with Roboflow...")
    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("ws-workspace-yhner").project("example-ueewe-bw1lr")
        
        print("Downloading version 1 of the dataset (example-ueewe-bw1lr)...")
        # Download in YOLOv8 format
        dataset = project.version(1).download("yolov8", location=os.path.join(base_dir, "temp_download"))
    except Exception as e:
        print(f"ERROR: Failed to authenticate or download dataset: {e}")
        sys.exit(1)
        
    temp_download_dir = os.path.join(base_dir, "temp_download")
    if not os.path.exists(temp_download_dir):
        print(f"ERROR: Downloaded folder not found at: {temp_download_dir}")
        sys.exit(1)
        
    # 4. Clean local dataset folders
    clean_local_dataset(data_dir)
    
    # 5. Move/Copy files to standard locations
    copy_dataset_files(temp_download_dir, data_dir)
    
    # 6. Correct label indices from 0 to 1
    fix_downloaded_labels(data_dir)
    
    # 7. Cleanup temp folder
    print("\nCleaning up temporary download directory...")
    shutil.rmtree(temp_download_dir)
    
    # 8. Save API key to .env if the user wants
    env_file = os.path.join(base_dir, ".env")
    if not os.path.exists(env_file):
        try:
            with open(env_file, 'w') as f:
                f.write(f"ROBOFLOW_API_KEY={api_key}\n")
            print("Saved API Key to .env file for local inference.")
        except Exception as e:
            print(f"Could not save API Key to .env: {e}")
            
    # 9. Verify setup
    print("\nRunning verification...")
    subprocess.run([sys.executable, os.path.join(base_dir, "tools", "verify_setup.py")])
    
    print("\nDataset replace complete! You can now train the model on 124 images by running:")
    print("  python train.py")

if __name__ == '__main__':
    main()
