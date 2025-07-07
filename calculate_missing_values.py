import os
from shutil import copyfile
import subprocess, sys
#space="I 41 2 2"
#res_cut=3.0
#rfree_cut=0.30

home=os.getcwd()
folders=os.listdir(home)

for i in folders:
  if "." not in i:
    os.chdir(i)
    os.system("mv original.mtz final.mtz")
    logfile = open('uniqueify.log', 'w')
    proc=subprocess.Popen(["uniqueify", "-f", "FreeR_flag", "final.mtz", "final_unique.mtz"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.write(str(line))
        logfile.write(str(line))
    proc.wait()
    logfile.close()
    print(i)
    res = 0
    f = open("final.pdb", "r")
    lines = f.readlines()
    for j in lines:
        if "RESOLUTION RANGE HIGH (ANGSTROMS) :" in j:
            res = str(float(j.split(":")[1]))
            print(i, res)
    w = open("cad.input", "w")
    w.write("monitor BRIEF\nlabin file 1 - \nALL\nresolution file 1 999.0 "+res)
    w.close()

    w = open("cad.sh", "w")
    w.write("cad hklin1 final_unique.mtz hklout OUTPUT.mtz < cad.input")
    w.close()

    logfile = open('cad.log', 'w')
    proc=subprocess.Popen(["bash", "cad.sh"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.write(str(line))
        logfile.write(str(line))
    proc.wait()
    logfile.close()

    logfile = open('phenix.log', 'w')
    proc=subprocess.Popen(["/nfs/apps_new/phenix/phenix-1.19.2-4158/build/bin/phenix.maps", "final.pdb", "OUTPUT.mtz"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.write(str(line))
        logfile.write(str(line))
    proc.wait()
    logfile.close()

    os.chdir(home)
    


    
                

            
                
    
    
