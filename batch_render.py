import os
import subprocess

# Root directory of CAD files
CAD_ROOT = "cad_samples/"

# Supported file types
SUPPORTED_EXTENSIONS = [".step", ".stp", ".ply", ".obj"]

# Batch size
BATCH_SIZE = 10

def find_supported_files(root_dir):
    all_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                all_files.append(os.path.join(dirpath, file))
    return all_files

def main():
    cad_files = find_supported_files(CAD_ROOT)
    total_files = len(cad_files)
    print(f"🟢 Found {total_files} CAD files to visualize.\n")

    for start in range(0, total_files, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total_files)
        batch = cad_files[start:end]
        print(f"\n🔢 Processing batch {start//BATCH_SIZE + 1}: files {start+1} to {end}")

        for idx, cad_file in enumerate(batch, start=start + 1):
            print(f"\n[{idx}/{total_files}] 🖼️ Visualizing: {cad_file}")
            print("👉 Close the window to proceed to the next file...")

            try:
                subprocess.run(["python", "visualize.py", cad_file], check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Error visualizing {cad_file}:\n{e}")

        if end < total_files:
            input(f"\n✅ Batch {start//BATCH_SIZE + 1} complete. Press Enter to continue to next batch...")
        else:
            print("\n🎉 All files visualized!")

if __name__ == "__main__":
    main()
