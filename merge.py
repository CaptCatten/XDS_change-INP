import os
import subprocess

# Define max value for loop
max_value = 16

# Loop through folders
for i in range(1, max_value + 1):
    print("00000000000000000000000000 PROCESSING {i} 0000000000000000000000000000000")
    folder = f"POS{i}"
    
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
            
            # Run CCP4 programs
            print(f"Running ccp4 {i}")
            os.system("/home/bothe/Programs/ccp4-7.0/bin/pointless XDS_ASCII.HKL")
            os.system("/home/bothe/Programs/ccp4-7.0/bin/pointless -copy XDS_ASCII.HKL hklout XDS_ASCII.mtz")
            os.system("/home/bothe/Programs/ccp4-7.0/bin/aimless HKLIN XDS_ASCII.mtz HKLOUT Merged.mtz XMLOUT XDS.xml ONLYMERGE --no-input")
            print("end")
            # Exit subfolder
            os.chdir('..')
    
    # Exit folder
    os.chdir('..')

    # Reporter message
    print("================================================")   
    print(f"Finished processing files in folder {folder}")
    print("================================================")
