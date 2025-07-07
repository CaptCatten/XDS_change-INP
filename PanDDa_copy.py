import os
import shutil

# Define the base paths
base_path = "/Data/1TB_SSD/X-ray/p97/Covalent/CPS6191_jun_2023"
panDDA_run_path = os.path.join(base_path, "PanDDA_run")
dimple_file_path = "dimple_results_filtered.dat"

# Create the PanDDA_run directory if it doesn't exist
if not os.path.exists(panDDA_run_path):
    os.makedirs(panDDA_run_path)

# Define the index of the ID column (0-indexed)
id_column_index = 0

# Open the dimple file and skip the header line
with open(dimple_file_path, 'r') as f:
    next(f)  # Skip the header line
    for line in f:
        # Extract the ID from the specified column index
        columns = line.strip().split(";")
        if id_column_index < len(columns):
            id_value = columns[id_column_index]
        else:
            print(f"ID column index {id_column_index} is out of range for line: {line}")
            continue
        
        # Construct the folder path
        folder = f"POS{id_value}"
        folder_path = os.path.join(base_path, folder)
        
        # Check if all three files exist using os.walk
        merged_mtz_src = None
        final_mtz_src = None
        final_pdb_src = None
        files_exist = False
        for root, dirs, files in os.walk(folder_path):
            if "Merged.mtz" in files:
                merged_mtz_src = os.path.join(root, "Merged.mtz")
            if "final.mtz" in files:
                final_mtz_src = os.path.join(root, "final.mtz")
            if "final.pdb" in files:
                final_pdb_src = os.path.join(root, "final.pdb")
            
            if merged_mtz_src and final_mtz_src and final_pdb_src:
                files_exist = True
                break

        if not files_exist:
            print(f"Not all required files found for {folder}")
            continue

        # Create the PanDDA_run/SHP-{i} directory
        panDDA_folder_path = os.path.join(panDDA_run_path, folder)
        if not os.path.exists(panDDA_folder_path):
            os.makedirs(panDDA_folder_path)

        # Copy the three files to PanDDA_run/POS{i}
        shutil.copy(merged_mtz_src, panDDA_folder_path)
        shutil.copy(final_mtz_src, panDDA_folder_path)
        shutil.copy(final_pdb_src, panDDA_folder_path)

        print(f"Files copied to: {panDDA_folder_path}")



