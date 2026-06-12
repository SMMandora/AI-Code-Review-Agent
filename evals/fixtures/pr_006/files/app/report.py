import csv


def generate_report(data: list[dict], output_path: str) -> None:
    print(f"generating report with {len(data)} rows")
    try:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    except:
        pass
