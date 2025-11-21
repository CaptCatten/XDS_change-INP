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
RAW_DATA_BASE_DIR = "/home/napasornnilparuk/Desktop/TRIM72/Beamline_data/20251025/raw_data/CC138A/"

# Path of your processed data set (contains XDS.INP, XDS_ASCII.HKL, etc.)
ROOT_DIR = "/home/napasornnilparuk/Desktop/TRIM72/Beamline_data/20251025/processed_data/CC138A/"

# If your dataset has a common prefix, or you have a unique identifier
# you want to restrict to, set it here (e.g. "TRIM72_"). Otherwise leave as None.
PREFIX_HINT = None

# If you change this, also change the unit cell constants,
# or XDS will produce an error.
SPACE_GROUP_NUMBER = None          # e.g. "96"
UNIT_CELL_CONSTANTS = None         # e.g. "50.0 60.0 70.0 90.0 90.0 120.0"

# Optional overrides for XDS ranges, e.g. "1 360"
DATA_RANGE = None
SPOT_RANGE = None

# Path to CCP4 setup script for pointless/aimless
CCP4_SETUP = "/opt/xtal/ccp4-9/bin/ccp4.setup-sh"

# Whether to run XDS and/or Aimless in FULL mode
RUN_XDS = True
RUN_AIMLESS = True

# ================== PIPELINE MODE ==================
# Options:
#   MODE = "full"         → rewrite XDS.INP → run XDS → run Aimless
#   MODE = "aimless-only" → ONLY run pointless + aimless
#                            (ignores raw data, ignores XDS.INP, skips XDS)
MODE = "full"
# ===================================================


