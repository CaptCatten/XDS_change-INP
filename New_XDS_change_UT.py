import os
import re

# --- User Configuration ---
# If you do not want change, keep the variable as "None"
RAW_DATA_BASE_DIR = "/path/to/raw/data"         # e.g. "/mnt/data/xtal_images"
PREFIX_HINT = None                              # e.g. "dataset1_"
SPACE_GROUP_NUMBER = None                       # e.g. 19
UNIT_CELL_CONSTANTS = None                      # e.g. "70.1 80.2 90.3 90 90 90"
DATA_RANGE = None                               # e.g. "1 900"
SPOT_RANGE = None                               # e.g. "1 100"
ROOT_DIR = "/path/to/xds/projects"              # Folder containing multiple XDS.INP files

def find_name_template_in_raw_data(raw_data_base_dir, prefix_hint=None):
    print(f" Searching in: {raw_data_base_dir}")
    for root, _, files in os.walk(raw_data_base_dir):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                print(f" Found file: {file} in {root}")
                wildcard_file = re.sub(r"\d+\.cbf\.gz$", "?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)
    raise FileNotFoundError(f"No matching .cbf.gz file found under {raw_data_base_dir} with prefix '{prefix_hint}'")

def transform_xds_inp_auto_template(
    input_path, output_path, raw_data_base_dir,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    print(f"\n Processing file: {input_path}")
    
    try:
        name_template_path = find_name_template_in_raw_data(raw_data_base_dir, prefix_hint)
    except FileNotFoundError as e:
        print(f"⚠ {e}")
        return

    with open(input_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            print("Replacing NAME_TEMPLATE_OF_DATA_FRAMES")
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_template_path}\n")
            continue

        if stripped.startswith("DETECTOR= PILATUS"):
            print("Replacing DETECTOR with EIGER")
            new_lines.append("DETECTOR= EIGER\n")
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            continue

        if stripped.startswith("FRIEDEL'S_LAW="):
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        if re.match(r"^STRONG_PIXEL\s*=", stripped):
            new_lines.append(f"!{line}" if not line.lstrip().startswith("!") else line)
            continue

        if stripped.startswith("SPOT_RANGE="):
            new_lines.append(f"SPOT_RANGE={spot_range}\n" if spot_range else line)
            continue

        if stripped.startswith("DATA_RANGE="):
            new_lines.append(f"DATA_RANGE={data_range}\n" if data_range else line)
            continue

        if stripped.startswith("SPACE_GROUP_NUMBER=") and space_group_number is not None:
            new_lines.append(f"SPACE_GROUP_NUMBER={space_group_number}\n")
            continue

        if stripped.startswith("UNIT_CELL_CONSTANTS=") and unit_cell_constants is not None:
            new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")
            continue

        new_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(new_lines)
    print(f" Written modified file: {output_path}")

def batch_process_xds_inps(
    root_dir,
    raw_data_base_dir,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    print(f"\n Starting batch processing in: {root_dir}\n")
    for subdir, _, files in os.walk(root_dir):
        if "XDS.INP" in files:
            inp_path = os.path.join(subdir, "XDS.INP")
            out_path = os.path.join(subdir, "XDS_modified.INP")
            print(f" Found XDS.INP in: {subdir}")
            transform_xds_inp_auto_template(
                inp_path, out_path, raw_data_base_dir,
                prefix_hint=prefix_hint,
                space_group_number=space_group_number,
                unit_cell_constants=unit_cell_constants,
                data_range=data_range,
                spot_range=spot_range
            )
    print("\n Batch processing complete.")

if __name__ == "__main__":
    batch_process_xds_inps(
        root_dir=ROOT_DIR,
        raw_data_base_dir=RAW_DATA_BASE_DIR,
        prefix_hint=PREFIX_HINT,
        space_group_number=SPACE_GROUP_NUMBER,
        unit_cell_constants=UNIT_CELL_CONSTANTS,
        data_range=DATA_RANGE,
        spot_range=SPOT_RANGE
    )
