import os


def ensure_file(path: str) -> None:
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("")
