# crystal_pipeline.py

This script runs XDS -> CCP4 (`pointless`, `aimless`, `ctruncate`, `freerflag`) and optionally DIMPLE for all datasets under one visit.

## Warning

Before running this script, make sure the raw-data tree and processed-data tree use the same relative folder layout.
Do **not** move, rename, or delete files or folders under `RAW_DATA_BASE_DIR` or `ROOT_DIR` while the script is running, because recursive directory traversal can otherwise produce confusing partial results.
If your raw and processed folder trees do not match, stop and talk to the script maintainer before using this script.

## Required paths

### `RAW_DATA_BASE_DIR`

Set this to the absolute path containing the raw diffraction images (`.cbf.gz`) for the run or set of runs.
Under this folder, you should have one subfolder tree per dataset or collection, and that tree must match the processed-data layout under `ROOT_DIR`.
A typical example is:

```text
/Data/Obelix_DataSafe2/BeamlineData/EMBL/20260425/RAW_DATA/CC464A/
```

Best practice is to keep a stable directory hierarchy, for example a protein directory before the puck directory, and then let the script iterate through all puck subfolders.

Example layouts:

```text
RAW_DATA_BASE_DIR/
├── dataset1/*.cbf.gz
└── dataset2/*.cbf.gz
```

or

```text
RAW_DATA_BASE_DIR/
└── Puck01/
    ├── Pin03/DS1/*.cbf.gz
    └── Pin04/DS2/*.cbf.gz
```

### `ROOT_DIR`

Set this to the absolute path containing the processed data you want the script to work on.
The script searches **recursively** under this folder for XDS processing directories, defined as any folder containing `XDS.INP`.
This means the script will find datasets no matter how many folder levels you use, such as visit, proposal, puck, pin, dataset, or `xds_*` subdirectories.

Example layouts:

```text
ROOT_DIR/
├── dataset1/xds_run/XDS.INP
└── dataset2/xds_run/XDS.INP
```

or

```text
ROOT_DIR/
└── Puck01/
    ├── Pin03/DS1/xds_run/XDS.INP
    └── Pin04/DS2/xds_run/XDS.INP
```

## Folder-layout rule

This script depends on matching **relative paths** between `ROOT_DIR` and `RAW_DATA_BASE_DIR`.
For each dataset, the relative path below `ROOT_DIR` must be the same as the relative path below `RAW_DATA_BASE_DIR`.

Example:

```text
ROOT_DIR/Puck01/Pin03/DS1/xds_run/XDS.INP
RAW_DATA_BASE_DIR/Puck01/Pin03/DS1/*.cbf.gz
```

If your raw and processed folders do not follow the same subfolder layout, this script will not find the correct raw images automatically.
If your layout does **not** look like this, stop and contact the script maintainer.

## `PREFIX_HINT` (optional)

Only change this if you know your image filenames.
If all images from a dataset start with a common prefix and there are other `.cbf.gz` files in the same folder, set `PREFIX_HINT` to that prefix.

Example:

```text
TRIM72_00001.cbf.gz  ->  PREFIX_HINT = "TRIM72_"
```

If you are not sure, leave this as `None`.

## `MODE`

Available modes:

- `"full"`: rewrite `XDS.INP`, run XDS, run CCP4, and optionally DIMPLE.
- `"aimless-only"`: skip XDS and run CCP4, and optionally DIMPLE.
- `"dimple-only"`: run DIMPLE only on existing `Final_with_FreeR.mtz` files.

## Processing order

The script walks the directory tree recursively using `os.walk()`.
The order returned by `os.walk()` is not something users should treat as meaningful unless directory and file names are explicitly sorted in code.
Because of that, the summary file may not list datasets in the order you expect.

## Practical notes

- Use absolute paths.
- Avoid spaces or hyphens in newly created file or folder names; underscores are safer.
- Do not reorganize the copied beamline directory tree unless you also preserve the raw/processed path mapping exactly.
- This is a lab utility script with strict assumptions; if those assumptions are violated, failures are expected rather than surprising.
