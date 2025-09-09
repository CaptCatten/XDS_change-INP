import os

# ====== USER SETTINGS ======
PROCESSED_ROOT = '/home/napasornnilparuk/p97/EMBL_20240425/PROCESSED_DATA'  # Where the XDS.INP folders are
RAW_DATA_ROOT = '/Data/Obilix_DataSafe2/BeamlineData/EMBL/20240425/RAW_DATA'  # Where *.cbf.gz files are located
PREFIX = 'SHP-'  # Folder prefix to target
TARGET_FILE = "XDS.INP"
# ============================

def find_raw_data_template_path(search_root, prefix):
    """
    Find the first .cbf.gz file under the raw data root matching the prefix.
    Constructs the path with '?????.cbf.gz' wildcard for XDS.
    """
    for dirpath, _, filenames in os.walk(search_root):
        for fname in filenames:
            if fname.endswith(".cbf.gz") and prefix in fname:
                full_path = os.path.join(dirpath, fname)
                base = os.path.basename(fname)
                # Extract static part before 5-digit number
                parts = base.split('_')
                if len(parts) >= 3 and parts[-1][:5].isdigit():
                    parts[-1] = '?????.cbf.gz'
                    wildcard_name = '_'.join(parts)
                    template_path = os.path.join(dirpath, wildcard_name)
                    return f"NAME_TEMPLATE_OF_DATA_FRAMES= {template_path}\n"
    return None

def process_xds_input(file_path, dynamic_name_template):
    """
    Modifies the XDS.INP file in-place, applying necessary changes.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    modified = False
    for i, line in enumerate(lines):
        if line.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            lines[i] = dynamic_name_template
            modified = True
        elif line.startswith("UNIT_CELL_CONSTANTS=") or \
             line.startswith("LIB=") or \
             line.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            lines[i] = "!" + line
            modified = True
        elif line.startswith("SPACE_GROUP_NUMBER= 96"):
            lines[i] = "SPACE_GROUP_NUMBER= 0\n"
            modified = True

    if modified:
        backup_file = file_path + ".bak"
        os.rename(file_path, backup_file)
        with open(file_path, 'w') as file:
            file.writelines(lines)
        print(f"Modified: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def main():
    for root, dirs, _ in os.walk(PROCESSED_ROOT):
        for folder in dirs:
            if folder.startswith(PREFIX):
                folder_path = os.path.join(root, folder)
                print(f"\nProcessing folder: {folder_path}")

                for subfolder in os.listdir(folder_path):
                    subfolder_path = os.path.join(folder_path, subfolder)
                    if not os.path.isdir(subfolder_path):
                        continue

                    file_path = os.path.join(subfolder_path, TARGET_FILE)
                    if not os.path.isfile(file_path):
                        print(f"Skipped (no XDS.INP): {subfolder_path}")
                        continue

                    # Get full dynamic name template for this folder
                    dynamic_name_template = find_raw_data_template_path(RAW_DATA_ROOT, folder)
                    if not dynamic_name_template:
                        print(f"Raw data file for {folder} not found, skipping.")
                        continue

                    try:
                        process_xds_input(file_path, dynamic_name_template)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    main()
