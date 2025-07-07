import os

# Define max value for loop
max_value = 16
space = "P 6 2 2"
res_cut = 3.0
rfree_cut = 0.6
w = open("dimple_results.dat", "w")
wc = open("dimple_results_filtered.dat", "w")
w.write("ID; CRYSTAL;RES;Rfree\n")
wc.write("ID; CRYSTAL;RES;Rfree\n")

# Loop through main folder 
for i in range(1, max_value + 1):
    print(f"00000000000000000000000000 PROCESSING 0000000000000000000000000000000")
    folder = f"POS{i}"
    
    # Check if the folder exists
    if not os.path.exists(folder):
        print(f"Folder {folder} not found, moving to the next folder.")
        continue
    
    # Iterate over the root directory, its subdirectories, and files
    for root, dirs, files in os.walk(folder):
        # Iterate over subdirectories (dir1, dir2, ...)
        for directory in dirs:
            # Construct the path to the subdirectory
            subdirectory_path = os.path.join(root, directory)
            
            # Perform operations on subdirectories if needed
            
        # Iterate over files
        for file in files:
            # Construct the path to the file
            file_path = os.path.join(root, file)
            
            # Perform operations on files if needed
            if file == "final.pdb":
                try:
                    with open(file_path, "r") as f:
                        lines = f.readlines()
                        cryst = res = rfree = ""
                        for line in lines:
                            if "CRYST" in line:
                                cryst = line.strip()
                            elif "RESOLUTION RANGE HIGH" in line:
                                res = line.split(":")[1].strip()
                            elif "FREE R VALUE" in line:
                                rfree = line.split(":")[1].strip()
                        
                        # Write data to dimple_results.dat
                        w.write(f"{i};{cryst};{res};{rfree}\n")
                        
                        # Perform additional filtering and write to dimple_results_filtered.dat
                        if space in cryst and float(res) <= res_cut and float(rfree) <= rfree_cut:
                            wc.write(f"{i};{cryst};{res};{rfree}\n")
                except FileNotFoundError:
                    continue

# Close files
w.close()
wc.close()

# Reporter message
print("================================================")   
print("=====================Done=======================")
print("================================================")

