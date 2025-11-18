#!/bin/bash

ROOT="/media/lauren/T7/trim72_XDS_test"
PYTHON_SCRIPT="/media/lauren/T7/trim72_XDS_test/XDS_mod.py"   # <-- CHANGE THIS TO THE REAL LOCATION

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

