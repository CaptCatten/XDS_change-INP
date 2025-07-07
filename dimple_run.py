import os
from shutil import copyfile
import subprocess, sys
import glob

# Define folder prefix
prefix = "POS"

# Find all folders matching the prefix
pos_folders = sorted(glob.glob(f"{prefix}*"))

# Loop through found folders
for folder in pos_folders:
    print(f"00000000000000000000000000 PROCESSING {folder} 0000000000000000000000000000000")
    
    # Change directory to the current folder
    try:
        os.chdir(folder)
    except FileNotFoundError:
        print(f"Folder {folder} not found, moving to the next folder.")
        continue

    # Subfolder looping
    for subfolder in os.listdir():
        if os.path.isdir(subfolder):
            try:
                os.chdir(subfolder)
            except FileNotFoundError:
                print(f"Subfolder {subfolder} not found, moving to the next subfolder.")
                continue
                print("processing in subfolder")
            MTZIN = "Merged.mtz"
            PDBIN = "/Data/1TB_SSD/X-ray/p97/SHP_follow_up/PROCESSED_DATA/p97ND1_new.pdb"
            dimple = ["dimple", PDBIN, MTZIN, "-M0", "-s", "DIMPLE_OUT"]
            logfile = open('dimple.log', 'w')
            proc = subprocess.Popen(dimple, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in proc.stdout:
                sys.stdout.write(str(line))
                logfile.write(str(line))
            proc.wait()
            logfile.close()
            print("end")
            # Exit subfolder
            os.chdir('..')

    # Exit folder
    os.chdir('..')

# Reporter message
print("================================================")   
print(f"Finished processing all {prefix} folders")
print("================================================")
