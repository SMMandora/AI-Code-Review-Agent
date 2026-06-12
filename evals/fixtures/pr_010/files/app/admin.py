import subprocess


def convert_image(filename: str, output: str) -> None:
    subprocess.run(
        f"convert {filename} {output}",
        shell=True,
        check=True,
    )
