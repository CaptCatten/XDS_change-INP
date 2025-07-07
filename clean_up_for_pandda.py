
import os
import shutil

def navigate_and_rename(src):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        if os.path.isdir(s):
            navigate_and_rename(s)
        elif s.endswith(".pdb"): 
            shutil.copy(s, os.path.join(src, "OUTPUT.pdb"))    

dir_src = "/Data/1TB_SSD/X-ray/p97/Covalent/CPS6191_jun_2023/PanDDA_run"
navigate_and_rename(dir_src)
