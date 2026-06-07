import os
import sys
import shutil
import subprocess
import yaml

def load_env_key():
    """Attempts to read ROBOFLOW_API_KEY from environment or .env file."""
    key = os.environ.get("ROBOFLOW_API_KEY")
    if key:
        return key
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("ROBOFLOW_API_KEY="):
                    return line.strip().split("=")[1]
    return None

def main():
    # Dynamically resolve base directory relative to this script's location
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")
    
    # 1. Get API key
    api_key = load_env_key()
    if not api_key:
        print("ERROR: ROBOFLOW_API_KEY not found in environment or .env file.")
        print("Please run tools/download_dataset.py first or write the key to .env.")
        sys.exit(1)
        
    from roboflow import Roboflow
    
    # 2. Download bees dataset
    temp_dir = os.path.join(base_dir, "temp_bees_download")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    print("Connecting to Roboflow...")
    try:
        rf = Roboflow(api_key=api_key)
        project = rf.workspace("ws-workspace-yhner").project("find-new-zealand-bees")
        print("Downloading version 1 of find-new-zealand-bees dataset...")
        dataset = project.version(1).download("yolov8", location=temp_dir)
    except Exception as e:
        print(f"ERROR: Failed downloading bees dataset: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        sys.exit(1)

    # 3. Merge splits
    splits = ['train', 'valid', 'test']
    merged_summary = {'train': 0, 'val': 0, 'test': 0}
    
    print("\nMerging dataset files and mapping class indices (Bees -> Class 0)...")
    for split in splits:
        src_img_dir = os.path.join(temp_dir, split, "images")
        src_lbl_dir = os.path.join(temp_dir, split, "labels")
        
        dest_split = 'val' if split == 'valid' else split
        dest_img_dir = os.path.join(data_dir, "images", dest_split)
        dest_lbl_dir = os.path.join(data_dir, "labels", dest_split)
        
        # Ensure directories exist
        os.makedirs(dest_img_dir, exist_ok=True)
        os.makedirs(dest_lbl_dir, exist_ok=True)
        
        if not os.path.exists(src_img_dir):
            continue
            
        for file in os.listdir(src_img_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                base, ext = os.path.splitext(file)
                
                # Prefix filenames to avoid conflicts and identify sources
                new_img_name = f"bee_{base}{ext}"
                new_lbl_name = f"bee_{base}.txt"
                
                src_img_path = os.path.join(src_img_dir, file)
                src_lbl_path = os.path.join(src_lbl_dir, f"{base}.txt")
                
                dest_img_path = os.path.join(dest_img_dir, new_img_name)
                dest_lbl_path = os.path.join(dest_lbl_dir, new_lbl_name)
                
                # Copy image
                shutil.copy(src_img_path, dest_img_path)
                
                # Copy and map labels (both class 0 and 1 represent bees -> map to class 0 Apis_mellifera)
                if os.path.exists(src_lbl_path):
                    with open(src_lbl_path, 'r') as f:
                        lines = f.readlines()
                        
                    new_lines = []
                    for line in lines:
                        parts = line.strip().split()
                        if parts:
                            # Map any class index (e.g. 0 or 1) to 0 (bee class)
                            parts[0] = '0'
                            new_lines.append(' '.join(parts) + '\n')
                            
                    with open(dest_lbl_path, 'w') as f:
                        f.writelines(new_lines)
                else:
                    # Create empty file for background images
                    with open(dest_lbl_path, 'w') as f:
                        pass
                
                merged_summary[dest_split] += 1

    # 4. Clean up temp folder
    print("\nCleaning up temporary download directory...")
    shutil.rmtree(temp_dir)
    
    print("\n=== Merge Summary ===")
    for split, count in merged_summary.items():
        print(f"  Merged {count} bee images/labels into data/{split}/")
        
    # 5. Run verification script
    print("\nRunning verification on merged dataset...")
    subprocess.run([sys.executable, os.path.join(base_dir, "tools", "verify_setup.py")])
    
    print("\nDataset merge complete! You can now train the multi-class model on wasp + bee data by running:")
    print("  python train.py")

if __name__ == '__main__':
    main()
