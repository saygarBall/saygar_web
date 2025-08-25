import os
import subprocess

# -----------------------------
# ตั้งค่า
# -----------------------------
REPO_PATH = r"D:\web\web"   # โฟลเดอร์โปรเจกต์ของคุณ
REMOTE_URL = "https://github.com/saygarball/saygar_web.git"
SIZE_LIMIT = 100 * 1024 * 1024  # 100MB

# -----------------------------
# Helper function
# -----------------------------
def run_cmd(cmd, cwd=None):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result

# -----------------------------
# 1. ตรวจสอบไฟล์ใหญ่เกิน 100MB
# -----------------------------
print("🔎 Checking large files (>100MB)...")
large_files = []
for root, dirs, files in os.walk(REPO_PATH):
    for f in files:
        path = os.path.join(root, f)
        if os.path.getsize(path) > SIZE_LIMIT:
            large_files.append(path)

if large_files:
    print("⚠️ Found large files:")
    for f in large_files:
        size = round(os.path.getsize(f) / (1024*1024), 2)
        print(f" - {f} ({size} MB)")
else:
    print("✅ No large files found.")

# -----------------------------
# 2. Git init
# -----------------------------
run_cmd("git init", cwd=REPO_PATH)

# -----------------------------
# 3. ติดตั้ง Git LFS และ track ไฟล์ใหญ่
# -----------------------------
run_cmd("git lfs install", cwd=REPO_PATH)
patterns = ["*.zip", "*.mp4", "*.wav", "*.exe"]
for p in patterns:
    run_cmd(f"git lfs track \"{p}\"", cwd=REPO_PATH)

# -----------------------------
# 4. Add .gitattributes
# -----------------------------
run_cmd("git add .gitattributes", cwd=REPO_PATH)

# -----------------------------
# 5. ถ้ามีไฟล์ใหญ่ → ลบออกจาก Git
# -----------------------------
for f in large_files:
    rel = os.path.relpath(f, REPO_PATH)
    run_cmd(f"git rm --cached \"{rel}\"", cwd=REPO_PATH)

# -----------------------------
# 6. Add, Commit
# -----------------------------
run_cmd("git add .", cwd=REPO_PATH)
run_cmd("git commit -m \"Auto commit: setup project with Git LFS and remove big files\"", cwd=REPO_PATH)

# -----------------------------
# 7. ตั้ง branch main
# -----------------------------
run_cmd("git branch -M main", cwd=REPO_PATH)

# -----------------------------
# 8. Remote origin
# -----------------------------
run_cmd("git remote remove origin", cwd=REPO_PATH)
run_cmd(f"git remote add origin {REMOTE_URL}", cwd=REPO_PATH)

# -----------------------------
# 9. Push ขึ้น GitHub
# -----------------------------
run_cmd("git push -u origin main", cwd=REPO_PATH)

print("\n🎉 Done! Your project should now be on GitHub.")
