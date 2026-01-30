import os
from pathlib import Path

# =========================
# CONFIGURATION
# =========================
# Hardcoded path to scan
TARGET_PATH = Path(r"F:\Pluto")   # 🔁 CHANGE THIS PATH AS NEEDED

# Output file (saved where this script is run)
OUTPUT_FILE = Path.cwd() / "folder_structure.txt"


# =========================
# CORE LOGIC
# =========================
def generate_tree(path: Path, prefix: str = "") -> list[str]:
    """
    Recursively generate folder structure as a tree.
    """
    lines = []
    entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            lines.extend(generate_tree(entry, prefix + extension))

    return lines


def main():
    if not TARGET_PATH.exists():
        print(f"❌ Path does not exist: {TARGET_PATH}")
        return

    print(f"📂 Scanning: {TARGET_PATH}")

    tree_lines = [f"{TARGET_PATH}"]
    tree_lines.extend(generate_tree(TARGET_PATH))

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f"✅ Folder structure saved to: {OUTPUT_FILE}")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
