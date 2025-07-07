import os
import re

def build_dynamic_name_template(data_folder, raw_data_base_dir, prefix_hint=None):
    search_base = os.path.join(raw_data_base_dir, data_folder)
    print(f"🔍 Searching in: {search_base}")
    for root, _, files in os.walk(search_base):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                print(f"✅ Found file: {file} in {root}")
                wildcard_file = re.sub(r"\d+\.cbf\.gz$", "?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)
    raise FileNotFoundError(f"No matching .cbf.gz file found under {search_base} with prefix '{prefix_hint}'")

def transform_xds_inp_auto_template(
    input_path, output_path, data_folder, raw_data_base_dir,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    print(f"\n🛠 Processing file: {input_path}")
    
    try:
        name_template_path = build_dynamic_name_template(data_folder, raw_data_base_dir, prefix_hint)
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
            if spot_range:
                new_lines.append(f"SPOT_RANGE={spot_range}\n")
            else:
                new_lines.append(line)
            continue

        if stripped.startswith("DATA_RANGE="):
            if data_range:
                new_lines.append(f"DATA_RANGE={data_range}\n")
            else:
                new_lines.append(line)
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
    print(f"✅ Written modified file: {output_path}")

def batch_process_xds_inps(
    root_dir,
    raw_data_base_dir,
    folder_mapping,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None
):
    print(f"\n🔁 Starting batch processing in: {root_dir}\n")
    for subdir, _, files in os.walk(root_dir):
        if "XDS.INP" in files:
            folder_key = os.path.basename(subdir)
            if folder_key not in folder_mapping:
                print(f"⚠ No mapping found for {folder_key} — skipping")
                continue
            data_folder = folder_mapping[folder_key]
            inp_path = os.path.join(subdir, "XDS.INP")
            out_path = os.path.join(subdir, "XDS_modified.INP")
            print(f"📂 Found XDS.INP in: {subdir}")
            transform_xds_inp_auto_template(
                inp_path, out_path, data_folder, raw_data_base_dir,
                prefix_hint=prefix_hint,
                space_group_number=space_group_number,
                unit_cell_constants=unit_cell_constants,
                data_range=data_range,
                spot_range=spot_range
            )
    print("\n✅ Batch processing complete.")
