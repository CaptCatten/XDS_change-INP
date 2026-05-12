import os
import re
import shutil
import subprocess
from dataclasses import dataclass

# ============================================================
# USER CONFIGURATION
# If you do not want to change a parameter, leave as None.
# Paths should be absolute.
# When naming files or folder please do not use space or hyphens
# Underscore is the safest option as always
# ============================================================


# Optional space group / cell (if known)
# If you change this, also change the unit cell constants,
# or XDS will produce an error.
SPACE_GROUP_NUMBER = None
UNIT_CELL_CONSTANTS = None

DATA_RANGE = "1 3600"
SPOT_RANGE = "1 3600"
DETECTOR_TYPE = "EIGER"   # "EIGER", "PILATUS", or None

# Path to CCP4 setup script for pointless/aimless/ctruncate/freerflag
# if you are using the work station copy the path below
# "/usr/local/ccp4/ccp4-8.0/bin/ccp4.setup-sh"
CCP4_SETUP = "/opt/xtal/ccp4-9/bin/ccp4.setup-sh"

DIMPLE_PDB = "/path/to/reference_model.pdb"   # None to skip DIMPLE
DIMPLE_OUTDIR = "dimple_out"

# Pipeline mode
MODE = "full"   # "full", "aimless-only", "dimple-only"

# Timeouts
XDS_TIMEOUT_SECONDS = 3600
CCP4_TIMEOUT_SECONDS = 1800
DIMPLE_TIMEOUT_SECONDS = 3600

# Summary file
SUMMARY_FILE = os.path.join(ROOT_DIR, "summary.txt")

# In aimless-only mode: which file triggers CCP4?
#   - If this is *.HKL  → start from HKL, run pointless + aimless.
#   - If this is *.mtz  → start from MTZ, run aimless only.
AIMLESS_INPUT_FILE = "XDS_ASCII.HKL"

# Debug flag: show subprocess output if True
DEBUG = False

# ============================================================
# ===== DO NOT CHANGE ANYTHING FROM THIS POINT ONWARDS =======
# ============================================================

# if you do and things break, I might not know how to fix it..

# ============================================================
# ENVIRONMENT
# ============================================================

@dataclass
class PipelineEnv:
    raw_data_base_dir: str
    root_dir: str
    prefix_hint: str | None
    space_group_number: int | None
    unit_cell_constants: str | None
    data_range: str | None
    spot_range: str | None
    detector_type: str | None
    ccp4_setup: str
    dimple_pdb: str | None
    dimple_outdir: str
    xds_timeout: int
    ccp4_timeout: int
    dimple_timeout: int
    summary_file: str
    aimless_input_file: str
    debug: bool = False


ENV = PipelineEnv(
    raw_data_base_dir=RAW_DATA_BASE_DIR,
    root_dir=ROOT_DIR,
    prefix_hint=PREFIX_HINT,
    space_group_number=SPACE_GROUP_NUMBER,
    unit_cell_constants=UNIT_CELL_CONSTANTS,
    data_range=DATA_RANGE,
    spot_range=SPOT_RANGE,
    detector_type=DETECTOR_TYPE,
    ccp4_setup=CCP4_SETUP,
    dimple_pdb=DIMPLE_PDB,
    dimple_outdir=DIMPLE_OUTDIR,
    xds_timeout=XDS_TIMEOUT_SECONDS,
    ccp4_timeout=CCP4_TIMEOUT_SECONDS,
    dimple_timeout=DIMPLE_TIMEOUT_SECONDS,
    summary_file=SUMMARY_FILE,
    aimless_input_file=AIMLESS_INPUT_FILE,
    debug=DEBUG,
)


# ============================================================
# UTILS
# ============================================================

def run_cmd(cmd, cwd, timeout, env: PipelineEnv):
    try:
        if env.debug:
            stdout = None
            stderr = None
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL

        p = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
            text=True,
            timeout=timeout,
        )
        return p.returncode == 0, p.returncode, False
    except subprocess.TimeoutExpired:
        return False, 124, True
    except Exception:
        return False, 125, False


def write_summary_header(summary_path):
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        f.write("dataset\tspace_group\tresolution_A\tdimple_ok\tblobs\n")


