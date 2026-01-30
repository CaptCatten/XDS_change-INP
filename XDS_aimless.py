import os
import re
import shutil
import subprocess

# ============================================================
# USER CONFIGURATION
# If you do not want to change a parameter, leave as None.
# Paths should be absolute.
# ============================================================

# Path of your raw data root directory, grouped by dataset id
RAW_DATA_BASE_DIR = "/path/to/raw_data/CC138A/"

# Path of your processed data set (contains XDS.INP, XDS_ASCII.HKL, etc.)
ROOT_DIR = "/home/lauren/Desktop/testing_ground/CC138A"

# If your dataset has a common prefix, or you have a unique identifier
# you want to restrict to, set it here (e.g. "TRIM72_"). Otherwise leave as None.
PREFIX_HINT = None

# If you change this, also change the unit cell constants,
# or XDS will produce an error.
SPACE_GROUP_NUMBER = None          # e.g. "96"
UNIT_CELL_CONSTANTS = None         # e.g. "50.0 60.0 70.0 90.0 90.0 120.0"

# Optional overrides for XDS ranges, e.g. "1 3600"
DATA_RANGE = None
SPOT_RANGE = None

# Path to CCP4 setup script for pointless/aimless/ctruncate/freerflag
# if you are using the work station copy the path below
# "/usr/local/ccp4-8.0/bin/ccp4.setup-sh"
CCP4_SETUP = "/opt/xtal/ccp4-9/bin/ccp4.setup-sh"

# ================== PIPELINE MODE ==================
# Options:
#   MODE = "full"         → rewrite XDS.INP → run XDS → CCP4 pipeline
#   MODE = "aimless-only" → ONLY run CCP4 pipeline
#                            (ignores raw data, ignores XDS.INP, skips XDS)
MODE = "aimless-only"
# ===================================================


# ================== ROBUSTNESS / DEV CONTROLS ==================
# Timeouts (seconds). Set to None to disable.
XDS_TIMEOUT_SECONDS = 3600
CCP4_TIMEOUT_SECONDS = 1800

# One summary file for the whole run:
SUMMARY_FILE = os.path.join(ROOT_DIR, "summary.txt")
# ============================================================


def run_cmd(cmd, cwd, timeout=None):
    """
    Run a command quietly (we rely on the tool logs you already redirect).
    Returns (ok_bool, returncode_int, timed_out_bool).
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
        return p.returncode == 0, p.returncode, False
    except subprocess.TimeoutExpired:
        return False, 124, True
    except Exception:
        return False, 125, False


def write_summary_header(summary_path):
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        f.write("dataset\tspace_group\tresolution_A\n")


def append_summary_line(summary_path, dataset_id, space_group, resolution):
    with open(summary_path, "a") as f:
        f.write(f"{dataset_id}\t{space_group}\t{resolution}\n")


def find_name_template_in_raw_data(raw_base, dataset_id, prefix_hint=None):
    search_root = os.path.join(raw_base, dataset_id)
    if not os.path.isdir(search_root):
        raise FileNotFoundError(search_root)

    for root, _, files in os.walk(search_root):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                wildcard_file = re.sub(r"_(\d+)\.cbf\.gz$", r"_?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)

    raise FileNotFoundError("No matching cbf.gz found")


def transform_xds_inp_auto_template(
    inp,
    raw_base,
    dataset_id,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None,
):
    name_template = find_name_template_in_raw_data(raw_base, dataset_id, prefix_hint)

    with open(inp, "r") as f:
        lines = f.readlines()

    new_lines = []
    has_sg = False
    has_uc = False

    for line in lines:
        s = line.lstrip()

        if s.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_template}\n")
            continue

        if s.startswith("DETECTOR=") and "PILATUS" in s:
            new_lines.append("DETECTOR= EIGER\n")
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            continue

        if s.startswith("FRIEDEL'S_LAW="):
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        if s.startswith("GENERIC_LIB=") or s.startswith("LIB="):
            continue

        if s.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            new_lines.append("!" + line if not s.startswith("!") else line)
            continue

        if s.startswith("SPOT_RANGE=") and spot_range:
            new_lines.append(f"SPOT_RANGE= {spot_range}\n")
            continue

        if s.startswith("DATA_RANGE=") and data_range:
            new_lines.append(f"DATA_RANGE= {data_range}\n")
            continue

        if s.startswith("SPACE_GROUP_NUMBER="):
            has_sg = True

        if s.startswith("UNIT_CELL_CONSTANTS="):
            has_uc = True

        new_lines.append(line)

    if space_group_number is not None and not has_sg:
        new_lines.append(f"\nSPACE_GROUP_NUMBER= {space_group_number}\n")

    if unit_cell_constants is not None and not has_uc:
        new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")

    shutil.copy2(inp, inp.replace("XDS.INP", "XDS_org.INP"))
    with open(inp, "w") as f:
        f.writelines(new_lines)

    return True


def run_xds(folder):
    ok, rc, timed_out = run_cmd(
        ["bash", "-lc", "xds_par > XDS_run.log 2>&1"],
        cwd=folder,
        timeout=XDS_TIMEOUT_SECONDS,
    )

    if (not ok) or (not os.path.isfile(os.path.join(folder, "XDS_ASCII.HKL"))):
        folder_name = os.path.basename(os.path.abspath(folder))
        print(f"XDS failed for '{folder_name}'")
        print(f"  Check: {os.path.join(folder, 'XDS_run.log')}")
        return False

    return True


def parse_aimless_summary(log_path):
    """
    Extract only: space group and high-resolution limit from aimless.log.
    Returns (space_group_str, high_res_str) or ('UNKNOWN', 'UNKNOWN').
    """
    space_group = "UNKNOWN"
    high_res = "UNKNOWN"

    try:
        with open(log_path, "r") as f:
            text = f.read()
    except FileNotFoundError:
        return space_group, high_res

    sg_matches = list(re.finditer(r"Space\s+group\s*[:=]\s*(.+)", text))
    if sg_matches:
        sg_line = sg_matches[-1].group(1).strip()
        sg_line = re.sub(r"\(.*?\)", "", sg_line).strip()
        space_group = sg_line

    res_matches = list(re.finditer(r"High\s+resolution\s+limit\s+([0-9.]+)", text))
    if not res_matches:
        res_matches = list(re.finditer(r"Resolution\s+range\s+[0-9.]+\s+to\s+([0-9.]+)", text))
    if res_matches:
        high_res = res_matches[-1].group(1)

    return space_group, high_res


def run_ccp4_pipeline(folder):
    """
    Uses only per-tool logs. No wrapper log.
    Returns (space_group, high_res) on success, else None.
    """
    if not os.path.isfile(os.path.join(folder, "XDS_ASCII.HKL")):
        return None

    bash_cmd = f"""source "{CCP4_SETUP}" && \
