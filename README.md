the most current script is crystal_pipeline.py

HOW TO USE THIS SCRIPT (READ THIS FIRST)

This script runs XDS -> CCP4 (pointless/aimless/ctruncate/freerflag)
and optionally DIMPLE for ALL datasets under one visit.

You MUST set these paths correctly:
/Data/Obelix_DataSafe2/BeamlineData/EMBL/20260425/RAW_DATA/CC464A/# 1) RAW_DATA_BASE_DIR
    - Folder that contains your RAW diffraction images (.cbf.gz) for this run
      (or set of runs).
    - Under this folder you should have one subfolder per dataset / collection,
      and those subfolders should match the processed-data layout under ROOT_DIR.

   Example layouts:
          RAW_DATA_BASE_DIR/
              dataset1/*.cbf.gz
              dataset2/*.cbf.gz

   or, with extra levels (puck / pin / dataset):
          RAW_DATA_BASE_DIR/
              Puck01/Pin03/DS1/*.cbf.gz
              Puck01/Pin04/DS2/*.cbf.gz

   - Set this to the absolute path where your raw images live on your machine.

 2) ROOT_DIR
    - Top-level folder of the processed data you want this script to work on.
    - The script will search RECURSIVELY under this folder for XDS processing
      directories (any folder that contains XDS.INP), no matter how many
      subfolder levels you have (visit, proposal, puck, pin, dataset, etc.).

      Example layouts:
          ROOT_DIR/
              dataset1/xds_.../XDS.INP
              dataset2/xds_.../XDS.INP

      or, with puck/pin levels:
          ROOT_DIR/
              Puck01/Pin03/DS1/xds_.../XDS.INP
              Puck01/Pin04/DS2/xds_.../XDS.INP

    - Set this to the absolute path where your XDS runs are stored. The script
      will walk through all subfolders under ROOT_DIR and try to process every
      dataset it finds.
 IMPORTANT: folder layout must match
    - For each dataset, the relative path under ROOT_DIR and RAW_DATA_BASE_DIR
      must be the same.
      If you have:
          ROOT_DIR/Puck01/Pin03/DS1/xds_.../XDS.INP
      the script will look for images in:
          RAW_DATA_BASE_DIR/Puck01/Pin03/DS1/*.cbf.gz

   - If your raw and processed folders do not follow the same subfolder layout,
      this script will not find the right images automatically.
    If your layout does NOT look like this, STOP and talk to the script maintainer.

 3) PREFIX_HINT (optional)
    - Only touch this if you know your image filenames.
    - If all your images start with a common prefix and there are other .cbf.gz
      files in the same folder, set PREFIX_HINT to that prefix, e.g.:
          TRIM72_00001.cbf.gz -> PREFIX_HINT = "TRIM72_"
    - If you are not sure, LEAVE THIS AS None.

 4) MODE
    - "full":        rewrite XDS.INP, run XDS, run CCP4, (optional) DIMPLE
    - "aimless-only":skip XDS, only run CCP4 (and optional DIMPLE)
    - "dimple-only": only run DIMPLE on existing Final_with_FreeR.mtz

 While this script is running:
    DO NOT move, rename, or delete files or folders under RAW_DATA_BASE_DIR
    or ROOT_DIR. You will get confusing errors and half-finished results.

Unfortunately the summary will not arrange the dataset, this is because the function
os.walk() will take the file it can find first.
