the most current script is crystal_pipeline.py

HOW TO USE THIS SCRIPT (READ THIS FIRST)

This script runs XDS -> CCP4 (pointless/aimless/ctruncate/freerflag)
and optionally DIMPLE for ALL datasets under one visit.

You MUST set these paths correctly:
1) RAW_DATA_BASE_DIR
   - Folder that contains your RAW diffraction images (.cbf.gz) for THIS visit.
   - Under this folder you should see the SAME subfolders as under ROOT_DIR,
      e.g.:
          RAW_DATA_BASE_DIR/
              06/DS1/*.cbf.gz
              06/DS2/*.cbf.gz
              07/DS1/*.cbf.gz
    - Set this to where you rsynced the RAW_DATA from the synchrotron.

 2) ROOT_DIR
    - TOP folder of your processed data for THIS visit.
    - The script will search UNDER this folder for XDS processing directories
      (folders that contain XDS.INP), e.g.:
          ROOT_DIR/
              06/DS1/xds_.../XDS.INP
              06/DS2/xds_.../XDS.INP
              07/DS1/xds_.../XDS.INP

    - Set this to where your XDS runs live for the visit.

 IMPORTANT: folder layout must match
    For each dataset, the subfolder layout under ROOT_DIR and RAW_DATA_BASE_DIR
    MUST be the same. If you have:
        ROOT_DIR/06/DS1/xds_.../XDS.INP
    the script will look for images in:
        RAW_DATA_BASE_DIR/06/DS1/*.cbf.gz

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