export CCP4_SCR="$PWD/CCP4_SCRATCH" && mkdir -p "$CCP4_SCR" && \
rm -f XDS_ASCII.mtz Merged.mtz Truncate.mtz Final_with_FreeR.mtz XDS.xml && \
pointless XDS_ASCII.HKL hklout XDS_ASCII.mtz > pointless.log 2>&1 && \
aimless HKLIN XDS_ASCII.mtz HKLOUT Merged.mtz XMLOUT XDS.xml --no-input > aimless.log 2>&1 && \
ctruncate -mtzin Merged.mtz -mtzout Truncate.mtz -colin '/*/*/[IMEAN,SIGIMEAN]' > ctruncate.log 2>&1 && \
freerflag HKLIN Truncate.mtz HKLOUT Final_with_FreeR.mtz > freerflag.log 2>&1 << EOF
FREERFRAC 0.05
END
EOF
"""
    ok, rc, timed_out = run_cmd(
        ["bash", "-lc", bash_cmd],
        cwd=folder,
        timeout=CCP4_TIMEOUT_SECONDS,
    )

    if not ok:
        folder_name = os.path.basename(os.path.abspath(folder))
        print(f"CCP4 pipeline failed for '{folder_name}'")
        print("  Check logs:")
        print(f"   - {os.path.join(folder, 'pointless.log')}")
        print(f"   - {os.path.join(folder, 'aimless.log')}")
        print(f"   - {os.path.join(folder, 'ctruncate.log')}")
        print(f"   - {os.path.join(folder, 'freerflag.log')}")
        return None

    return parse_aimless_summary(os.path.join(folder, "aimless.log"))


def full_pipeline(
    root_dir,
    raw_data_base_dir,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None,
):
    print(f"\n=== FULL MODE: Starting batch processing in: {root_dir} ===\n")
    write_summary_header(SUMMARY_FILE)

    for subdir, _, files in os.walk(root_dir):
        if "XDS.INP" not in files:
            continue

        rel_path = os.path.relpath(subdir, root_dir)
        dataset_id = rel_path.split(os.sep)[0]
        folder_name = os.path.basename(os.path.abspath(subdir))

        print(f"\n--- Dataset directory: {subdir} (dataset_id = {dataset_id}) ---")

        try:
            transform_xds_inp_auto_template(
                os.path.join(subdir, "XDS.INP"),
                raw_data_base_dir,
                dataset_id,
                prefix_hint,
                space_group_number,
                unit_cell_constants,
                data_range,
                spot_range,
            )
        except Exception as e:
            print(f"XDS.INP modification failed for '{folder_name}': {e}")
            continue

        if not run_xds(subdir):
            continue

        result = run_ccp4_pipeline(subdir)
        if result is None:
            continue

        sg, res = result
        append_summary_line(SUMMARY_FILE, dataset_id, sg, res)

    print(f"\nSummary written to: {SUMMARY_FILE}")


def aimless_only(root_dir):
    print(f"\n=== AIMLESS-ONLY MODE: Searching under: {root_dir} ===\n")
    write_summary_header(SUMMARY_FILE)

    for subdir, _, files in os.walk(root_dir):
        if "XDS_ASCII.HKL" not in files:
            continue

        rel_path = os.path.relpath(subdir, root_dir)
        dataset_id = rel_path.split(os.sep)[0]

        print(f"\n--- CCP4-only dataset: {subdir} ---")
        result = run_ccp4_pipeline(subdir)
        if result is None:
            continue

        sg, res = result
        append_summary_line(SUMMARY_FILE, dataset_id, sg, res)

    print(f"\nSummary written to: {SUMMARY_FILE}")


if __name__ == "__main__":
    if MODE == "aimless-only":
        aimless_only(ROOT_DIR)
    elif MODE == "full":
        full_pipeline(
            root_dir=ROOT_DIR,
            raw_data_base_dir=RAW_DATA_BASE_DIR,
            prefix_hint=PREFIX_HINT,
            space_group_number=SPACE_GROUP_NUMBER,
            unit_cell_constants=UNIT_CELL_CONSTANTS,
            data_range=DATA_RANGE,
            spot_range=SPOT_RANGE,
        )
    else:
        print(f"ERROR: Unknown MODE='{MODE}'. Use 'full' or 'aimless-only'.")