def append_summary_line(summary_path, dataset_id, space_group, resolution, dimple_ok, blobs):
    with open(summary_path, "a") as f:
        f.write(f"{dataset_id}\t{space_group}\t{resolution}\t{dimple_ok}\t{blobs}\n")


def print_counter(counts, env: PipelineEnv):
    print(f"\n{'='*52}")
    print(f"  XDS:    {counts['xds_ok']:>4} OK   /  {counts['xds_fail']:>4} FAILED")
    print(f"  CCP4:   {counts['ccp4_ok']:>4} OK   /  {counts['ccp4_fail']:>4} FAILED")
    if env.dimple_pdb is not None:
        print(f"  DIMPLE: {counts['dimple_ok']:>4} OK   /  {counts['dimple_fail']:>4} FAILED")
        print(f"  Blobs:  {counts['blobs_found']:>4} dataset(s) with potential ligand density")
    print(f"{'='*52}\n")


# ============================================================
# DATASET HANDLING
# ============================================================

@dataclass
class Dataset:
    processing_dir: str
    dataset_dir: str
    dataset_rel: str
    dataset_id: str


def derive_dataset_info_from_xds_dir(xds_dir, root_dir) -> Dataset:
    dataset_dir = os.path.dirname(xds_dir)
    dataset_rel = os.path.relpath(dataset_dir, root_dir)
    dataset_id = dataset_rel.replace(os.sep, "_")
    return Dataset(
        processing_dir=xds_dir,
        dataset_dir=dataset_dir,
        dataset_rel=dataset_rel,
        dataset_id=dataset_id,
    )


# ============================================================
# XDS HANDLING
# ============================================================

def find_name_template_in_raw_data(raw_base, dataset_rel, prefix_hint=None):
    search_root = os.path.join(raw_base, dataset_rel)
    if not os.path.isdir(search_root):
        raise FileNotFoundError(f"Raw dataset directory not found: {search_root}")

    for root, _, files in os.walk(search_root):
        for file in files:
            if file.endswith(".cbf.gz") and (prefix_hint is None or file.startswith(prefix_hint)):
                wildcard_file = re.sub(r"_(\d+)\.cbf\.gz$", r"_?????.cbf.gz", file)
                return os.path.join(root, wildcard_file)

    raise FileNotFoundError(f"No matching .cbf.gz found under: {search_root}")


def transform_xds_inp_auto_template(
    inp,
    raw_base,
    dataset_rel,
    prefix_hint=None,
    space_group_number=None,
    unit_cell_constants=None,
    data_range=None,
    spot_range=None,
    detector_type=None,
):
    name_template = find_name_template_in_raw_data(raw_base, dataset_rel, prefix_hint)

    with open(inp, "r") as f:
        lines = f.readlines()

    new_lines = []
    has_sg = False
    has_uc = False
    has_detector = False

    for line in lines:
        s = line.lstrip()

        if s.startswith("NAME_TEMPLATE_OF_DATA_FRAMES="):
            new_lines.append(f"NAME_TEMPLATE_OF_DATA_FRAMES= {name_template}\n")
            continue

        if s.startswith("DETECTOR="):
            has_detector = True
            if detector_type is not None:
                new_lines.append(f"DETECTOR= {detector_type}\n")
                if detector_type.upper() == "EIGER":
                    new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")
            else:
                new_lines.append(line)
            continue

        if detector_type is not None and (
            s.startswith("MINIMUM_VALID_PIXEL_VALUE=") or s.startswith("OVERLOAD=")
        ):
            continue

        if s.startswith("FRIEDEL'S_LAW="):
            new_lines.append("FRIEDEL'S_LAW=TRUE\n")
            continue

        if s.startswith("GENERIC_LIB=") or s.startswith("LIB="):
            continue

        if s.startswith("MAXIMUM_NUMBER_OF_JOBS="):
            new_lines.append("!" + line if not s.startswith("!") else line)
            continue

        if s.startswith("SPOT_RANGE=") and spot_range:
            new_lines.append(f"SPOT_RANGE= {spot_range}\n")
            continue

        if s.startswith("DATA_RANGE=") and data_range:
            new_lines.append(f"DATA_RANGE= {data_range}\n")
            continue

        if s.startswith("SPACE_GROUP_NUMBER="):
            has_sg = True

        if s.startswith("UNIT_CELL_CONSTANTS="):
            has_uc = True

        new_lines.append(line)

    if detector_type is not None and not has_detector:
        new_lines.append(f"\nDETECTOR= {detector_type}\n")
        if detector_type.upper() == "EIGER":
            new_lines.append("MINIMUM_VALID_PIXEL_VALUE=0 OVERLOAD= 239990\n")

    if space_group_number is not None and not has_sg:
        new_lines.append(f"\nSPACE_GROUP_NUMBER= {space_group_number}\n")

    if unit_cell_constants is not None and not has_uc:
        new_lines.append(f"UNIT_CELL_CONSTANTS= {unit_cell_constants}\n")

    backup = inp.replace("XDS.INP", "XDS_org.INP")
    if not os.path.exists(backup):
        shutil.copy2(inp, backup)

    with open(inp, "w") as f:
        f.writelines(new_lines)

    return True


