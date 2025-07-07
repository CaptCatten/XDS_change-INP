import os
import glob

# Parameters
space = "P 6 2 2"
res_cut = 3.0
rfree_cut = 0.6
prefix = "POS*"

# Output files
with open("dimple_results.dat", "w") as w, open("dimple_results_filtered.dat", "w") as wc:
    w.write("ID;CRYSTAL;RES;Rfree\n")
    wc.write("ID;CRYSTAL;RES;Rfree\n")

    # Dynamically find all folders starting with "POS"
    for folder in sorted(glob.glob(prefix)):
        if not os.path.isdir(folder):
            continue
        print(f"==================== PROCESSING {os.path.abspath(folder)} ====================")

        # Walk through all subdirectories and files
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file == "final.pdb":
                    file_path = os.path.join(root, file)
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

                            # Write to results
                            w.write(f"{folder};{cryst};{res};{rfree}\n")

                            # Apply filters and write to filtered file
                            if space in cryst and float(res) <= res_cut and float(rfree) <= rfree_cut:
                                wc.write(f"{folder};{cryst};{res};{rfree}\n")
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
                        continue

# Final message
print("================================================")   
print("===================== Done =====================")
print("================================================")
