import os
import re
import subprocess

project_path = r"D:\web\web"  # เปลี่ยนเป็น path โปรเจ็คของคุณ
requirements_file = os.path.join(project_path, "requirements.txt")

# regex สำหรับ import statements
import_re = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_]+)')

packages = set()

# scan ทุกไฟล์ .py
for root, dirs, files in os.walk(project_path):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, encoding='utf-8') as f:
                for line in f:
                    match = import_re.match(line)
                    if match:
                        packages.add(match.group(1))

# ตรวจสอบ package ที่ติดตั้งและดึง version
final_packages = []
for pkg in packages:
    try:
        result = subprocess.run(
            ["pip", "show", pkg],
            capture_output=True, text=True, check=True
        )
        version = None
        for l in result.stdout.splitlines():
            if l.startswith("Version:"):
                version = l.split(":", 1)[1].strip()
                break
        if version:
            final_packages.append(f"{pkg}=={version}")
        else:
            final_packages.append(pkg)
    except subprocess.CalledProcessError:
        # ถ้า package ไม่มีใน environment
        final_packages.append(pkg + "  # not installed")

# เขียนไฟล์ requirements.txt
with open(requirements_file, "w", encoding='utf-8') as f:
    f.write("\n".join(sorted(final_packages)))

print(f"✅ สร้าง {requirements_file} เรียบร้อยแล้ว")
