import os
#DO NOT MOVE ANY FILES VIA THE UI WHEN THE CODE IS RUNNING!!!
#this will not run XDS it will only changes the XDS input file. 
# Define the root directory
root_dir = '/home/napasornnilparuk/p97/EMBL_20240425/PROCESSED_DATA'  # Change this to the root directory where your folders are located
Prefix = 'SHP-'

# Loop through folders and subfolders
for root, dirs, files in os.walk(root_dir):
    for folder in dirs:
        if folder.startswith(Prefix): #change this parametre to the suitable file initial. The rest will be left bank so the scrip will loop to all the files with that initial. 
            print(f"Processing folder: {folder}")
            folder_path = os.path.join(root, folder)
            # You do not need the max loop number. os.walk will find the files that have the initial by itself :3 
            # Change directory to the current folder
            try:
                os.chdir(folder_path)
            # Do not remove the part below. It is for debuggig. Most likely occured if the script is running but the file is missing between os.walk finding the file and ch.dir
            except FileNotFoundError:
                print(f"Folder {folder} not found, moving to the next folder.") 
                continue # Safe loop exit without termination

            # Subfolder looping
            for subfolder in os.listdir():
                subfolder_path = os.path.join(folder_path, subfolder)
                if os.path.isdir(subfolder_path):
                    try:
                        os.chdir(subfolder_path)
                    # Do not remove the part below. It is for debuggig. Most likely occured if the script is running but the file is missing between os.walk finding the file and ch.dir
                    except FileNotFoundError:
                        print(f"Subfolder {subfolder} not found, moving to the next subfolder.")
                        continue # Safe loop exit without termination

                    # Define the file path
                    file_path = os.path.join(subfolder_path, "XDS.INP") # Make sure this subfolder name is this, if not change it to the appropiate name

                    # Read the file
                    with open(file_path, 'r') as file:
                        lines = file.readlines()

                    # Make changes
                    for j in range(len(lines)):  
                        if lines[j].startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
                            lines[j] = "NAME_TEMPLATE_OF_DATA_FRAMES= /Data/Obilix_DataSafe2/BeamlineData/EMBL/20240425/RAW_DATA/SHP-202_DS/SAMI-SHP-202_1_?????.cbf.gz\n" 
                            #change this to the full path of your data, case-sensitive. This will calls the files into the current folder that the script is running. 
                        elif lines[j].startswith("UNIT_CELL_CONSTANTS=") or \
                                lines[j].startswith("LIB=") or \
                                lines[j].startswith("MAXIMUM_NUMBER_OF_JOBS="):
                            lines[j] = "!" + lines[j]
                        elif lines[j].startswith("SPACE_GROUP_NUMBER= 96"): #change the space group to the one appears in the RAW XDS and not from the IspYB!!!
                            lines[j] = "SPACE_GROUP_NUMBER= 0\n"

                    # Write changes back to the file
                    with open(file_path, 'w') as file:
                        file.writelines(lines)

                    os.chdir(root_dir)  # Change back to the root directory

            print(f"Finished processing files in folder {folder}")

