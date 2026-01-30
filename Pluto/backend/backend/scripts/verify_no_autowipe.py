"""
Verify that auto-wipe is disabled in main.py
"""
import sys
from pathlib import Path

# Read main.py
main_py_path = Path(__file__).parent.parent / "app" / "main.py"

with open(main_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if force_wipe_memory is being called (not commented out)
if 'force_wipe_memory(CHROMA_PATH)' in content and not '# force_wipe_memory(CHROMA_PATH)' in content:
    print("[ERROR] Auto-wipe is STILL ACTIVE!")
    print("The line 'force_wipe_memory(CHROMA_PATH)' is not commented out.")
    sys.exit(1)
elif '# force_wipe_memory(CHROMA_PATH)' in content:
    print("[OK] Auto-wipe is properly DISABLED (commented out)")
    print("\nNext steps:")
    print("1. STOP the backend server completely (Ctrl+C)")
    print("2. Verify no Python process is running")
    print("3. Restart: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("4. The database should persist between restarts now!")
    sys.exit(0)
else:
    print("[WARN] force_wipe_memory not found in main.py")
    print("This might be OK if the function was removed entirely")
    sys.exit(0)
