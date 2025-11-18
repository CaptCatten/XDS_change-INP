#!/bin/bash

# Use an absolute path to avoid some funny business. (I am sorry this is all I know how to do) 
ROOT="/media/lauren/T7/trim72_XDS_test" # Change this to where your XDS.INP is
PYTHON_SCRIPT="/media/lauren/T7/trim72_XDS_test/XDS_mod.py"   # Change to the absolute path of the python script location

echo "=== Starting full pipeline ==="
echo "Root directory: $ROOT"
echo

find "$ROOT" -type f -name "XDS.INP" | while read -r inp; do
    dir=$(dirname "$inp")
    echo "Processing dataset in: $dir"

    # 1) Run Python script to modify XDS.INP
    python3 "$PYTHON_SCRIPT" "$dir/XDS.INP"
    echo " → Modified XDS.INP"

    # 2) Run xds_par
    (
        cd "$dir" || exit
        xds_par
    )
    echo " → xds_par finished"
    echo
done

echo "=== Pipeline complete ==="

