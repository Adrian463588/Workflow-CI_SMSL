#!/usr/bin/env python3
import sys
import os
import re
import subprocess

# Regular expressions for detecting potential secrets and sensitive keys
SECRET_REGEXES = {
    "GitHub Personal Access Token": re.compile(r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82}"),
    "Docker Hub Token": re.compile(r"dckr_pat_[a-zA-Z0-9_-]{20,50}"),
    "PEM Private Key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    "DagsHub Token Format": re.compile(r"\b[a-f0-9]{40}\b"), # 40-character hex token
    "Generic Credentials Assignment": re.compile(
        r"(?i)(token|passwd|password|secret|api_key|auth_key|private_key|user_token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-+=/]{12,})['\"]"
    )
}

# Directories or files to ignore from scanning
IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".zip", ".gz", ".tar", ".gitkeep", ".csv",
    ".ipynb", ".pdf", ".pkl", ".h5", ".ipynb_checkpoints"
}
IGNORE_DIRS = {".git", "node_modules", ".husky", ".github", "mlruns", "artifacts"}
IGNORE_FILES = {"package.json", "package-lock.json", "detect_secrets.py", "conda.yaml", "requirements.txt", ".gitignore"}

# Safe placeholders that are allowed to pass through
SAFE_PLACEHOLDERS = [
    re.compile(r"(?i)\b(your|my|mock|test|dummy|example|placeholder|insert|secrets\.|env\.|os\.environ|sys\.env)\b"),
    re.compile(r"\$\{\{\s*secrets\.[a-zA-Z0-9_]+\s*\}\}"), # GitHub Actions secret reference: ${{ secrets.XYZ }}
    re.compile(r"<[a-zA-Z0-9_ -]+>") # Bracket placeholders like <YOUR_TOKEN>
]

def is_ignored(filepath):
    # Check ignored directories
    parts = filepath.replace("\\", "/").split("/")
    for d in IGNORE_DIRS:
        if d in parts:
            return True
            
    # Check ignored extensions and files
    _, ext = os.path.splitext(filepath)
    if ext.lower() in IGNORE_EXTENSIONS:
        return True
    if os.path.basename(filepath) in IGNORE_FILES:
        return True
    return False

def is_safe_value(value_str):
    # Check if the matched secret is just a safe placeholder
    for pattern in SAFE_PLACEHOLDERS:
        if pattern.search(value_str):
            return True
    return False

def scan_file(filepath):
    leaks = []
    if not os.path.exists(filepath):
        return leaks

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("#") or clean_line.startswith("//"):
                    continue

                for name, regex in SECRET_REGEXES.items():
                    matches = regex.findall(clean_line)
                    for match in matches:
                        matched_str = match[1] if isinstance(match, tuple) else match
                        if not is_safe_value(matched_str) and not is_safe_value(clean_line):
                            leaks.append((line_no, name, clean_line[:80]))
    except Exception:
        pass

    return leaks

def get_staged_files():
    try:
        output = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
        return [f.strip() for f in output.split("\n") if f.strip()]
    except Exception:
        return []

def get_all_files():
    all_files = []
    for root, dirs, files in os.walk("."):
        # Filter out directories to avoid traversing unnecessary files
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            filepath = os.path.join(root, file)
            if filepath.startswith("./") or filepath.startswith(".\\"):
                filepath = filepath[2:]
            all_files.append(filepath)
    return all_files

def main():
    scan_all = "--all" in sys.argv or os.environ.get("CI") == "true"
    
    if scan_all:
        files_to_scan = get_all_files()
        print("🛡️  Memindai seluruh repositori dari kebocoran kredensial (CI Mode)...")
    else:
        files_to_scan = get_staged_files()
        if not files_to_scan:
            print("ℹ️  Tidak ada file yang di-stage untuk dicommit.")
            sys.exit(0)
        print("🛡️  Memindai file yang di-stage dari kebocoran kredensial (Local Hook)...")

    total_leaks = 0

    for filepath in files_to_scan:
        if is_ignored(filepath):
            continue

        leaks = scan_file(filepath)
        if leaks:
            print(f"\n❌ POTENSI KEBOCORAN KREDENSIAL terdeteksi pada: {filepath}")
            for line_no, name, snippet in leaks:
                print(f"   - Baris {line_no} [{name}]: {snippet}")
            total_leaks += len(leaks)

    if total_leaks > 0:
        print("\n⛔ SCAN GAGAL: Bersihkan rahasia di atas sebelum melanjutkan!")
        sys.exit(1)

    print("✅ Scan selesai: Tidak ada kebocoran kredensial terdeteksi.")
    sys.exit(0)

if __name__ == "__main__":
    main()