def xds_failed_due_to_low_indexing(folder):
    lp = os.path.join(folder, "IDXREF.LP")
    if not os.path.isfile(lp):
        return False
    try:
        with open(lp) as f:
            txt = f.read()
    except Exception:
        return False
    return "INSUFFICIENT PERCENTAGE" in txt and "INDEXED REFLECTIONS" in txt


def patch_job_defpix_integrate_correct(xds_inp_path):
    with open(xds_inp_path) as f:
        lines = f.readlines()

    new_lines = []
    replaced = False
    for line in lines:
        if line.lstrip().startswith("JOB="):
            new_lines.append("JOB= DEFPIX INTEGRATE CORRECT\n")
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        new_lines.append("\nJOB= DEFPIX INTEGRATE CORRECT\n")

    shutil.copy2(xds_inp_path, xds_inp_path.replace("XDS.INP", "XDS_before_retry.INP"))
    with open(xds_inp_path, "w") as f:
        f.writelines(new_lines)


def run_xds(folder, env: PipelineEnv):
    ok, rc, timed_out = run_cmd(
        ["bash", "-lc", "xds_par > XDS_run.log 2>&1"],
        cwd=folder,
        timeout=env.xds_timeout,
        env=env,
    )

    xds_ascii = os.path.join(folder, "XDS_ASCII.HKL")
    if ok and os.path.isfile(xds_ascii):
        return True

    if xds_failed_due_to_low_indexing(folder):
        folder_name = os.path.basename(os.path.abspath(folder))
        print(f"Low indexing stop for '{folder_name}'; retrying with JOB= DEFPIX INTEGRATE CORRECT")
        try:
            patch_job_defpix_integrate_correct(os.path.join(folder, "XDS.INP"))
        except Exception as e:
            print(f"  Failed to patch XDS.INP: {e}")
            return False

        ok2, rc2, timed_out2 = run_cmd(
            ["bash", "-lc", "xds_par > XDS_retry.log 2>&1"],
            cwd=folder,
            timeout=env.xds_timeout,
            env=env,
        )
        if ok2 and os.path.isfile(xds_ascii):
            return True

        print(f"XDS retry failed for '{folder_name}'")
        print(f"  Check: {os.path.join(folder, 'XDS_retry.log')}")
        return False

    folder_name = os.path.basename(os.path.abspath(folder))
    print(f"XDS failed for '{folder_name}'")
    print(f"  Check: {os.path.join(folder, 'XDS_run.log')}")
    return False


# ============================================================
# CCP4 / AIMLESS PIPELINE
# ============================================================

def parse_aimless_summary(log_path):
    space_group = "UNKNOWN"
    high_res = "UNKNOWN"

    try:
        with open(log_path, "r") as f:
            text = f.read()
    except FileNotFoundError:
        return space_group, high_res

    sg_matches = list(re.finditer(r"Space\s+group\s*[:=]\s*(.+)", text))
    if sg_matches:
        sg_line = sg_matches[-1].group(1).strip()
        sg_line = re.sub(r"\(.*?\)", "", sg_line).strip()
        space_group = sg_line

    res_matches = list(re.finditer(r"High\s+resolution\s+limit\s+([0-9.]+)", text))
    if not res_matches:
        res_matches = list(re.finditer(r"Resolution\s+range\s+[0-9.]+\s+to\s+([0-9.]+)", text))
    if res_matches:
        high_res = res_matches[-1].group(1)

    return space_group, high_res


