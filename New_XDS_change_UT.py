import os
import re

def find_name_template(base_dir, prefix_hint=None):
    print(f"Searching for .cbf.gz file in: {base_dir}")
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".cbf.gz"):
                if prefix_hint is None or file.startswith(prefix_hint):
                    print(f"Found .cbf.gz file: {file} in {root}")
                    wildcard_file = re.sub(r"\d{5}\.cbf\.gz$", "?????.cbf.gz", file)
                    name_template = os.path.join(root, wildcard_file)
                    print(f"Generated NAME_TEMPLATE: {name_template}")
                    return name_template
    raise FileNotFoundError(f"No matching .cbf.gz file found under {base_dir}.")

def transform_xds_inp_auto_template(
    input_path, output_path, base_data_dir, 
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    print(f"\n Processing file: {input_path}")
    
    try:
        name_template_path = find_name_template(base_data_dir, prefix_hint)
    except FileNotFoundError as e:
        print(f"{e}")
        return

    with open(input_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()

        # NAME_TEMPLATE
        if stripped.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            print(f"Replacing NAME_TEMPLATE_OF_DATA_FRAMES")
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES={name_template_path}\n")
            continue

        # DETECTOR swap
        if stripped.startswith("DETECTOR= PILATUS"):
            print(f"Replacing DETECTOR line with EIGER")
            new_lines.append("DETECTOR= EIGER\n")
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            continue

        # FRIEDEL'S_LAW
        if stripped.startswith("FRIEDEL'S_LAW="):
            print(f"Changing FRIEDEL'S_LAW to TRUE")
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        # STRONG_PIXEL comment
        if re.match(r"^STRONG_PIXEL\s*=", stripped):
            print(f"Commenting out STRONG_PIXEL line")
            new_lines.append(f"!{line}" if not line.lstrip().startswith("!") else line)
            continue

        # SPOT_RANGE
        if stripped.startswith("SPOT_RANGE="):
            print(f"change SPOT_RANGE to {spot_range}")
            new_lines.append(f"SPOT_RANGE={spot_range}\n")
            continue
            
        # DATA_RANGE
        if stripped.startswith("DATA_RANGE="):
            print(f"change DATA_RANGE to {data_range}")
            new_lines.append(f"DATA_RANGE={data_range}\n")
            continue

        # SPACE_GROUP_NUMBER
        if stripped.startswith("SPACE_GROUP_NUMBER=") and space_group_number is not None:
            print(f"Replacing SPACE_GROUP_NUMBER with {space_group_number}")
            new_lines.append(f"SPACE_GROUP_NUMBER={space_group_number}\n")
            continue

        # UNIT_CELL_CONSTANTS
        if stripped.startswith("UNIT_CELL_CONSTANTS=") and unit_cell_constants is not None:
            print(f"Replacing UNIT_CELL_CONSTANTS with {unit_cell_constants}")
            new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")
            continue

        new_lines.append(line)

    with open(output_path, 'w') as f:
        f.writelines(new_lines)
    print(f"Written modified file: {output_path}")

def batch_process_xds_inps(base_dir, prefix_hint=None, space_group_number=None, unit_cell_constants=None, data_range=None, spot_range=None):
    print(f"\n Starting batch processing in: {base_dir}\n") 
    for subdir, _, files in os.walk(base_dir):
        if "XDS.INP" in files:
            inp_path = os.path.join(subdir, "XDS.INP")
            out_path = os.path.join(subdir, "XDS_modified.INP")
            print(f"\n Found XDS.INP in: {subdir}")
            transform_xds_inp_auto_template(
                inp_path, out_path, subdir,
                prefix_hint=prefix_hint,
                space_group_number=space_group_number,
                unit_cell_constants=unit_cell_constants,
                data_range=data_range,
                spot_range=spot_range
            )
    print(f"\n Batch processing complete.")

# ==== USER CONFIG ====
base_directory = "/media/napasornnilparuk/T7/trim72/"

# Optional parameters — set to None if not needed
prefix_hint = "TRIM72-TRIM72_04_3_" # Add the prefix of file
space_group_number = "0"  # change to the desired space group
unit_cell_constants = "70 80 90 90 90 90"  # change to the correct constants based on the space group
spot_range = "1 3600" #change to the desire spot range
data_range = "1 3600" #change to the desire data range

batch_process_xds_inps(
    root_directory,
    prefix_hint=prefix_hint,  
    space_group_number=space_group_number,
    unit_cell_constants=unit_cell_constants,
    data_range=data_range,
    spot_range=spot_range
)
