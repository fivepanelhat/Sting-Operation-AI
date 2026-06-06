import os
import sys
import yaml

def verify_setup():
    base_dir = r"c:\Users\Admin\Track and Zap\Sting-Operation-AI"
    data_dir = os.path.join(base_dir, "data")
    config_file = os.path.join(base_dir, "config", "data.yaml")
    
    errors = []
    warnings = []
    
    # 1. Check data.yaml
    print("Checking data.yaml...")
    if not os.path.exists(config_file):
        errors.append("config/data.yaml is missing!")
    else:
        try:
            with open(config_file, 'r') as f:
                cfg = yaml.safe_load(f)
            
            if cfg.get('path') != 'data':
                errors.append(f"data.yaml path is set to '{cfg.get('path')}', expected 'data'.")
            else:
                print("  [OK] data.yaml path is set correctly to 'data'.")
                
            expected_names = {0: 'Apis_mellifera', 1: 'Vespula_germanica', 2: 'Vespa_velutina'}
            names = cfg.get('names', {})
            for k, v in expected_names.items():
                if names.get(k) != v:
                    errors.append(f"data.yaml class mapping mismatch: expected {k}: {v}, got {k}: {names.get(k)}")
            if not errors:
                print("  [OK] data.yaml classes are correctly defined.")
        except Exception as e:
            errors.append(f"Failed to parse data.yaml: {e}")

    # 2. Check for stray files in images
    print("\nChecking images folders...")
    for split in ['train', 'val']:
        img_split_dir = os.path.join(data_dir, "images", split)
        if not os.path.exists(img_split_dir):
            errors.append(f"Images folder for {split} split is missing!")
            continue
            
        stray_files = [f for f in os.listdir(img_split_dir) if not f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if stray_files:
            errors.append(f"Stray files found in images/{split}: {stray_files}")
        else:
            print(f"  [OK] images/{split} contains only images.")

    # 3. Check for stray files in labels and verify class indices
    print("\nChecking labels folders and class mappings...")
    for split in ['train', 'val']:
        lbl_split_dir = os.path.join(data_dir, "labels", split)
        if not os.path.exists(lbl_split_dir):
            errors.append(f"Labels folder for {split} split is missing!")
            continue
            
        stray_files = [f for f in os.listdir(lbl_split_dir) if not f.endswith('.txt')]
        if stray_files:
            errors.append(f"Stray files found in labels/{split}: {stray_files}")
            
        # Verify labels in txt files
        for file in os.listdir(lbl_split_dir):
            if file.endswith('.txt'):
                path = os.path.join(lbl_split_dir, file)
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                for line_idx, line in enumerate(lines):
                    parts = line.strip().split()
                    if parts:
                        cls = parts[0]
                        if cls not in ['0', '1', '2']:
                            errors.append(f"Invalid class index {cls} found in label file: data/labels/{split}/{file} on line {line_idx+1}")


    # 4. Check for top-level stray files
    print("\nChecking top-level label directory clean-up...")
    lbl_top_dir = os.path.join(data_dir, "labels")
    if os.path.exists(lbl_top_dir):
        top_files = [f for f in os.listdir(lbl_top_dir) if os.path.isfile(os.path.join(lbl_top_dir, f))]
        if top_files:
            errors.append(f"Stray files found in top-level labels/ directory: {top_files}")
        else:
            print("  [OK] labels/ directory is clean of stray files/caches.")

    # 5. Check virtual environment
    print("\nChecking virtual environment...")
    venv_dir = os.path.join(base_dir, ".venv")
    if not os.path.exists(venv_dir):
        warnings.append(".venv directory is missing! Run local setup first.")
    else:
        print("  [OK] .venv exists.")

    # 6. Check trained model
    print("\nChecking trained model weights...")
    model_path = os.path.join(base_dir, "models", "trained_models", "sting_operation_v3", "weights", "best.pt")
    if not os.path.exists(model_path):
        warnings.append(f"Trained model v3 weights not found at: {os.path.relpath(model_path, base_dir)}")
    else:
        print("  [OK] Trained model best.pt weights found.")

    # Summary
    print("\n=== Verification Summary ===")
    if errors:
        print(f"\nFAIL: {len(errors)} errors found:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("\nSUCCESS: No errors found! All configurations, label indices, and file structures are verified.")
        
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  - {warn}")
            
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    verify_setup()