def run_ccp4_pipeline(folder, env: PipelineEnv, input_mode="hkl", hklin_path=None):
    """
    input_mode:
      - "hkl": use HKL → pointless + aimless + ctruncate + freerflag.
      - "mtz": use MTZ → aimless + ctruncate + freerflag.
    """
    if input_mode == "hkl":
        if hklin_path is None:
            hklin_path = os.path.join(folder, "XDS_ASCII.HKL")
        if not os.path.isfile(hklin_path):
            return None

        bash_cmd = (
            f'source "{env.ccp4_setup}" && '
            'export CCP4_SCR="$PWD/CCP4_SCRATCH" && mkdir -p "$CCP4_SCR" && '
            'rm -f XDS_ASCII.mtz Merged.mtz Truncate.mtz Final_with_FreeR.mtz XDS.xml && '
            f'pointless "{hklin_path}" hklout XDS_ASCII.mtz > pointless.log 2>&1 && '
            'aimless HKLIN XDS_ASCII.mtz HKLOUT Merged.mtz XMLOUT XDS.xml --no-input > aimless.log 2>&1 && '
            "ctruncate -mtzin Merged.mtz -mtzout Truncate.mtz -colin '/*/*/[IMEAN,SIGIMEAN]' > ctruncate.log 2>&1 && "
            'freerflag HKLIN Truncate.mtz HKLOUT Final_with_FreeR.mtz > freerflag.log 2>&1 << EOF\n'
            'FREERFRAC 0.05\n'
            'END\n'
            'EOF'
        )
    elif input_mode == "mtz":
        if hklin_path is None:
            hklin_path = os.path.join(folder, "XDS_ASCII.mtz")
        if not os.path.isfile(hklin_path):
            return None

        bash_cmd = (
            f'source "{env.ccp4_setup}" && '
            'export CCP4_SCR="$PWD/CCP4_SCRATCH" && mkdir -p "$CCP4_SCR" && '
            'rm -f Merged.mtz Truncate.mtz Final_with_FreeR.mtz XDS.xml && '
            f'aimless HKLIN "{hklin_path}" HKLOUT Merged.mtz XMLOUT XDS.xml --no-input > aimless.log 2>&1 && '
            "ctruncate -mtzin Merged.mtz -mtzout Truncate.mtz -colin '/*/*/[IMEAN,SIGIMEAN]' > ctruncate.log 2>&1 && "
            'freerflag HKLIN Truncate.mtz HKLOUT Final_with_FreeR.mtz > freerflag.log 2>&1 << EOF\n'
            'FREERFRAC 0.05\n'
            'END\n'
            'EOF'
        )
    else:
        raise ValueError(f"Unknown input_mode='{input_mode}'")

    ok, rc, timed_out = run_cmd(
        ["bash", "-lc", bash_cmd],
        cwd=folder,
        timeout=env.ccp4_timeout,
        env=env,
    )

    if not ok:
        folder_name = os.path.basename(os.path.abspath(folder))
        print(f"CCP4 pipeline failed for '{folder_name}'")
        print("  Check logs:")
        for log in ["pointless.log", "aimless.log", "ctruncate.log", "freerflag.log"]:
            print(f"   - {os.path.join(folder, log)}")
        return None

    return parse_aimless_summary(os.path.join(folder, "aimless.log"))


# ============================================================
# DIMPLE
# ============================================================

