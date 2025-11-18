import os
import re
import shutil

#variable list if you do not want to change, leave as None. Keep in mind everything is case sensitive. when dealing with path always use absolute path. 
RAW_DATA_BASE_DIR = "/media/lauren/T7/trim72" # Path of your raw data root directory, yes potentioally it should work if you do not copy the data over but I have not tested that
ROOT_DIR = "/media/lauren/T7/trim72_XDS_test" # Path of your processed data set. ALWAYS leave the back up in obelix alone. that way if you encounter a bug, you have a back up
PREFIX_HINT = None # if your dataset have a common prefix, or you have a unique identifyer that you want only that one processed
SPACE_GROUP_NUMBER = None # If you change this, change the unit cell constants, or XDS will produce an error 
UNIT_CELL_CONSTANTS = None
DATA_RANGE = None 
SPOT_RANGE = None


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
                print(f" Found file: {file} in {root}")
                # e.g. TRIM72-TRIM72_09_1_00001.cbf.gz -> TRIM72-TRIM72_09_1_?????.cbf.gz
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
    print(f"\n Processing file: {input_path}")
    print(f" Dataset id inferred: {dataset_id}")

    try:
        name_template_path = find_name_template_in_raw_data(
            raw_data_base_dir, dataset_id, prefix_hint
        )
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

        if stripped_line.startswith("GENERIC_LIB=") or stripped_line.startswith("LIB="):
            print("Removing GENERIC_LIB / LIB line")
            continue

        if stripped_line.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            print("Commenting out MAXIMUM_NUMBER_OF_JOBS")
            new_lines.append(f"!{line}" if not stripped_line.startswith("!") else line)
            continue

        if stripped_line.startswith("SPOT_RANGE="):
            print("Replacing SPOT_RANGE")
            new_lines.append(f"SPOT_RANGE= {spot_range}\n" if spot_range else line)
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

    if space_group_number is not None and not has_space_group:
        print("Appending SPACE_GROUP_NUMBER")
        new_lines.append(f"\nSPACE_GROUP_NUMBER= {space_group_number}\n")

    if unit_cell_constants is not None and not has_unit_cell:
        print("Appending UNIT_CELL_CONSTANTS")
        new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")

    backup_path = input_path.replace("XDS.INP", "XDS_org.INP")
    shutil.copy2(input_path, backup_path)
    print(f" Backed up original to: {backup_path}")

    with open(input_path, 'w') as f:
        f.writelines(new_lines)
    print(f" Overwritten: {input_path}")


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

            # dataset_id = first folder under ROOT_DIR (just the number, e.g. '9')
            rel_path = os.path.relpath(subdir, root_dir)
            dataset_id = rel_path.split(os.sep)[0]

            print(f" Found XDS.INP in: {subdir} (dataset_id = {dataset_id})")

            transform_xds_inp_auto_template(
                inp_path,
                raw_data_base_dir,
                dataset_id=dataset_id,
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