def find_name_template_in_raw_data(raw_data_base_dir, dataset_id, prefix_hint=None):
    """
    Search only in /raw_data_base_dir/<dataset_id>/** for *.cbf.gz
    and convert the last frame number to ?????.
    """
    search_root = os.path.join(raw_data_base_dir, dataset_id)
    print(f" Searching in raw data folder: {search_root}")

    if not os.path.isdir(search_root):
        raise FileNotFoundError(
            f"Raw data folder for dataset '{dataset_id}' not found under {raw_data_base_dir}"
        )

    for root, _, files in os.walk(search_root):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                print(f"  Found file: {file} in {root}")
                # e.g. TRIM72_09_1_00001.cbf.gz -> TRIM72_09_1_?????.cbf.gz
                wildcard_file = re.sub(r"_(\d+)\.cbf\.gz$", r"_?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)

    raise FileNotFoundError(
        f"No matching .cbf.gz file found in {search_root} with prefix '{prefix_hint}'"
    )


def transform_xds_inp_auto_template(
    input_path,
    raw_data_base_dir,
    dataset_id,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    """
    Modify XDS.INP in-place:
      - fix NAME_TEMPLATE_OF_DATA_FRAMES using raw data
      - switch DETECTOR to EIGER and set OVERLOAD
      - force FRIEDEL'S_LAW=TRUE
      - remove GENERIC_LIB / LIB
      - comment MAXIMUM_NUMBER_OF_JOBS
      - optionally override SPOT_RANGE / DATA_RANGE
      - optionally append SPACE_GROUP_NUMBER / UNIT_CELL_CONSTANTS
    """
    print(f"\n Processing XDS.INP: {input_path}")
    print(f" Dataset id inferred: {dataset_id}")

    try:
        name_template_path = find_name_template_in_raw_data(
            raw_data_base_dir, dataset_id, prefix_hint
        )
    except FileNotFoundError as e:
        print(f"  WARNING: {e}")
        return False

    with open(input_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    has_space_group = False
    has_unit_cell = False

    for line in lines:
        stripped_line = line.lstrip()

        if stripped_line.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            print("  Replacing NAME_TEMPLATE_OF_DATA_FRAMES")
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_template_path}\n")
            continue

        if stripped_line.startswith("DETECTOR=") and "PILATUS" in stripped_line:
            print("  Replacing DETECTOR with EIGER and setting OVERLOAD")
            new_lines.append("DETECTOR= EIGER\n")
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            continue

        if stripped_line.startswith("FRIEDEL'S_LAW="):
            print("  Forcing FRIEDEL'S_LAW=TRUE")
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        if stripped_line.startswith("GENERIC_LIB=") or stripped_line.startswith("LIB="):
            print("  Removing GENERIC_LIB / LIB line")
            continue

        if stripped_line.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            print("  Commenting out MAXIMUM_NUMBER_OF_JOBS")
            if stripped_line.startswith("!"):
                new_lines.append(line)
            else:
                new_lines.append("!" + line)
            continue

        if stripped_line.startswith("SPOT_RANGE="):
            if spot_range:
                print("  Replacing SPOT_RANGE")
                new_lines.append(f"SPOT_RANGE= {spot_range}\n")
            else:
                new_lines.append(line)
            continue

        if stripped_line.startswith("DATA_RANGE="):
            if data_range:
                print("  Replacing DATA_RANGE")
                new_lines.append(f"DATA_RANGE= {data_range}\n")
            else:
                new_lines.append(line)
            continue

        if stripped_line.startswith("SPACE_GROUP_NUMBER="):
            has_space_group = True

        if stripped_line.startswith("UNIT_CELL_CONSTANTS="):
            has_unit_cell = True

        new_lines.append(line)

    if space_group_number is not None and not has_space_group:
        print("  Appending SPACE_GROUP_NUMBER")
        new_lines.append(f"\nSPACE_GROUP_NUMBER= {space_group_number}\n")

    if unit_cell_constants is not None and not has_unit_cell:
        print("  Appending UNIT_CELL_CONSTANTS")
        new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")

    backup_path = input_path.replace("XDS.INP", "XDS_org.INP")
    shutil.copy2(input_path, backup_path)
    print(f"  Backed up original to: {backup_path}")

    with open(input_path, 'w') as f:
        f.writelines(new_lines)
    print(f"  Overwritten: {input_path}")

    return True


def run_xds(folder):
    """Run xds_par in the given folder and capture log (used in FULL mode)."""
    if not RUN_XDS:
        return True

    print(f"  Running xds_par in: {folder}")
    result = subprocess.run(
        ["bash", "-lc", "xds_par > XDS_run.log 2>&1"],
        cwd=folder,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  ERROR: xds_par failed")
        print("  ---- stdout ----")
        print(result.stdout)
        print("  ---- stderr ----")
        print(result.stderr)
        return False

    if not os.path.isfile(os.path.join(folder, "XDS_ASCII.HKL")):
        print("  ERROR: XDS_ASCII.HKL not found after xds_par")
        return False

    print("  xds_par finished successfully")
    return True


def run_pointless_aimless(folder):
    """Run pointless + aimless on XDS_ASCII.HKL using CCP4."""
    hkl_path = os.path.join(folder, "XDS_ASCII.HKL")
    if not os.path.isfile(hkl_path):
        print("  WARNING: XDS_ASCII.HKL not found, skipping aimless.")
        return False

    print(f"  Running pointless + aimless in: {folder}")

    bash_cmd = f"""source {CCP4_SETUP} && \
    pointless XDS_ASCII.HKL > pointless1.log 2>&1 && \
    pointless -copy XDS_ASCII.HKL hklout XDS_ASCII.mtz > pointless2.log 2>&1 && \
    aimless HKLIN XDS_ASCII.mtz HKLOUT Merged.mtz XMLOUT XDS.xml \
        --no-input > aimless.log 2>&1 && \
    ctruncate HKLIN Merged.mtz HKLOUT Truncate.mtz XMLSTATOUT Truncate.xml \
        > ctruncate.log 2>&1 && \
    freerflag HKLIN Truncate.mtz HKLOUT Final_with_FreeR.mtz \
        > freerflag.log 2>&1 << EOF
    FREERFRAC 0.05
    END
    EOF
    """


    result = subprocess.run(
        ["bash", "-lc", bash_cmd],
        cwd=folder,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("  ERROR: pointless/aimless failed")
        print("  ---- stdout ----")
        print(result.stdout)
        print("  ---- stderr ----")
        print(result.stderr)
        return False

    print("  pointless + aimless finished successfully")
    return True


def full_pipeline(
    root_dir,
    raw_data_base_dir,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    """
    FULL MODE:
      - rewrite XDS.INP
      - run XDS
      - run pointless + aimless
    """
    print(f"\n=== FULL MODE: Starting batch processing in: {root_dir} ===\n")

    processed = 0
    xds_ok = 0
    aimless_ok = 0

    for subdir, _, files in os.walk(root_dir):
        if "XDS.INP" not in files:
            continue

        inp_path = os.path.join(subdir, "XDS.INP")

        # dataset_id = first folder under ROOT_DIR (e.g. "9" or "POS9")
        rel_path = os.path.relpath(subdir, root_dir)
        dataset_id = rel_path.split(os.sep)[0]

        print(f"\n--- Dataset directory: {subdir} (dataset_id = {dataset_id}) ---")

        ok = transform_xds_inp_auto_template(
            inp_path,
            raw_data_base_dir,
            dataset_id=dataset_id,
            prefix_hint=prefix_hint,
            space_group_number=space_group_number,
            unit_cell_constants=unit_cell_constants,
            data_range=data_range,
            spot_range=spot_range,
        )

        if not ok:
            print(" Skipping XDS/Aimless because XDS.INP modification failed.")
            continue

        processed += 1

        if run_xds(subdir):
            xds_ok += 1
            if RUN_AIMLESS and run_pointless_aimless(subdir):
                aimless_ok += 1

    print("\n=== FULL MODE: Batch processing complete ===")
    print(f" Total XDS.INP files processed: {processed}")
    if RUN_XDS:
        print(f" XDS successful:                  {xds_ok}")
    if RUN_AIMLESS:
        print(f" Aimless successful:              {aimless_ok}")


def aimless_only(root_dir):
    """
    AIMLESS-ONLY MODE:
      - DOES NOT touch XDS.INP
      - DOES NOT look at RAW_DATA_BASE_DIR
      - DOES NOT run XDS
      - ONLY: finds XDS_ASCII.HKL and runs pointless + aimless
    """
    print(f"\n=== AIMLESS-ONLY MODE: Searching under: {root_dir} ===\n")

    aimless_ok = 0
    aimless_fail = 0

    for subdir, _, files in os.walk(root_dir):
        if "XDS_ASCII.HKL" not in files:
            continue

        print(f"\n--- Aimless-only dataset: {subdir} ---")

        if run_pointless_aimless(subdir):
            aimless_ok += 1
        else:
            aimless_fail += 1

    print("\n=== AIMLESS-ONLY MODE: Complete ===")
    print(f" Datasets with XDS_ASCII.HKL: {aimless_ok + aimless_fail}")
    print(f" Aimless successful:          {aimless_ok}")
    print(f" Aimless failed:              {aimless_fail}")


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