def parse_dimple_blobs(folder):
    log_path = os.path.join(folder, "dimple.log")
    if not os.path.isfile(log_path):
        return -1
    try:
        with open(log_path) as f:
            text = f.read()
    except Exception:
        return -1

    match = re.search(r"blobs?:\s*(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.search(r"no blobs", text, re.IGNORECASE):
        return 0
    return -1


def run_dimple(folder, pdb, outdir, env: PipelineEnv):
    mtz = os.path.join(folder, "Final_with_FreeR.mtz")
    folder_name = os.path.basename(os.path.abspath(folder))

    if not os.path.isfile(mtz):
        print(f"DIMPLE skipped for '{folder_name}': Final_with_FreeR.mtz not found")
        return -1

    if not os.path.isfile(pdb):
        print(f"DIMPLE skipped for '{folder_name}': PDB not found at {pdb}")
        return -1

    bash_cmd = (
        f'source "{env.ccp4_setup}" && '
        f'dimple "{mtz}" "{pdb}" "{outdir}" > dimple.log 2>&1'
    )

    ok, rc, timed_out = run_cmd(
        ["bash", "-lc", bash_cmd],
        cwd=folder,
        timeout=env.dimple_timeout,
        env=env,
    )

    if not ok:
        reason = "timed out" if timed_out else f"exit code {rc}"
        print(f"DIMPLE failed for '{folder_name}' ({reason})")
        print(f"  Check: {os.path.join(folder, 'dimple.log')}")
        return -1

    final_pdb = os.path.join(folder, outdir, "final.pdb")
    if not os.path.isfile(final_pdb):
        print(f"DIMPLE finished but final.pdb missing for '{folder_name}'")
        print(f"  Check: {os.path.join(folder, 'dimple.log')}")
        return -1

    blobs = parse_dimple_blobs(folder)
    blob_str = str(blobs) if blobs >= 0 else "unknown"
    print(f"DIMPLE OK for '{folder_name}' -> blobs: {blob_str}")
    return blobs


# ============================================================
# PIPELINE MODES
# ============================================================

def full_pipeline(env: PipelineEnv):
    print(f"\n=== FULL MODE: Starting batch processing in: {env.root_dir} ===\n")
    write_summary_header(env.summary_file)

    counts = {"xds_ok": 0, "xds_fail": 0, "ccp4_ok": 0, "ccp4_fail": 0,
              "dimple_ok": 0, "dimple_fail": 0, "blobs_found": 0}

    for subdir, _, files in os.walk(env.root_dir):
        if "XDS.INP" not in files:
            continue

        ds = derive_dataset_info_from_xds_dir(subdir, env.root_dir)
        print(f"\n--- Dataset: {ds.dataset_id} ---")
        print(f"    Processing dir: {ds.processing_dir}")
        print(f"    Raw lookup dir: {os.path.join(env.raw_data_base_dir, ds.dataset_rel)}")

        try:
            transform_xds_inp_auto_template(
                os.path.join(ds.processing_dir, "XDS.INP"),
                env.raw_data_base_dir,
                ds.dataset_rel,
                env.prefix_hint,
                env.space_group_number,
                env.unit_cell_constants,
                env.data_range,
                env.spot_range,
                env.detector_type,
            )
        except Exception as e:
            print(f"XDS.INP modification failed for '{ds.dataset_id}': {e}")
            counts["xds_fail"] += 1
            continue

        if not run_xds(ds.processing_dir, env):
            counts["xds_fail"] += 1
            continue
        counts["xds_ok"] += 1

        result = run_ccp4_pipeline(ds.processing_dir, env, input_mode="hkl")
        if result is None:
            counts["ccp4_fail"] += 1
            continue
        counts["ccp4_ok"] += 1

        sg, res = result
        dimple_ok_str = "N/A"
        blobs_str = "N/A"

        if env.dimple_pdb is not None:
            blobs = run_dimple(ds.processing_dir, env.dimple_pdb, env.dimple_outdir, env)
            if blobs >= 0:
                counts["dimple_ok"] += 1
                dimple_ok_str = "OK"
                blobs_str = str(blobs)
                if blobs > 0:
                    counts["blobs_found"] += 1
            else:
                counts["dimple_fail"] += 1
                dimple_ok_str = "FAILED"
                blobs_str = "N/A"

        append_summary_line(env.summary_file, ds.dataset_id, sg, res, dimple_ok_str, blobs_str)

    print(f"\nSummary written to: {env.summary_file}")
    print_counter(counts, env)


def aimless_only(env: PipelineEnv):
    print(f"\n=== AIMLESS-ONLY MODE: Searching under: {env.root_dir} ===\n")
    write_summary_header(env.summary_file)

    counts = {"xds_ok": 0, "xds_fail": 0, "ccp4_ok": 0, "ccp4_fail": 0,
              "dimple_ok": 0, "dimple_fail": 0, "blobs_found": 0}

    if env.aimless_input_file.lower().endswith(".hkl"):
        input_mode = "hkl"
    elif env.aimless_input_file.lower().endswith(".mtz"):
        input_mode = "mtz"
    else:
        raise ValueError(f"AIMLESS_INPUT_FILE must be .hkl or .mtz, got '{env.aimless_input_file}'")

    for subdir, _, files in os.walk(env.root_dir):
        if env.aimless_input_file not in files:
            continue

        ds = derive_dataset_info_from_xds_dir(subdir, env.root_dir)
        print(f"\n--- CCP4-only dataset: {ds.dataset_id} ---")

        hklin_path = os.path.join(ds.processing_dir, env.aimless_input_file)
        result = run_ccp4_pipeline(ds.processing_dir, env, input_mode=input_mode, hklin_path=hklin_path)
        if result is None:
            counts["ccp4_fail"] += 1
            continue
        counts["ccp4_ok"] += 1

        sg, res = result
        dimple_ok_str = "N/A"
        blobs_str = "N/A"

        if env.dimple_pdb is not None:
            blobs = run_dimple(ds.processing_dir, env.dimple_pdb, env.dimple_outdir, env)
            if blobs >= 0:
                counts["dimple_ok"] += 1
                dimple_ok_str = "OK"
                blobs_str = str(blobs)
                if blobs > 0:
                    counts["blobs_found"] += 1
            else:
                counts["dimple_fail"] += 1
                dimple_ok_str = "FAILED"
                blobs_str = "N/A"

        append_summary_line(env.summary_file, ds.dataset_id, sg, res, dimple_ok_str, blobs_str)

    print(f"\nSummary written to: {env.summary_file}")
    print_counter(counts, env)


def dimple_only(env: PipelineEnv):
    if env.dimple_pdb is None:
        print("ERROR: DIMPLE_PDB must be set for dimple-only mode.")
        return

    print(f"\n=== DIMPLE-ONLY MODE: Searching under: {env.root_dir} ===\n")
    write_summary_header(env.summary_file)

    counts = {"xds_ok": 0, "xds_fail": 0, "ccp4_ok": 0, "ccp4_fail": 0,
              "dimple_ok": 0, "dimple_fail": 0, "blobs_found": 0}

    for subdir, _, files in os.walk(env.root_dir):
        if "Final_with_FreeR.mtz" not in files:
            continue

        ds = derive_dataset_info_from_xds_dir(subdir, env.root_dir)
        print(f"\n--- DIMPLE-only dataset: {ds.dataset_id} ---")

        sg, res = parse_aimless_summary(os.path.join(ds.processing_dir, "aimless.log"))

        blobs = run_dimple(ds.processing_dir, env.dimple_pdb, env.dimple_outdir, env)
        if blobs >= 0:
            counts["dimple_ok"] += 1
            dimple_ok_str = "OK"
            blobs_str = str(blobs)
            if blobs > 0:
                counts["blobs_found"] += 1
        else:
            counts["dimple_fail"] += 1
            dimple_ok_str = "FAILED"
            blobs_str = "N/A"

        append_summary_line(env.summary_file, ds.dataset_id, sg, res, dimple_ok_str, blobs_str)

    print(f"\nSummary written to: {env.summary_file}")
    print_counter(counts, env)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n====================================================")
    print("  WARNING")
    print("  Do NOT move, rename, or delete files or folders")
    print("  under the raw or processed data roots")
    print("  while this script is running.")
    print("====================================================\n")

    if MODE == "aimless-only":
        aimless_only(ENV)
    elif MODE == "full":
        full_pipeline(ENV)
    elif MODE == "dimple-only":
        dimple_only(ENV)
    else:
        print(f"ERROR: Unknown MODE='{MODE}'. Use 'full', 'aimless-only', or 'dimple-only'.")
