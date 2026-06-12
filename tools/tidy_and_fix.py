import os
import shutil
import subprocess


def run_git_cmd(args):
    """Run a git command and return stdout/stderr."""
    try:
        res = subprocess.run(
            ["git"] + args, capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: git {' '.join(args)}")
        print(e.stderr)
        return None


def main():
    # Dynamically resolve base directory relative to this script's location
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_dir, "data")

    # 1. Create target directories
    raw_ann_dir = os.path.join(data_dir, "raw_annotations")
    vis_dir = os.path.join(data_dir, "visualizations")
    tools_dir = os.path.join(base_dir, "tools")

    for d in [raw_ann_dir, vis_dir, tools_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory: {os.path.relpath(d, base_dir)}")

    # 2. Move misplaced pixel-coordinate text files from data/images/train/
    images_train_dir = os.path.join(data_dir, "images", "train")
    moved_txt_count = 0
    if os.path.exists(images_train_dir):
        for file in os.listdir(images_train_dir):
            if file.endswith(".txt"):
                src = os.path.join(images_train_dir, file)
                dst = os.path.join(raw_ann_dir, file)

                # Check if it is tracked in Git
                is_tracked = run_git_cmd(
                    ["ls-files", f"data/images/train/{file}"]
                )

                if is_tracked:
                    # Move via git mv to keep history/cleanliness
                    run_git_cmd(
                        [
                            "mv",
                            f"data/images/train/{file}",
                            f"data/raw_annotations/{file}",
                        ]
                    )
                    print(
                        f"Git moved: data/images/train/{file} -> data/raw_annotations/{file}"
                    )
                else:
                    shutil.move(src, dst)
                    print(
                        f"Moved: data/images/train/{file} -> data/raw_annotations/{file}"
                    )
                moved_txt_count += 1
    print(f"Reorganized {moved_txt_count} misplaced annotation files.")

    # 3. Move Roboflow screenshot PNGs from data/labels/
    labels_dir = os.path.join(data_dir, "labels")
    moved_png_count = 0
    if os.path.exists(labels_dir):
        for file in os.listdir(labels_dir):
            if file.lower().endswith(".png"):
                src = os.path.join(labels_dir, file)
                dst = os.path.join(vis_dir, file)

                is_tracked = run_git_cmd(["ls-files", f"data/labels/{file}"])

                if is_tracked:
                    run_git_cmd(
                        [
                            "mv",
                            f"data/labels/{file}",
                            f"data/visualizations/{file}",
                        ]
                    )
                    print(
                        f"Git moved: data/labels/{file} -> data/visualizations/{file}"
                    )
                else:
                    shutil.move(src, dst)
                    print(
                        f"Moved: data/labels/{file} -> data/visualizations/{file}"
                    )
                moved_png_count += 1
    print(f"Reorganized {moved_png_count} screenshot visualization files.")

    # 4. Remove cached files from Git tracking
    cache_files = ["data/labels/train.cache", "data/labels/val.cache"]
    for cache in cache_files:
        cache_path = os.path.join(base_dir, cache)
        is_tracked = run_git_cmd(["ls-files", cache])
        if is_tracked:
            run_git_cmd(["rm", "--cached", cache])
            print(f"Untracked from git: {cache}")
        if os.path.exists(cache_path):
            os.remove(cache_path)
            print(f"Removed cache file: {cache}")

    # 5. Fix class mapping in label files (0 -> 1)
    fixed_labels_count = 0
    modified_lines_count = 0

    for split in ["train", "val"]:
        lbl_split_dir = os.path.join(data_dir, "labels", split)
        if not os.path.exists(lbl_split_dir):
            continue

        for file in os.listdir(lbl_split_dir):
            if file.endswith(".txt") and not file.endswith(".cache"):
                path = os.path.join(lbl_split_dir, file)
                with open(path, "r") as f:
                    lines = f.readlines()

                new_lines = []
                file_modified = False
                for line in lines:
                    parts = line.strip().split()
                    if parts and parts[0] == "0":
                        parts[0] = "1"
                        new_lines.append(" ".join(parts) + "\n")
                        file_modified = True
                        modified_lines_count += 1
                    else:
                        new_lines.append(line)

                if file_modified:
                    with open(path, "w") as f:
                        f.writelines(new_lines)
                    print(f"Corrected labels in: data/labels/{split}/{file}")
                    fixed_labels_count += 1

    print(
        f"\nCorrected class mappings in {fixed_labels_count} label files (modified {modified_lines_count} annotations)."
    )


if __name__ == "__main__":
    main()
