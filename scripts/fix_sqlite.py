import glob


def fix_sqlite() -> None:
    files = glob.glob("babylon60/**/*.py", recursive=True) + glob.glob("scripts/**/*.py", recursive=True)
    for filepath in files:
        if "database/core.py" in filepath or "purge_exceptions.py" in filepath:
            continue
        with open(filepath) as f:
            content = f.read()
        if "babylon60.database.core.connect" in content:
            content = content.replace("babylon60.database.core.connect", "babylon60.database.core.connect")
            if "import babylon60.database.core" not in content:
                content = "import babylon60.database.core\n" + content
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Fixed sqlite3 in {filepath}")


if __name__ == "__main__":
    fix_sqlite()
