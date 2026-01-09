#!/usr/bin/env python3
import os
import re
from datetime import datetime

# ==========================
# USER CONFIG
# ==========================
ROOT_DIR = "/media/lauren/T7/Processed_data/processed_data/CC138A"
OUTPUT_LOG = os.path.join(ROOT_DIR, "aimless_summary.log")


def parse_aimless_log(log_path):
    """
    Return (space_group, high_resolution_A) from an aimless.log.
    If not found, returns ('UNKNOWN', 'UNKNOWN').
    """
    space_group = "UNKNOWN"
    high_res = "UNKNOWN"

    try:
        with open(log_path, "r", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        return space_group, high_res

    # Space group (use last occurrence)
    sg_matches = list(
        re.finditer(r"Space\s+group\s*[:=]\s*(.+)", text, flags=re.IGNORECASE)
    )
    if sg_matches:
        sg_line = sg_matches[-1].group(1).strip()
        sg_line = re.sub(r"\(.*?\)", "", sg_line).strip()
        space_group = sg_line

    # High resolution limit
    res_matches = list(
        re.finditer(
            r"High\s+resolution\s+limit\s+([0-9]+(?:\.[0-9]+)?)",
            text,
            flags=re.IGNORECASE,
        )
    )
    if res_matches:
        high_res = res_matches[-1].group(1)
        return space_group, high_res

    # Fallback
    rr_matches = list(
        re.finditer(
            r"Resolution\s+range\s+[0-9]+(?:\.[0-9]+)?\s+to\s+([0-9]+(?:\.[0-9]+)?)",
            text,
            flags=re.IGNORECASE,
        )
    )
    if rr_matches:
        high_res = rr_matches[-1].group(1)

    return space_group, high_res


def iter_aimless_logs(root_dir):
    """
    Yield (dataset_id, aimless_log_path).
    dataset_id = first directory under ROOT_DIR.
    """
    for subdir, _, files in os.walk(root_dir):
        if "aimless.log" not in files:
            continue

        rel = os.path.relpath(subdir, root_dir)
        dataset_id = rel.split(os.sep)[0] if rel and rel != "." else "."

        yield dataset_id, os.path.join(subdir, "aimless.log")


def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []

    for dataset_id, log_path in iter_aimless_logs(ROOT_DIR):
        sg, res = parse_aimless_log(log_path)
        rows.append((dataset_id, sg, res, os.path.dirname(log_path)))

    rows.sort(key=lambda x: (x[0], x[3]))

    with open(OUTPUT_LOG, "w") as log:
        log.write("===== AIMLESS SUMMARY =====\n")
        log.write(f"Root directory : {ROOT_DIR}\n")
        log.write(f"Generated      : {timestamp}\n")
        log.write(f"Datasets found : {len(rows)}\n")
        log.write("\n")

        header = f"{'DATASET':12s}  {'SPACE_GROUP':20s}  {'HIGH_RES (Å)':12s}  PATH\n"
        log.write(header)
        log.write("-" * len(header) + "\n")

        for dataset_id, sg, res, folder in rows:
            log.write(
                f"{dataset_id:12s}  {sg:20s}  {res:12s}  {folder}\n"
            )

    print(f"✔ Wrote summary log: {OUTPUT_LOG}")


if __name__ == "__main__":
    main()
