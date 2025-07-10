import os
import re

# --- User Configuration ---
# If you do not want change, keep the variable as "None"
RAW_DATA_BASE_DIR = "/media/lauren/T7/trim72"        
PREFIX_HINT = None                              
SPACE_GROUP_NUMBER = "REEEEEE"                      
UNIT_CELL_CONSTANTS = "REEEEE"                    
DATA_RANGE = "REEEEEE"                              
SPOT_RANGE = "REEEEEEE"                              
ROOT_DIR = "/media/lauren/T7/trim72_XDS_test"              

def find_name_template_in_raw_data(raw_data_base_dir, prefix_hint=None):
    print(f" Searching in: {raw_data_base_dir}")
    for root, _, files in os.walk(raw_data_base_dir):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                print(f" Found file: {file} in {root}")
                wildcard_file = re.sub(r"\d+\.cbf\.gz$", "?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)
    raise FileNotFoundError(f"No matching .cbf.gz file found under {raw_data_base_dir} with prefix '{prefix_hint}'")

# (unchanged code above)...

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
        print(f"{e}")
        return

    with open(input_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    has_space_group = False
    has_unit_cell = False

    for line in lines:
        stripped_line = line.lstrip()

        if stripped_line.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            print("Replacing NAME_TEMPLATE_OF_DATA_FRAMES")
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_template_path}\n")
            continue

        if stripped_line.startswith("DETECTOR=") and "PILATUS" in stripped_line:
            print("Replacing DETECTOR with EIGER")
            new_lines.append("DETECTOR= EIGER\n")
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            continue

        if stripped_line.startswith("FRIEDEL'S_LAW="):
            print("Forcing FRIEDEL'S_LAW=TRUE")
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        if stripped_line.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            print("Commenting out MAXIMUM_NUMBER_OF_JOBS")
            new_lines.append(f"!{line}" if not line.lstrip().startswith("!") else line)
            continue

        if stripped_line.startswith("SPOT_RANGE="):
            print("Replacing SPOT_RANGE")
            new_lines.append(
f"SPOT_RANGE= {spot_range}\n" if spot_range else line)
            continue

        if stripped_line.startswith("DATA_RANGE="):
            print("Replacing DATA_RANGE")
            new_lines.append(f"DATA_RANGE= {data_range}\n" if data_range else line)
            continue

        if stripped_line.startswith("SPACE_GROUP_NUMBER="):
            has_space_group = True

        if stripped_line.startswith("UNIT_CELL_CONSTANTS="):
            has_unit_cell = True

        new_lines.append(line)

    # Append new parameters only if provided and not already present
    if space_group_number is not None and not has_space_group:
        print("Appending SPACE_GROUP_NUMBER")
        new_lines.append(f"\nSPACE_GROUP_NUMBER= {space_group_number}\n")

    if unit_cell_constants is not None and not has_unit_cell:
        print("Appending UNIT_CELL_CONSTANTS")
        new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")

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
