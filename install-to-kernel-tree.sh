#!/bin/bash
# SPDX-License-Identifier: MIT
#
# install-to-kernel-tree.sh - Install NVIDIA open GPU kernel modules for
# in-tree kernel building.
#
# Usage:  ./install-to-kernel-tree.sh <kernel-source-directory>
#
# This script copies the NVIDIA open-source GPU driver source code into a
# Linux kernel tree so that the driver can be built as part of a normal
# kernel build (make menuconfig / make modules).
#
# It:
#   1. Copies source files to drivers/gpu/drm/nvidia/
#   2. Generates a Kconfig for menuconfig integration
#   3. Generates a Kbuild Makefile from the upstream source lists
#   4. Patches drivers/gpu/drm/{Kconfig,Makefile} to wire it in
#

set -e

##############################################################################
# Helpers
##############################################################################

die() { echo "ERROR: $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

##############################################################################
# Argument handling
##############################################################################

KERNEL_DIR="${1:?Usage: $0 <kernel-source-directory>}"
KERNEL_DIR="$(cd "$KERNEL_DIR" && pwd)"

[ -f "$KERNEL_DIR/Kbuild" ] || [ -f "$KERNEL_DIR/Makefile" ] || \
    die "$KERNEL_DIR does not look like a kernel source tree"

DRV_DIR="$KERNEL_DIR/drivers/gpu/drm/nvidia"

echo "==> NVIDIA open GPU kernel module in-tree installer"
echo "    Source:  $SCRIPT_DIR"
echo "    Kernel:  $KERNEL_DIR"
echo "    Target:  $DRV_DIR"
echo

##############################################################################
# Read version string from version.mk
##############################################################################

NV_VERSION="$(sed -n 's/^NVIDIA_VERSION *= *//p' "$SCRIPT_DIR/version.mk" | tr -d ' ')"
[ -n "$NV_VERSION" ] || die "Cannot determine NVIDIA_VERSION from version.mk"
echo "    Version: $NV_VERSION"
echo

##############################################################################
# 1. Copy source trees
##############################################################################

echo "==> Copying source files ..."

rm -rf "$DRV_DIR"
mkdir -p "$DRV_DIR/kernel-open" "$DRV_DIR/src"

# kernel-open: interface layer + common headers
cp -a "$SCRIPT_DIR/kernel-open/common"          "$DRV_DIR/kernel-open/common"
cp -a "$SCRIPT_DIR/kernel-open/nvidia"           "$DRV_DIR/kernel-open/nvidia"
cp -a "$SCRIPT_DIR/kernel-open/nvidia-drm"       "$DRV_DIR/kernel-open/nvidia-drm"
cp -a "$SCRIPT_DIR/kernel-open/nvidia-modeset"   "$DRV_DIR/kernel-open/nvidia-modeset"
cp -a "$SCRIPT_DIR/kernel-open/nvidia-uvm"       "$DRV_DIR/kernel-open/nvidia-uvm"
cp -a "$SCRIPT_DIR/kernel-open/nvidia-peermem"   "$DRV_DIR/kernel-open/nvidia-peermem"
cp -a "$SCRIPT_DIR/kernel-open/conftest.sh"      "$DRV_DIR/kernel-open/conftest.sh"
cp -a "$SCRIPT_DIR/kernel-open/header-presence-tests.mk" \
      "$DRV_DIR/kernel-open/header-presence-tests.mk"

# src: full open-source RM core, modeset core, common libraries
cp -a "$SCRIPT_DIR/src/nvidia"         "$DRV_DIR/src/nvidia"
cp -a "$SCRIPT_DIR/src/nvidia-modeset" "$DRV_DIR/src/nvidia-modeset"
cp -a "$SCRIPT_DIR/src/common"         "$DRV_DIR/src/common"

echo "    Done."
echo

##############################################################################
# 2b. Patch nvidia sources for GCC RANDSTRUCT compatibility
##############################################################################

echo "==> Patching sources for GCC RANDSTRUCT compatibility ..."

# discovery_lr10.c
sed -i \
    -e 's/    \&_nvswitch_ptop_parse_entry_lr10,$/    .parse_entry  = \&_nvswitch_ptop_parse_entry_lr10,/' \
    -e 's/    \&_nvswitch_ptop_parse_enum_lr10,$/    .parse_enum   = \&_nvswitch_ptop_parse_enum_lr10,/' \
    -e 's/    \&_nvswitch_ptop_handle_data1_lr10,$/    .handle_data1 = \&_nvswitch_ptop_handle_data1_lr10,/' \
    -e 's/    \&_nvswitch_ptop_handle_data2_lr10$/    .handle_data2 = \&_nvswitch_ptop_handle_data2_lr10/' \
    -e 's/    \&_nvswitch_npg_parse_entry_lr10,$/    .parse_entry  = \&_nvswitch_npg_parse_entry_lr10,/' \
    -e 's/    \&_nvswitch_npg_parse_enum_lr10,$/    .parse_enum   = \&_nvswitch_npg_parse_enum_lr10,/' \
    -e 's/    \&_nvswitch_npg_handle_data1_lr10,$/    .handle_data1 = \&_nvswitch_npg_handle_data1_lr10,/' \
    -e 's/    \&_nvswitch_npg_handle_data2_lr10$/    .handle_data2 = \&_nvswitch_npg_handle_data2_lr10/' \
    -e 's/    \&nvswitch_nvlw_parse_entry_lr10,$/    .parse_entry  = \&nvswitch_nvlw_parse_entry_lr10,/' \
    -e 's/    \&nvswitch_nvlw_parse_enum_lr10,$/    .parse_enum   = \&nvswitch_nvlw_parse_enum_lr10,/' \
    -e 's/    \&nvswitch_nvlw_handle_data1_lr10,$/    .handle_data1 = \&nvswitch_nvlw_handle_data1_lr10,/' \
    -e 's/    \&nvswitch_nvlw_handle_data2_lr10$/    .handle_data2 = \&nvswitch_nvlw_handle_data2_lr10/' \
    -e 's/    \&nvswitch_nxbar_parse_entry_lr10,$/    .parse_entry  = \&nvswitch_nxbar_parse_entry_lr10,/' \
    -e 's/    \&nvswitch_nxbar_parse_enum_lr10,$/    .parse_enum   = \&nvswitch_nxbar_parse_enum_lr10,/' \
    -e 's/    \&nvswitch_nxbar_handle_data1_lr10,$/    .handle_data1 = \&nvswitch_nxbar_handle_data1_lr10,/' \
    -e 's/    \&nvswitch_nxbar_handle_data2_lr10$/    .handle_data2 = \&nvswitch_nxbar_handle_data2_lr10/' \
    "$DRV_DIR/src/common/nvswitch/kernel/lr10/discovery_lr10.c"

# discovery_ls10.c
sed -i \
    -e 's/    \&_nvswitch_ptop_parse_entry_ls10,$/    .parse_entry  = \&_nvswitch_ptop_parse_entry_ls10,/' \
    -e 's/    \&_nvswitch_ptop_parse_enum_ls10,$/    .parse_enum   = \&_nvswitch_ptop_parse_enum_ls10,/' \
    -e 's/    \&_nvswitch_ptop_handle_data1_ls10,$/    .handle_data1 = \&_nvswitch_ptop_handle_data1_ls10,/' \
    -e 's/    \&_nvswitch_ptop_handle_data2_ls10$/    .handle_data2 = \&_nvswitch_ptop_handle_data2_ls10/' \
    -e 's/    \&_nvswitch_npg_parse_entry_ls10,$/    .parse_entry  = \&_nvswitch_npg_parse_entry_ls10,/' \
    -e 's/    \&_nvswitch_npg_parse_enum_ls10,$/    .parse_enum   = \&_nvswitch_npg_parse_enum_ls10,/' \
    -e 's/    \&_nvswitch_npg_handle_data1_ls10,$/    .handle_data1 = \&_nvswitch_npg_handle_data1_ls10,/' \
    -e 's/    \&_nvswitch_npg_handle_data2_ls10$/    .handle_data2 = \&_nvswitch_npg_handle_data2_ls10/' \
    -e 's/    \&nvswitch_nvlw_parse_entry_ls10,$/    .parse_entry  = \&nvswitch_nvlw_parse_entry_ls10,/' \
    -e 's/    \&nvswitch_nvlw_parse_enum_ls10,$/    .parse_enum   = \&nvswitch_nvlw_parse_enum_ls10,/' \
    -e 's/    \&nvswitch_nvlw_handle_data1_ls10,$/    .handle_data1 = \&nvswitch_nvlw_handle_data1_ls10,/' \
    -e 's/    \&nvswitch_nvlw_handle_data2_ls10$/    .handle_data2 = \&nvswitch_nvlw_handle_data2_ls10/' \
    -e 's/    \&nvswitch_nxbar_parse_entry_ls10,$/    .parse_entry  = \&nvswitch_nxbar_parse_entry_ls10,/' \
    -e 's/    \&nvswitch_nxbar_parse_enum_ls10,$/    .parse_enum   = \&nvswitch_nxbar_parse_enum_ls10,/' \
    -e 's/    \&nvswitch_nxbar_handle_data1_ls10,$/    .handle_data1 = \&nvswitch_nxbar_handle_data1_ls10,/' \
    -e 's/    \&nvswitch_nxbar_handle_data2_ls10$/    .handle_data2 = \&nvswitch_nxbar_handle_data2_ls10/' \
    "$DRV_DIR/src/common/nvswitch/kernel/ls10/discovery_ls10.c"

# vbioscall.c
sed -i \
    -e 's/        (\&x_inb),$/        .inb  = \&x_inb,/' \
    -e 's/        (\&x_inw),$/        .inw  = \&x_inw,/' \
    -e 's/        (\&x_inl),$/        .inl  = \&x_inl,/' \
    -e 's/        (\&x_outb),$/        .outb = \&x_outb,/' \
    -e 's/        (\&x_outw),$/        .outw = \&x_outw,/' \
    -e 's/        (\&x_outl)$/        .outl = \&x_outl,/' \
    -e 's/        (\&Mem_rb),$/        .rdb = \&Mem_rb,/' \
    -e 's/        (\&Mem_rw),$/        .rdw = \&Mem_rw,/' \
    -e 's/        (\&Mem_rl),$/        .rdl = \&Mem_rl,/' \
    -e 's/        (\&Mem_wb),$/        .wrb = \&Mem_wb,/' \
    -e 's/        (\&Mem_ww),$/        .wrw = \&Mem_ww,/' \
    -e 's/        (\&Mem_wl)$/        .wrl = \&Mem_wl,/' \
    "$DRV_DIR/src/nvidia/arch/nvalloc/unix/src/vbioscall.c"

echo "    Done."
echo

##############################################################################
# 2b2. Linux 7.2: gpio_device_get_chip() takes a non-const gpio_device *
#
# NVIDIA's of_gpio.h compat wrapper passes a const gpio_device * into
# gpio_device_get_chip(). On aarch64 CONFIG_WERROR turns that into
# -Wincompatible-pointer-types-discards-qualifiers. The only caller
# already has a non-const pointer, so drop const from the helper.
##############################################################################

echo "==> Patching nv-linux.h gpio_device_get_chip const mismatch ..."
nvlinux="$DRV_DIR/kernel-open/common/inc/nv-linux.h"
if [ -f "$nvlinux" ]; then
	sed -i 's/static inline int __to_hwgpio(const struct gpio_device \*gdev,/static inline int __to_hwgpio(struct gpio_device *gdev,/' \
		"$nvlinux"
	echo "    Done."
else
	echo "    WARNING: nv-linux.h not found, skipped."
fi
echo

##############################################################################
# 2c. Patch generated HAL vtable initializers for GCC RANDSTRUCT compatibility
#
# The RM code-generator emits positional struct initializers for every HAL
# interface vtable, e.g.:
#
#   rpcCtrlFifoSetupVfZombieSubctxPdb_STUB,   // rpcCtrlFifoSetupVfZombieSubctxPdb
#
# With CONFIG_RANDSTRUCT the compiler shuffles struct field order, so
# positional initializers assign values to the wrong fields, producing a
# cascade of "incompatible pointer type" errors.
#
# Every positional entry in these files already carries a trailing comment
# that names the target field.  We exploit that to convert mechanically:
#
#   BEFORE:   <value>,   // fieldName
#   AFTER:    .fieldName = <value>,
#
# The sed expression matches only lines of that exact form (leading
# whitespace, a value token, a comma, optional spaces, then "// name") so it
# is safe to run idempotently and will not corrupt already-named initialisers,
# NULL entries without comments, or closing braces.
#
# We apply it to every g_*_private.h in the generated/ directory so that new
# files added in future driver versions are covered automatically.
##############################################################################

echo "==> Patching positional struct initialisers for RANDSTRUCT ..."

# We need to convert positional struct initializer entries like:
#
#   someFunction_STUB,   // fieldName
#
# into designated initializers:
#
#   .fieldName = someFunction_STUB,
#
# The challenge is that EXACTLY the same syntactic pattern appears in
# function call argument lists:
#
#   eheapAlloc(pHeap,       // thisHeap
#              owner,       // owner   ← must NOT be converted
#              ...);
#
# A line-by-line sed cannot distinguish the two contexts.  We use a small
# Python script that tracks brace/parenthesis depth: the transform is only
# applied when we are inside a brace block (depth_brace > depth_paren),
# which is the case for struct/array initializers but not function calls.
#
# The script is also idempotent: lines already in ".field = value," form
# are left untouched because their value token starts with '.'.

# Write the patcher to a temp file to avoid heredoc quoting issues
cat > /tmp/nv_randstruct_patch.py << 'SCRIPTEOF'
import re, sys, os

ROOT = sys.argv[1]

POSITIONAL_RE = re.compile(
    r'^(?P<ws>\s+)(?P<val>[^,\s.][^,]*),'
    r'\s*(?://|/\*)\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\*/)?\s*$'
)
# Strip C string literals before bracket counting
_Q = '"'
STR_RE = re.compile(_Q + r'(?:[^' + _Q + r'\\]|\\.)*' + _Q)

def patch_file(path):
    with open(path, 'r', errors='replace') as fh:
        lines = fh.readlines()

    out = []
    changed = False

    # brace_stack: True = initializer brace, False = structural brace.
    # The transform fires when the innermost brace is an initializer brace
    # and brace depth exceeds paren depth.
    #
    # We detect initializer braces by checking for '=' either on the same
    # line as '{' or on the immediately preceding non-empty line, to handle
    # the split pattern:
    #
    #   static const FOO bar =
    #   {                        <- '{' on its own line, '=' was on prev line
    #       entry,  // field
    #   };
    brace_stack = []
    depth_paren = 0
    prev_line_has_assign = False  # previous stripped line ended with '='

    for line in lines:
        in_initializer = (bool(brace_stack) and
                          brace_stack[-1] and
                          len(brace_stack) > depth_paren)

        if in_initializer:
            m = POSITIONAL_RE.match(line.rstrip('\n'))
            if m:
                new_line = '{ws}.{field} = {val},\n'.format(
                    ws=m.group('ws'),
                    field=m.group('field'),
                    val=m.group('val').rstrip(),
                )
                if new_line != line:
                    line = new_line
                    changed = True

        out.append(line)

        stripped = STR_RE.sub('""', line)
        stripped = re.sub(r'//.*', '', stripped)
        stripped = re.sub(r'/\*.*?\*/', '', stripped)

        # Walk the stripped line character by character so each '{' is
        # classified individually using its position in the line.
        pos = 0
        for ch in stripped:
            if ch == '{':
                before = stripped[:stripped.index('{', pos)].rstrip()
                is_init = before.endswith('=') or prev_line_has_assign
                brace_stack.append(is_init)
                prev_line_has_assign = False
            elif ch == '}':
                if brace_stack:
                    brace_stack.pop()
                prev_line_has_assign = False
            pos += 1

        depth_paren += stripped.count('(') - stripped.count(')')
        # Carry forward: did this line end with '=' for a split initializer?
        prev_line_has_assign = stripped.rstrip().endswith('=')

    if changed:
        with open(path, 'w') as fh:
            fh.writelines(out)

# 1. Generated HAL vtable headers
gen_dir = os.path.join(ROOT, 'src', 'nvidia', 'generated')
if os.path.isdir(gen_dir):
    for fname in os.listdir(gen_dir):
        if fname.startswith('g_') and fname.endswith('_private.h'):
            fpath = os.path.join(gen_dir, fname)
            before = open(fpath).read()
            patch_file(fpath)
            after = open(fpath).read()
            changed = before != after
            
# 2. All handwritten C sources under src/ except the generated/ subtree
src_root = os.path.join(ROOT, 'src')
if os.path.isdir(src_root):
    for dirpath, dirnames, filenames in os.walk(src_root):
        # Skip generated/ directories (handled above)
        dirnames[:] = [d for d in dirnames if d != 'generated']
        for fname in filenames:
            if fname.endswith('.c'):
                patch_file(os.path.join(dirpath, fname))
SCRIPTEOF

python3 /tmp/nv_randstruct_patch.py "$DRV_DIR"

# g_hal_private.h uses positional HAL_IFACE_SETUP initializers with no
# trailing comments, so the generic comment-driven patcher cannot handle it.
# The struct has exactly two fields in this order:
#   1. rpcHalIfacesSetupFn
#   2. rpcstructurecopyHalIfacesSetupFn
# We convert them to designated form with two targeted sed expressions.
# bar2_walk.c and gmmu_walk.c define MMU_WALK_CALLBACKS initializers
# with no trailing comments.  We patch them using Python (sed backreferences
# are not portable across all implementations).
# Field order from mmu_walk.h:
#   LevelAlloc, LevelFree, UpdatePdb, UpdatePde, FillEntries, CopyEntries, WriteBuffer
cat > /tmp/nv_mmu_walk_patch.py << 'MMUEOF'
import re, sys, os

FIELDS = [
    ('LevelAlloc',  re.compile(r'^(\s*)(_bar2WalkCBLevelAlloc|_gmmuWalkCBLevelAlloc),$')),
    ('LevelFree',   re.compile(r'^(\s*)(_bar2WalkCBLevelFree|_gmmuWalkCBLevelFree),$')),
    ('UpdatePdb',   re.compile(r'^(\s*)(_bar2WalkCBUpdatePdb|_gmmuWalkCBUpdatePdb),$')),
    ('UpdatePde',   re.compile(r'^(\s*)(_bar2WalkCBUpdatePde|_gmmuWalkCBUpdatePde),$')),
    ('FillEntries', re.compile(r'^(\s*)(_bar2WalkCBFillEntries|_gmmuWalkCBFillEntries),$')),
    ('CopyEntries', re.compile(r'^(\s*)(_bar2WalkCBCopyEntries|_gmmuWalkCBCopyEntries),$')),
    ('WriteBuffer', re.compile(r'^(\s*)(_bar2WalkCBWriteBuffer|_gmmuWalkCBWriteBuffer),$')),
]
NULL_AFTER = {'FillEntries': 'CopyEntries', 'CopyEntries': 'WriteBuffer'}

for path in sys.argv[1:]:
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        src_lines = f.readlines()
    out = []
    changed = False
    last_field = None
    for line in src_lines:
        s = line.rstrip()
        matched = False
        for field, pat in FIELDS:
            m = pat.match(s)
            if m:
                nl = m.group(1) + '.' + field + ' = ' + m.group(2) + ',\n'
                if nl != line:
                    line = nl
                    changed = True
                last_field = field
                matched = True
                break
        if not matched and s.endswith('NULL,') and last_field in NULL_AFTER:
            ws = len(line) - len(line.lstrip())
            nf = NULL_AFTER[last_field]
            nl = ' ' * ws + '.' + nf + ' = NULL,\n'
            if nl != line:
                line = nl
                changed = True
            last_field = nf
        out.append(line)
    if changed:
        with open(path, "w") as f:
            f.writelines(out)
MMUEOF

python3 /tmp/nv_mmu_walk_patch.py \
    "$DRV_DIR/src/nvidia/src/kernel/gpu/mmu/bar2_walk.c" \
    "$DRV_DIR/src/nvidia/src/kernel/gpu/mmu/gmmu_walk.c"

G_HAL_PRIVATE="$DRV_DIR/src/nvidia/generated/g_hal_private.h"
if [ -f "$G_HAL_PRIVATE" ]; then
    python3 - "$G_HAL_PRIVATE" << 'HALEOF'
import re, sys
path = sys.argv[1]
with open(path) as f: src = f.read()
src = re.sub(
    r'(^\s*)(rpcHalIfacesSetup_[A-Za-z0-9_]+),\s*$',
    lambda m: m.group(1) + '.rpcHalIfacesSetupFn = ' + m.group(2) + ',',
    src, flags=re.MULTILINE)
src = re.sub(
    r'(^\s*)(rpcstructurecopyHalIfacesSetup_[A-Za-z0-9_]+),\s*$',
    lambda m: m.group(1) + '.rpcstructurecopyHalIfacesSetupFn = ' + m.group(2) + ',',
    src, flags=re.MULTILINE)
with open(path, "w") as f: f.write(src)
HALEOF
fi

echo "    Done."
echo

##############################################################################
# Helper: extract source file list from an srcs.mk / .Kbuild file
#
# extract_srcs <file> <variable_name> <parent_prefix> <base_prefix>
#
# Reads lines matching "^<variable_name> += <path>" and transforms:
#   1. Strips leading <prefix_to_strip> from the path (typically "../")
#   2. Adds <prefix_to_add> in front
# Prints one path per line.
##############################################################################

extract_srcs() {
    local file="$1" varname="$2" parent="$3" base="$4"
    # Fast path: single sed pipeline, no per-line subshells.
    # Paths starting with "../" are resolved relative to the parent directory
    # (e.g., ../common/foo.c in src/nvidia/srcs.mk → src/common/foo.c).
    # All other paths get the base prefix (e.g., arch/foo.c → src/nvidia/arch/foo.c).
    # The "t" command skips the second substitution when the first matches.
    sed -n "s|^${varname}[[:space:]]*+=[[:space:]]*||p" "$file" | \
        sed 's/[[:space:]]*$//' | \
        grep -v '^$' | \
        sed "s|^\.\./|${parent}|; t; s|^|${base}|"
}

##############################################################################
# Helper: extract conftest test names from .Kbuild/.mk files
##############################################################################

extract_conftest_tests() {
    local varname="$1"
    shift
    for f in "$@"; do
        [ -f "$f" ] || continue
        sed -n "s|^${varname}[[:space:]]*+=[[:space:]]*||p" "$f" | \
            sed 's/[[:space:]]*$//' | grep -v '^$'
    done | sort -u
}

##############################################################################
# 2. Collect source file lists
##############################################################################

echo "==> Generating source file lists ..."

# --- nvidia.ko: interface layer (kernel-open/nvidia/) ---
nvidia_if_srcs="$(extract_srcs \
    "$SCRIPT_DIR/kernel-open/nvidia/nvidia-sources.Kbuild" \
    "NVIDIA_SOURCES" "" "kernel-open/")"

# --- nvidia.ko: RM core (src/nvidia/) ---
nvidia_rm_srcs="$(extract_srcs \
    "$SCRIPT_DIR/src/nvidia/srcs.mk" "SRCS" "src/" "src/nvidia/")"

# --- nvidia-modeset.ko: interface layer ---
nv_modeset_if_srcs="kernel-open/nvidia-modeset/nvidia-modeset-linux.c
kernel-open/nvidia-modeset/nv-kthread-q.c"

# --- nvidia-modeset.ko: core C sources ---
nv_modeset_c_srcs="$(extract_srcs \
    "$SCRIPT_DIR/src/nvidia-modeset/srcs.mk" "SRCS" "src/" "src/nvidia-modeset/")"

# --- nvidia-modeset.ko: core C++ sources ---
nv_modeset_cxx_srcs="$(extract_srcs \
    "$SCRIPT_DIR/src/nvidia-modeset/srcs.mk" "SRCS_CXX" "src/" "src/nvidia-modeset/")"

# --- nvidia-drm.ko ---
nv_drm_srcs="$(extract_srcs \
    "$SCRIPT_DIR/kernel-open/nvidia-drm/nvidia-drm-sources.mk" \
    "NVIDIA_DRM_SOURCES" "" "kernel-open/")"
nv_drm_srcs="$nv_drm_srcs
kernel-open/nvidia-drm/nvidia-drm-linux.c"

# --- nvidia-uvm.ko ---
nv_uvm_srcs="$(extract_srcs \
    "$SCRIPT_DIR/kernel-open/nvidia-uvm/nvidia-uvm-sources.Kbuild" \
    "NVIDIA_UVM_SOURCES" "" "kernel-open/")"

# --- nvidia-peermem.ko ---
nv_peermem_srcs="kernel-open/nvidia-peermem/nvidia-peermem.c"

echo "    nvidia.ko:         $(echo "$nvidia_if_srcs" | wc -l) interface + $(echo "$nvidia_rm_srcs" | wc -l) RM core"
echo "    nvidia-modeset.ko: $(echo "$nv_modeset_if_srcs" | wc -l) interface + $(echo "$nv_modeset_c_srcs" | wc -l) C core + $(echo "$nv_modeset_cxx_srcs" | wc -l) C++ core"
echo "    nvidia-drm.ko:     $(echo "$nv_drm_srcs" | wc -l) sources"
echo "    nvidia-uvm.ko:     $(echo "$nv_uvm_srcs" | wc -l) sources"
echo "    nvidia-peermem.ko: $(echo "$nv_peermem_srcs" | wc -l) sources"
echo

##############################################################################
# 3. Collect conftest test names
##############################################################################

KBUILD_FILES=(
    "$SCRIPT_DIR/kernel-open/nvidia/nvidia.Kbuild"
    "$SCRIPT_DIR/kernel-open/nvidia-drm/nvidia-drm-sources.mk"
    "$SCRIPT_DIR/kernel-open/nvidia-drm/nvidia-drm.Kbuild"
    "$SCRIPT_DIR/kernel-open/nvidia-modeset/nvidia-modeset.Kbuild"
    "$SCRIPT_DIR/kernel-open/nvidia-uvm/nvidia-uvm.Kbuild"
    "$SCRIPT_DIR/kernel-open/nvidia-peermem/nvidia-peermem.Kbuild"
)

CONFTEST_FUNC="$(extract_conftest_tests NV_CONFTEST_FUNCTION_COMPILE_TESTS "${KBUILD_FILES[@]}")"
CONFTEST_SYM="$(extract_conftest_tests NV_CONFTEST_SYMBOL_COMPILE_TESTS "${KBUILD_FILES[@]}")"
CONFTEST_TYPE="$(extract_conftest_tests NV_CONFTEST_TYPE_COMPILE_TESTS "${KBUILD_FILES[@]}")"
CONFTEST_GENERIC="$(extract_conftest_tests NV_CONFTEST_GENERIC_COMPILE_TESTS "${KBUILD_FILES[@]}")"
CONFTEST_MACRO="$(extract_conftest_tests NV_CONFTEST_MACRO_COMPILE_TESTS "${KBUILD_FILES[@]}")"

##############################################################################
# Helper: convert a source file path (.c or .cpp) to an object file path (.o)
##############################################################################

src_to_obj() {
    echo "$1" | sed -e 's/\.c$/.o/' -e 's/\.cpp$/.o/'
}

# Build object lists — convert .c/.cpp → .o (fast sed, no per-line subshells)
srcs_to_objs() { echo "$1" | sed -e 's/\.c$/.o/' -e 's/\.cpp$/.o/' | grep -v '^$'; }

nvidia_if_objs="$(srcs_to_objs "$nvidia_if_srcs")"
nvidia_rm_objs="$(srcs_to_objs "$nvidia_rm_srcs")"
nv_modeset_if_objs="$(srcs_to_objs "$nv_modeset_if_srcs")"
nv_modeset_c_objs="$(srcs_to_objs "$nv_modeset_c_srcs")"
nv_modeset_cxx_objs="$(srcs_to_objs "$nv_modeset_cxx_srcs")"
nv_drm_objs="$(srcs_to_objs "$nv_drm_srcs")"
nv_uvm_objs="$(srcs_to_objs "$nv_uvm_srcs")"
nv_peermem_objs="$(srcs_to_objs "$nv_peermem_srcs")"

# Write a Makefile variable assignment from a newline-separated list of values.
# Usage: write_obj_var "varname" "$list" >> file
write_obj_var() {
    local varname="$1" list="$2"
    echo "${varname} := \\"
    echo "$list" | grep -v '^$' | sed 's/^/  /; $ ! s/$/ \\/'
    echo
}

##############################################################################
# 4. Collect shader binary files for nvidia-modeset
##############################################################################

SHADER_NAMES=()
for shader in "$SCRIPT_DIR"/src/nvidia-modeset/src/shaders/g_*_shaders; do
    [ -f "$shader" ] || continue
    name="$(basename "$shader")"
    # e.g. g_turing_shaders → turing
    tag="$(echo "$name" | sed 's/^g_//; s/_shaders$//')"
    SHADER_NAMES+=("$tag")
done

##############################################################################
# 4b. Patch PAHOLE_FLAGS to handle _Atomic types (nvidia sources use C11 atomics
#     which pahole < 1.28 cannot encode as BTF)
##############################################################################

echo "==> Patching scripts/Makefile.btf to add --skip_encoding_btf_type_tag ..."
if ! grep -q 'skip_encoding_btf_type_tag' "$KERNEL_DIR/scripts/Makefile.btf"; then
    sed -i 's/^export PAHOLE_FLAGS := /export PAHOLE_FLAGS := --skip_encoding_btf_type_tag /'         "$KERNEL_DIR/scripts/Makefile.btf"
    echo "    Patched."
else
    echo "    Already patched, skipping."
fi
echo

##############################################################################
# 5. Generate Kconfig
##############################################################################

echo "==> Writing Kconfig ..."

cat > "$DRV_DIR/Kconfig" << 'KCONFIG_EOF'
# SPDX-License-Identifier: MIT

config DRM_NVIDIA
	tristate "NVIDIA GPU (open kernel modules)"
	depends on DRM && PCI
	depends on X86_64 || ARM64
	select DRM_KMS_HELPER
	help
	  Choose this option if you have an NVIDIA GPU (Turing or newer)
	  and want to use the open-source kernel driver modules.

	  This provides the nvidia, nvidia-modeset, nvidia-drm, and
	  nvidia-uvm kernel modules, enabling full GPU support including
	  DRM/KMS mode setting.

	  The driver requires the GSP (GPU System Processor) firmware
	  which is loaded at runtime via the firmware loading mechanism.

	  If M is selected, several modules will be built:
	    - nvidia        (core GPU resource manager)
	    - nvidia-modeset (kernel mode setting engine)
	    - nvidia-drm     (DRM/KMS interface)
	    - nvidia-uvm     (unified virtual memory)

config DRM_NVIDIA_UVM
	tristate "NVIDIA Unified Virtual Memory (UVM) support"
	depends on DRM_NVIDIA
	select MMU_NOTIFIER
	default DRM_NVIDIA
	help
	  Enable Unified Virtual Memory support for NVIDIA GPUs.
	  UVM provides automatic page migration between CPU and GPU
	  memory, required by CUDA's managed-memory APIs.

	  If unsure, say Y.

config DRM_NVIDIA_PEERMEM
	tristate "NVIDIA peer memory (GPUDirect RDMA) support"
	depends on DRM_NVIDIA && INFINIBAND
	default n
	help
	  Enable peer memory support for NVIDIA GPUs, allowing
	  InfiniBand HCAs to directly access GPU memory (GPUDirect RDMA).

	  Requires a Mellanox/NVIDIA InfiniBand adapter.

	  If unsure, say N.
KCONFIG_EOF

echo "    Done."
echo

##############################################################################
# 6. Generate Makefile
##############################################################################

echo "==> Generating Makefile ..."

MK="$DRV_DIR/Makefile"

cat > "$MK" << HEADER_EOF
# SPDX-License-Identifier: MIT
#
# Kbuild Makefile for NVIDIA open GPU kernel modules (in-tree build).
#
# Generated by install-to-kernel-tree.sh from open-gpu-kernel-modules
# version ${NV_VERSION}.
#
# Do not edit — re-run the install script to regenerate.
#

###########################################################################
# Utility macro: assign per-object CFLAGS
###########################################################################
ASSIGN_PER_OBJ_CFLAGS = \\
 \$(foreach _cflags_variable, \\
   \$(notdir \$(1)) \$(1), \\
   \$(eval \$(addprefix CFLAGS_,\$(_cflags_variable)) += \$(2)))

###########################################################################
# Conftest — kernel feature detection for the interface layer
###########################################################################

NV_KERNEL_SOURCES := \$(abspath \$(srctree))
NV_KERNEL_OUTPUT  := \$(abspath \$(objtree))

NV_CONFTEST_SCRIPT := \$(src)/kernel-open/conftest.sh
NV_CONFTEST_HEADER := \$(obj)/conftest/headers.h

NV_CONFTEST_CMD := /bin/sh \$(NV_CONFTEST_SCRIPT) \\
  "\$(CC)" \$(ARCH) \$(NV_KERNEL_SOURCES) \$(NV_KERNEL_OUTPUT)

# Construct conftest CFLAGS directly from kbuild's exported variables instead
# of calling conftest.sh's build_cflags, which misses force-include headers
# required by kernel 7.0+ (compiler-version.h, kconfig.h, compiler_types.h).
#
# IMPORTANT: conftest.sh does "cd \$SCRIPTDIR" (into kernel-open/), so all
# relative paths from LINUXINCLUDE (e.g. -I./include) break.  We must
# convert them to absolute paths via subst.
#
# compiler_types.h is added explicitly (kbuild normally adds it via
# KBUILD_CFLAGS, but we cannot use KBUILD_CFLAGS wholesale because it
# contains -Werror which would break conftest's detection logic).
#
# -fms-extensions / -fms-anonymous-structs: required so anonymous MS struct
# members (e.g. struct filename { struct __filename_head; ... }) parse
# correctly. Clang 23's CONFIG_CC_MS_EXTENSIONS is -fms-anonymous-structs;
# older toolchains used -fms-extensions. Without these, conftest compile
# tests fail inside linux/fs.h (sizeof(struct filename) static_assert) and
# feature detection produces inverted/wrong results.
NV_CONFTEST_CFLAGS_ABS_SRCTREE := \$(abspath \$(srctree))
NV_CONFTEST_LINUXINCLUDE := \$(subst ./,\$(NV_CONFTEST_CFLAGS_ABS_SRCTREE)/,\$(LINUXINCLUDE))
NV_CONFTEST_CFLAGS = -O2 -D__KERNEL__ \\
  -DKBUILD_BASENAME=\\\"conftest\\\" -DKBUILD_MODNAME=\\\"conftest\\\" \\
  \$(NOSTDINC_FLAGS) \$(NV_CONFTEST_LINUXINCLUDE) \\
  -include \$(NV_CONFTEST_CFLAGS_ABS_SRCTREE)/include/linux/compiler_types.h \\
  \$(filter -std=% -fshort-wchar -funsigned-char -fno-common -fno-PIE -fno-pie -fms-extensions -fms-anonymous-structs -mfentry -fcf-protection=% -DCC_USING_FENTRY,\$(KBUILD_CFLAGS)) \\
  -I\$(abspath \$(obj)) \\
  -I\$(abspath \$(src)/kernel-open) \\
  -Wno-implicit-function-declaration -Wno-strict-prototypes \\
  -fno-pie


NV_CONFTEST_COMPILE_TEST_HEADERS := \$(obj)/conftest/macros.h
NV_CONFTEST_COMPILE_TEST_HEADERS += \$(obj)/conftest/functions.h
NV_CONFTEST_COMPILE_TEST_HEADERS += \$(obj)/conftest/symbols.h
NV_CONFTEST_COMPILE_TEST_HEADERS += \$(obj)/conftest/types.h
NV_CONFTEST_COMPILE_TEST_HEADERS += \$(obj)/conftest/generic.h

NV_CONFTEST_HEADERS := \$(obj)/conftest/patches.h
NV_CONFTEST_HEADERS += \$(obj)/conftest/headers.h
NV_CONFTEST_HEADERS += \$(NV_CONFTEST_COMPILE_TEST_HEADERS)

# Protect nvidia-generated files from "make clean" so that kernel-source
# package users and sequential kernel variant builds don't need to re-run
# the install script.
no-clean-files += kernel-open/header-presence-tests.mk
no-clean-files += conftest/patches.h
no-clean-files += conftest/headers.h
no-clean-files += conftest/macros.h
no-clean-files += conftest/functions.h
no-clean-files += conftest/symbols.h
no-clean-files += conftest/types.h
no-clean-files += conftest/generic.h
no-clean-files += \$(wildcard conftest/compile-tests/*.h)

# Generate a header file for a single conftest compile test.
\$(obj)/conftest/compile-tests/%.h: \$(NV_CONFTEST_SCRIPT) \$(NV_CONFTEST_HEADER)
	@mkdir -p \$(obj)/conftest/compile-tests
	@echo " CONFTEST: \$(notdir \$*)"
	@\$(NV_CONFTEST_CMD) compile_tests '\$(NV_CONFTEST_CFLAGS)' \\
	  \$(notdir \$*) > \$@

\$(obj)/conftest/symbols.h: \$(srctree)/vmlinux.symvers \$(NV_CONFTEST_HEADER)
	@mkdir -p \$(obj)/conftest
	@{ \\
	  echo "/* Auto-generated: symbol presence from vmlinux.symvers */"; \\
	  for sym in \$(NV_CONFTEST_SYMBOL_COMPILE_TESTS); do \\
	    bare=\$\$(echo "\$\$sym" | sed \\
	      -e 's/^is_export_symbol_present_//' \\
	      -e 's/^is_export_symbol_gpl_//'); \\
	    symvers="\$(srctree)/vmlinux.symvers"; \\
	    if grep -qP "^\S+\t\$\${bare}\t" "\$\$symvers" 2>/dev/null; then \\
	      present=1; \\
	      if grep -qP "^\S+\t\$\${bare}\t\S+\tEXPORT_SYMBOL_GPL\b" "\$\$symvers" 2>/dev/null; then \\
	        gpl=1; \\
	      else \\
	        gpl=0; \\
	      fi; \\
	    else \\
	      present=0; gpl=0; \\
	    fi; \\
	    echo "#define NV_IS_EXPORT_SYMBOL_PRESENT_\$\${bare} \$\${present}"; \\
	    echo "#define NV_IS_EXPORT_SYMBOL_GPL_\$\${bare} \$\${gpl}"; \\
	  done; \\
	} > \$@

# Concatenate a conftest header from its constituent compile test headers
define NV_GENERATE_COMPILE_TEST_HEADER
 \$(obj)/conftest/\$(1).h: \$(addprefix \$(obj)/conftest/compile-tests/,\$(addsuffix .h,\$(2)))
	@mkdir -p \$(obj)/conftest
	@cat \$\$^ /dev/null > \$\$@
endef

HEADER_EOF

# --- Write conftest test lists (fast: sed prefix, no per-line subshells) ---
write_conftest_var() {
    local varname="$1" values="$2"
    echo "${varname} :="
    echo "$values" | grep -v '^$' | sed "s/^/${varname} += /"
    echo
}

{
    write_conftest_var "NV_CONFTEST_FUNCTION_COMPILE_TESTS" "$CONFTEST_FUNC"
    write_conftest_var "NV_CONFTEST_SYMBOL_COMPILE_TESTS" "$CONFTEST_SYM"
    write_conftest_var "NV_CONFTEST_TYPE_COMPILE_TESTS" "$CONFTEST_TYPE"
    write_conftest_var "NV_CONFTEST_GENERIC_COMPILE_TESTS" "$CONFTEST_GENERIC"
    write_conftest_var "NV_CONFTEST_MACRO_COMPILE_TESTS" "$CONFTEST_MACRO"
} >> "$MK"

# --- Write conftest generation rules ---
cat >> "$MK" << 'CONFTEST_RULES_EOF'
$(eval $(call NV_GENERATE_COMPILE_TEST_HEADER,functions,$(NV_CONFTEST_FUNCTION_COMPILE_TESTS)))
$(eval $(call NV_GENERATE_COMPILE_TEST_HEADER,generic,$(NV_CONFTEST_GENERIC_COMPILE_TESTS)))
$(eval $(call NV_GENERATE_COMPILE_TEST_HEADER,macros,$(NV_CONFTEST_MACRO_COMPILE_TESTS)))
$(eval $(call NV_GENERATE_COMPILE_TEST_HEADER,types,$(NV_CONFTEST_TYPE_COMPILE_TESTS)))

$(obj)/conftest/patches.h: $(NV_CONFTEST_SCRIPT)
	@mkdir -p $(obj)/conftest
	@$(NV_CONFTEST_CMD) patch_check > $@

-include $(src)/kernel-open/header-presence-tests.mk

NV_HEADER_PRESENCE_PART = $(addprefix $(obj)/conftest/header_presence/,$(addsuffix .part,$(1)))

define NV_HEADER_PRESENCE_CHECK
 $$(call NV_HEADER_PRESENCE_PART,$(1)): $$(NV_CONFTEST_SCRIPT) $(obj)/conftest/uts_release
	@mkdir -p $$(dir $$@)
	@$$(NV_CONFTEST_CMD) test_kernel_header '$$(NV_CONFTEST_CFLAGS)' '$(1)' > $$@
endef

$(foreach header,$(NV_HEADER_PRESENCE_TESTS),$(eval $(call NV_HEADER_PRESENCE_CHECK,$(header))))

$(obj)/conftest/headers.h: $(call NV_HEADER_PRESENCE_PART,$(NV_HEADER_PRESENCE_TESTS))
	@cat $^ > $@

$(obj)/conftest/uts_release: NV_GENERATE_UTS_RELEASE
	@mkdir -p $(dir $@)
	@NV_UTS_RELEASE="// Kernel version: `$(NV_CONFTEST_CMD) compile_tests '$(NV_CONFTEST_CFLAGS)' uts_release 2>/dev/null | tail -1`"; \
	if ! [ -f "$@" ] || [ "$$NV_UTS_RELEASE" != "`cat $@`" ]; \
	then echo "$$NV_UTS_RELEASE" > $@; fi

.PHONY: NV_GENERATE_UTS_RELEASE

# Order-only prerequisite: uts_release must be built before the compile test
# headers run (they may need the kernel version), but must NOT be included in
# $^ (which is used by "cat $^ > $@" recipes to build the header files).
$(NV_CONFTEST_HEADERS): | $(obj)/conftest/uts_release

clean-dirs := $(obj)/conftest

NV_OBJECTS_DEPEND_ON_CONFTEST :=

CONFTEST_RULES_EOF

# --- Write global ccflags ---
cat >> "$MK" << GLOBALFLAGS_EOF

###########################################################################
# Global compiler flags (shared by all interface-layer modules)
###########################################################################

ccflags-y += -Wall -Wno-cast-qual -Wno-format-extra-args
ccflags-y += -DNVRM
ccflags-y += -DNV_VERSION_STRING=\\"${NV_VERSION}\\"
ccflags-y += -Wno-unused-function
ccflags-y += -Wno-missing-prototypes
ccflags-y += -fno-strict-aliasing
ccflags-y += -ffreestanding
ccflags-y += -DNV_UVM_ENABLE
ccflags-y += -DNV_SPECTRE_V2=0
ccflags-y += -DNV_FILESYSTEM_ACCESS_AVAILABLE=1

ifeq (\$(ARCH),arm64)
  ccflags-y += -mstrict-align -mgeneral-regs-only -march=armv8-a
  ccflags-y += \$(call cc-option,-mno-outline-atomics,)
endif

ifeq (\$(ARCH),x86_64)
  ccflags-y += -mno-red-zone -mcmodel=kernel
endif

GLOBALFLAGS_EOF

# ===========================================================================
# nvidia.ko
# ===========================================================================

{
echo "###########################################################################"
echo "# Module: nvidia.ko"
echo "###########################################################################"
echo
echo "obj-\$(CONFIG_DRM_NVIDIA) += nvidia.o"
echo

# Interface-layer objects
write_obj_var "nvidia-if-y" "$nvidia_if_objs"

# RM core objects
write_obj_var "nvidia-rm-y" "$nvidia_rm_objs"

echo "nvidia-y := \$(nvidia-if-y) \$(nvidia-rm-y) g_nvrm_nvid_string.o"
echo

# NVRM ID string generation
cat << NVRM_NVID_EOF
# Generated version identification string for nvidia.ko
\$(obj)/g_nvrm_nvid_string.c: FORCE
	@mkdir -p \$(@D)
	@echo 'const char NVRM_ID[] = "nvidia id: NVIDIA Open Kernel Module  ${NV_VERSION}";' > \$@
	@echo 'const char *const pNVRM_ID = NVRM_ID + 11;' >> \$@

clean-files += g_nvrm_nvid_string.c

NVRM_NVID_EOF

# nv-compiler.h generation
cat << 'NV_COMPILER_EOF'
NV_COMPILER_VERSION_HEADER = $(obj)/nv_compiler.h

$(NV_COMPILER_VERSION_HEADER):
	@echo \#define NV_COMPILER \"`$(CC) -v 2>&1 | tail -n 1`\" > $@

$(obj)/kernel-open/nvidia/nv-procfs.o: $(NV_COMPILER_VERSION_HEADER)
clean-files += $(NV_COMPILER_VERSION_HEADER)

NV_COMPILER_EOF

# Interface-layer CFLAGS
cat << 'NVIDIA_IF_CFLAGS_EOF'
NVIDIA_IF_CFLAGS := -I$(obj)
NVIDIA_IF_CFLAGS += -I$(src)/kernel-open/common/inc
NVIDIA_IF_CFLAGS += -I$(src)/kernel-open
NVIDIA_IF_CFLAGS += -I$(src)/kernel-open/nvidia
NVIDIA_IF_CFLAGS += -DNV_KERNEL_INTERFACE_LAYER
NVIDIA_IF_CFLAGS += -DNVIDIA_UNDEF_LEGACY_BIT_MACROS
NVIDIA_IF_CFLAGS += -DLIBSPDM_CONFIG=\"nvspdm_rmconfig.h\"
NVIDIA_IF_CFLAGS += -UDEBUG -U_DEBUG -DNDEBUG
NVIDIA_IF_CFLAGS += -Wno-error

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-if-y), $(NVIDIA_IF_CFLAGS))
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/functions.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/symbols.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/types.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/generic.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/macros.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/patches.h
NVIDIA_IF_CFLAGS += -include $(obj)/conftest/headers.h
NV_OBJECTS_DEPEND_ON_CONFTEST += $(nvidia-if-y)

NVIDIA_IF_CFLAGS_EOF

# RM core CFLAGS
cat << 'NV_RM_CFLAGS_EOF'
NV_RM_CFLAGS := -U__KERNEL__
NV_RM_CFLAGS += $(call cc-option,-Wno-designated-init,)
NV_RM_CFLAGS += -isystem $(shell $(CC) -print-file-name=include)
NV_RM_CFLAGS += -include $(src)/src/common/sdk/nvidia/inc/cpuopsys.h
NV_RM_CFLAGS += -I$(src)/src/nvidia/kernel/inc
NV_RM_CFLAGS += -I$(src)/src/nvidia/interface
NV_RM_CFLAGS += -I$(src)/src/common/sdk/nvidia/inc
NV_RM_CFLAGS += -I$(src)/src/common/sdk/nvidia/inc/hw
NV_RM_CFLAGS += -I$(src)/src/nvidia/arch/nvalloc/common/inc
NV_RM_CFLAGS += -I$(src)/src/nvidia/arch/nvalloc/common/inc/gsp
NV_RM_CFLAGS += -I$(src)/src/nvidia/arch/nvalloc/common/inc/deprecated
NV_RM_CFLAGS += -I$(src)/src/nvidia/arch/nvalloc/unix/include
NV_RM_CFLAGS += -I$(src)/src/nvidia/inc
NV_RM_CFLAGS += -I$(src)/src/nvidia/inc/os
NV_RM_CFLAGS += -I$(src)/src/common/shared/inc
NV_RM_CFLAGS += -I$(src)/src/common/inc
NV_RM_CFLAGS += -I$(src)/src/common/uproc/os/libos-v2.0.0/include
NV_RM_CFLAGS += -I$(src)/src/common/uproc/os/common/include
NV_RM_CFLAGS += -I$(src)/src/common/inc/swref
NV_RM_CFLAGS += -I$(src)/src/common/inc/swref/published
NV_RM_CFLAGS += -I$(src)/src/nvidia/generated
NV_RM_CFLAGS += -I$(src)/src/common/nvswitch/kernel/inc
NV_RM_CFLAGS += -I$(src)/src/common/nvswitch/interface
NV_RM_CFLAGS += -I$(src)/src/common/nvswitch/common/inc
NV_RM_CFLAGS += -I$(src)/src/common/inc/displayport
NV_RM_CFLAGS += -I$(src)/src/common/nvlink/interface
NV_RM_CFLAGS += -I$(src)/src/common/nvlink/inband/interface
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/mm/uvm/interface
NV_RM_CFLAGS += -I$(src)/src/nvidia/inc/libraries
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries
NV_RM_CFLAGS += -I$(src)/src/nvidia/inc/kernel
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/3.5.0/include
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/3.5.0/include/hal
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/3.5.0/os_stub/include
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/3.5.0/os_stub
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/3.5.0/os_stub/cryptlib_null
NV_RM_CFLAGS += -I$(src)/src/nvidia/src/libraries/libspdm/nvidia
NV_RM_CFLAGS += -D_LANGUAGE_C
NV_RM_CFLAGS += -D__NO_CTYPE
NV_RM_CFLAGS += -DNVRM
NV_RM_CFLAGS += -DLOCK_VAL_ENABLED=0
NV_RM_CFLAGS += -DPORT_ATOMIC_64_BIT_SUPPORTED=1
NV_RM_CFLAGS += -DPORT_IS_KERNEL_BUILD=1
NV_RM_CFLAGS += -DPORT_IS_CHECKED_BUILD=0
NV_RM_CFLAGS += -DPORT_MODULE_atomic=1
NV_RM_CFLAGS += -DPORT_MODULE_core=1
NV_RM_CFLAGS += -DPORT_MODULE_cpu=1
NV_RM_CFLAGS += -DPORT_MODULE_crypto=1
NV_RM_CFLAGS += -DPORT_MODULE_debug=1
NV_RM_CFLAGS += -DPORT_MODULE_memory=1
NV_RM_CFLAGS += -DPORT_MODULE_safe=1
NV_RM_CFLAGS += -DPORT_MODULE_string=1
NV_RM_CFLAGS += -DPORT_MODULE_sync=1
NV_RM_CFLAGS += -DPORT_MODULE_thread=1
NV_RM_CFLAGS += -DPORT_MODULE_time=1
NV_RM_CFLAGS += -DPORT_MODULE_util=1
NV_RM_CFLAGS += -DPORT_MODULE_example=0
NV_RM_CFLAGS += -DPORT_MODULE_mmio=0
NV_RM_CFLAGS += -DRS_STANDALONE=0
NV_RM_CFLAGS += -DRS_STANDALONE_TEST=0
NV_RM_CFLAGS += -DRS_COMPATABILITY_MODE=1
NV_RM_CFLAGS += -DRS_PROVIDES_API_STATE=0
NV_RM_CFLAGS += -DNV_CONTAINERS_NO_TEMPLATES
NV_RM_CFLAGS += -DINCLUDE_NVLINK_LIB
NV_RM_CFLAGS += -DINCLUDE_NVSWITCH_LIB
NV_RM_CFLAGS += -DNV_PRINTF_STRINGS_ALLOWED=1
NV_RM_CFLAGS += -DNV_ASSERT_FAILED_USES_STRINGS=1
NV_RM_CFLAGS += -DPORT_ASSERT_FAILED_USES_STRINGS=1
NV_RM_CFLAGS += -DLIBSPDM_CONFIG=\"nvspdm_rmconfig.h\"
NV_RM_CFLAGS += -DNDEBUG
NV_RM_CFLAGS += -Werror-implicit-function-declaration
NV_RM_CFLAGS += -Wwrite-strings
NV_RM_CFLAGS += -Wundef
NV_RM_CFLAGS += -fno-common
NV_RM_CFLAGS += -fno-stack-protector
NV_RM_CFLAGS += -fno-pic
NV_RM_CFLAGS += -ffunction-sections
NV_RM_CFLAGS += -fdata-sections
NV_RM_CFLAGS += -Wno-error

ifeq ($(ARCH),x86_64)
  NV_RM_CFLAGS += -msoft-float -mno-mmx -mno-sse -mno-sse2 -mno-3dnow
endif

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-rm-y), $(NV_RM_CFLAGS))

NV_RM_CFLAGS_EOF

} >> "$MK"

# ===========================================================================
# nvidia-modeset.ko
# ===========================================================================

{
echo "###########################################################################"
echo "# Module: nvidia-modeset.ko"
echo "###########################################################################"
echo
echo "obj-\$(CONFIG_DRM_NVIDIA) += nvidia-modeset.o"
echo

# Interface-layer objects
write_obj_var "nvidia-modeset-if-y" "$nv_modeset_if_objs"

# Core C objects
write_obj_var "nvidia-modeset-core-y" "$nv_modeset_c_objs"

# Core C++ objects
write_obj_var "nvidia-modeset-cxx-y" "$nv_modeset_cxx_objs"

# Shader objects
if [ ${#SHADER_NAMES[@]} -gt 0 ]; then
    echo "nvidia-modeset-shaders-y := \\"
    for tag in "${SHADER_NAMES[@]}"; do
        echo "  shaders/${tag}_shaders.xz.o \\"
    done | sed '$ s/ \\$//'
    echo
    echo
else
    echo "nvidia-modeset-shaders-y :="
    echo
fi

echo "nvidia-modeset-y := \$(nvidia-modeset-if-y) \$(nvidia-modeset-core-y) \$(nvidia-modeset-cxx-y) \$(nvidia-modeset-shaders-y) g_nv_kms_nvid_string.o"
echo

# C++ vtables/COMDAT groups become invalid after ld -r (multiple groups
# share a merged .rodata). GNU objcopy then fails BTF embedding with
# "invalid entry in group" / "corrupted group section" — which is the
# aarch64 build failure (OBJCOPY=objcopy). NVIDIA's own modeset Makefile
# passes --force-group-allocation for the same reason (discards groups on
# relocatable links). Kbuild applies LDFLAGS_$(@F) via ld_flags.
echo "# Discard C++ COMDAT groups on relocatable link (see NVIDIA --force-group-allocation)"
echo "LDFLAGS_nvidia-modeset.o := --force-group-allocation"
echo

# NV_KMS ID string generation
cat << NV_KMS_NVID_EOF
# Generated version identification string for nvidia-modeset.ko
\$(obj)/g_nv_kms_nvid_string.c: FORCE
	@mkdir -p \$(@D)
	@echo 'const char NV_KMS_ID[] = "nvidia id: NVIDIA Open Kernel Mode Setting Driver  ${NV_VERSION}";' > \$@
	@echo 'const char *const pNV_KMS_ID = NV_KMS_ID + 11;' >> \$@

clean-files += g_nv_kms_nvid_string.c

NV_KMS_NVID_EOF

# Interface-layer CFLAGS
cat << 'MODESET_IF_CFLAGS_EOF'
NVIDIA_MODESET_IF_CFLAGS := -I$(obj)
NVIDIA_MODESET_IF_CFLAGS += -I$(src)/kernel-open/common/inc
NVIDIA_MODESET_IF_CFLAGS += -I$(src)/kernel-open
NVIDIA_MODESET_IF_CFLAGS += -I$(src)/kernel-open/nvidia-modeset
NVIDIA_MODESET_IF_CFLAGS += -DNV_KERNEL_INTERFACE_LAYER
NVIDIA_MODESET_IF_CFLAGS += -UDEBUG -U_DEBUG -DNDEBUG -DNV_BUILD_MODULE_INSTANCES=0
NVIDIA_MODESET_IF_CFLAGS += -DNVKMS_CONFIG_FILE_SUPPORTED=1
NVIDIA_MODESET_IF_CFLAGS += -Wno-error

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-modeset-if-y), $(NVIDIA_MODESET_IF_CFLAGS))
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/functions.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/symbols.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/types.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/generic.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/macros.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/patches.h
NVIDIA_MODESET_IF_CFLAGS += -include $(obj)/conftest/headers.h
NV_OBJECTS_DEPEND_ON_CONFTEST += $(nvidia-modeset-if-y)

MODESET_IF_CFLAGS_EOF

# Core C CFLAGS for modeset
cat << 'MODESET_CORE_CFLAGS_EOF'
NV_MODESET_CORE_CFLAGS := -U__KERNEL__
NV_MODESET_CORE_CFLAGS += -isystem $(shell $(CC) -print-file-name=include)
NV_MODESET_CORE_CFLAGS += -include $(src)/src/common/sdk/nvidia/inc/cpuopsys.h
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/sdk/nvidia/inc
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/sdk/nvidia/inc/hw
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/shared/inc
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/inc
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/softfloat/nvidia
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/softfloat/source/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/softfloat/source/8086-SSE
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/common/utils/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/common/inc
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/modeset
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/os-interface/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/kapi/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia/arch/nvalloc/unix/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/kapi/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/displayport/inc
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/displayport/inc/dptestutil
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/inc/displayport
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/nvidia-3d/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/nvidia-push/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/nvidia-3d/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/nvidia-push/include
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/xzminidec/interface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/common/unix/nvidia-headsurface
NV_MODESET_CORE_CFLAGS += -I$(src)/src/nvidia-modeset/src/shaders
NV_MODESET_CORE_CFLAGS += -DNDEBUG
NV_MODESET_CORE_CFLAGS += -D_LANGUAGE_C
NV_MODESET_CORE_CFLAGS += -D__NO_CTYPE
NV_MODESET_CORE_CFLAGS += -DNV_CPU_INTRINSICS_KERNEL
NV_MODESET_CORE_CFLAGS += -DNVHDMIPKT_RM_CALLS_INTERNAL=0
NV_MODESET_CORE_CFLAGS += -DNVHDMIPKT_NVKMS
NV_MODESET_CORE_CFLAGS += -DSOFTFLOAT_ROUND_ODD
NV_MODESET_CORE_CFLAGS += -DSOFTFLOAT_FAST_DIV32TO16
NV_MODESET_CORE_CFLAGS += -DSOFTFLOAT_FAST_DIV64TO32
NV_MODESET_CORE_CFLAGS += -DNVT_USE_NVKMS
NV_MODESET_CORE_CFLAGS += -DNV_SMG_IN_NVKMS
NV_MODESET_CORE_CFLAGS += -DNV_PUSH_IN_KERNEL
NV_MODESET_CORE_CFLAGS += -DNV_XZ_CUSTOM_MEM_HOOKS
NV_MODESET_CORE_CFLAGS += -DNV_XZ_USE_NVTYPES
NV_MODESET_CORE_CFLAGS += -DXZ_DEC_SINGLE
NV_MODESET_CORE_CFLAGS += -DXZ_INTERNAL_CRC32=1
NV_MODESET_CORE_CFLAGS += -O2
NV_MODESET_CORE_CFLAGS += -fno-common
NV_MODESET_CORE_CFLAGS += -fno-stack-protector
NV_MODESET_CORE_CFLAGS += -fno-pic
NV_MODESET_CORE_CFLAGS += -Wno-error

ifeq ($(ARCH),x86_64)
  NV_MODESET_CORE_CFLAGS += -msoft-float -mno-mmx -mno-sse -mno-sse2 -mno-3dnow
endif

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-modeset-core-y), $(NV_MODESET_CORE_CFLAGS))

MODESET_CORE_CFLAGS_EOF

# C++ compilation rule and CFLAGS
cat << 'CXX_RULE_EOF'
# C++ compilation support for DisplayPort code.
# Kbuild has no built-in rule for .cpp files.  We add -x c++ to per-object
# CFLAGS and provide a pattern rule so make can produce .o from .cpp using
# the same compiler command used for .c files.
# -g0 is needed because pahole (BTF) can't handle C++
NV_CXX_FLAGS := -x c++ -std=gnu++11 -fno-operator-names -fno-rtti -g0
NV_CXX_FLAGS += -fno-exceptions -fcheck-new
NV_CXX_FLAGS += -Wno-missing-declarations

# The GCC randomize_layout plugin crashes on C++ code (ICE in
# is_pure_ops_struct / dp_linkedlist.h). Strip it and ftrace/mcount
# instrumentation: kernel ftrace does not work with C++ comdat sections
# and -pg/-mfentry/-mrecord-mcount cause __mcount_loc linker errors
# (references to discarded comdat sections) with --gc-sections.
NV_MODESET_CXX_CFLAGS := $(filter-out -fplugin% -pg -mfentry -mrecord-mcount,$(NV_MODESET_CORE_CFLAGS)) $(NV_CXX_FLAGS)

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-modeset-cxx-y), $(NV_MODESET_CXX_CFLAGS))

# Custom C++ compilation command.  The standard kbuild c_flags includes
# -include compiler_types.h, which redefines "auto" to __auto_type (a GCC C
# extension that is invalid in C++).  We replicate c_flags without that
# force-include.  The per-object CFLAGS already contain -x c++.
quiet_cmd_nv_cxx_o_cpp = CXX [M]  $@
      cmd_nv_cxx_o_cpp = $(CC) -Wp,-MMD,$(depfile) \
	$(NOSTDINC_FLAGS) $(LINUXINCLUDE) \
	$(filter-out -fplugin% -pg -mfentry -mrecord-mcount,$(_c_flags)) \
	$(modkern_cflags) \
	$(basename_flags) $(modname_flags) \
	-c -o $@ $<

$(obj)/%.o: $(src)/%.cpp FORCE
	$(call if_changed_dep,nv_cxx_o_cpp)

CXX_RULE_EOF

# Shader rules
if [ ${#SHADER_NAMES[@]} -gt 0 ]; then
cat >> "$MK" << 'SHADER_RULES_EOF'
# Shader binary embedding: XZ-compress the raw shader data, then convert
# to an ELF object via objcopy so it can be linked into nvidia-modeset.ko.
quiet_cmd_xz_shader = XZ      $@
      cmd_xz_shader = xz -ce -C none < $< > $@

quiet_cmd_objcopy_shader = OBJCOPY $@
      cmd_objcopy_shader = \
	(cd $(dir $<) && \
	$(OBJCOPY) \
	  --input-target=binary \
	  --output-target=$(if $(filter x86 x86_64,$(SRCARCH) $(ARCH)),elf64-x86-64,elf64-littleaarch64) \
	  --binary-architecture=$(if $(filter x86 x86_64,$(SRCARCH) $(ARCH)),i386:x86-64,aarch64) \
	  --rename-section .data=.rodata,alloc,load,readonly,data,contents \
	  $(notdir $<) $(abspath $@))

SHADER_RULES_EOF

for tag in "${SHADER_NAMES[@]}"; do
cat >> "$MK" << SHADER_TAG_EOF
targets += shaders/${tag}_shaders.xz shaders/${tag}_shaders.xz.o

\$(obj)/shaders/${tag}_shaders.xz: \$(src)/src/nvidia-modeset/src/shaders/g_${tag}_shaders FORCE
	\$(Q)mkdir -p \$(@D)
	\$(call if_changed,xz_shader)

\$(obj)/shaders/${tag}_shaders.xz.o: \$(obj)/shaders/${tag}_shaders.xz FORCE
	\$(call if_changed,objcopy_shader)

SHADER_TAG_EOF
done
fi

} >> "$MK"

# ===========================================================================
# nvidia-drm.ko
# ===========================================================================

{
echo "###########################################################################"
echo "# Module: nvidia-drm.ko"
echo "###########################################################################"
echo
echo "obj-\$(CONFIG_DRM_NVIDIA) += nvidia-drm.o"
echo

write_obj_var "nvidia-drm-y" "$nv_drm_objs"

cat << 'DRM_CFLAGS_EOF'
NVIDIA_DRM_CFLAGS := -I$(obj)
NVIDIA_DRM_CFLAGS += -I$(src)/kernel-open/common/inc
NVIDIA_DRM_CFLAGS += -I$(src)/kernel-open
NVIDIA_DRM_CFLAGS += -I$(src)/kernel-open/nvidia-drm
NVIDIA_DRM_CFLAGS += -DNV_KERNEL_INTERFACE_LAYER
NVIDIA_DRM_CFLAGS += -UDEBUG -U_DEBUG -DNDEBUG -DNV_BUILD_MODULE_INSTANCES=0
NVIDIA_DRM_CFLAGS += -Wno-error

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-drm-y), $(NVIDIA_DRM_CFLAGS))
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/functions.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/symbols.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/types.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/generic.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/macros.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/patches.h
NVIDIA_DRM_CFLAGS += -include $(obj)/conftest/headers.h
NV_OBJECTS_DEPEND_ON_CONFTEST += $(nvidia-drm-y)

DRM_CFLAGS_EOF

} >> "$MK"

# ===========================================================================
# nvidia-uvm.ko
# ===========================================================================

{
echo "###########################################################################"
echo "# Module: nvidia-uvm.ko"
echo "###########################################################################"
echo
echo "obj-\$(CONFIG_DRM_NVIDIA_UVM) += nvidia-uvm.o"
echo

write_obj_var "nvidia-uvm-y" "$nv_uvm_objs"

cat << 'UVM_CFLAGS_EOF'
NVIDIA_UVM_CFLAGS := -I$(obj)
NVIDIA_UVM_CFLAGS += -I$(src)/kernel-open/common/inc
NVIDIA_UVM_CFLAGS += -I$(src)/kernel-open
NVIDIA_UVM_CFLAGS += -DNV_KERNEL_INTERFACE_LAYER
NVIDIA_UVM_CFLAGS += -DNVIDIA_UVM_ENABLED
NVIDIA_UVM_CFLAGS += -DNVIDIA_UNDEF_LEGACY_BIT_MACROS
NVIDIA_UVM_CFLAGS += -DLinux -D__linux__
NVIDIA_UVM_CFLAGS += -I$(src)/kernel-open/nvidia-uvm
NVIDIA_UVM_CFLAGS += -Wno-error

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-uvm-y), $(NVIDIA_UVM_CFLAGS))
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/functions.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/symbols.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/types.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/generic.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/macros.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/patches.h
NVIDIA_UVM_CFLAGS += -include $(obj)/conftest/headers.h
NV_OBJECTS_DEPEND_ON_CONFTEST += $(nvidia-uvm-y)

UVM_CFLAGS_EOF

} >> "$MK"

# ===========================================================================
# nvidia-peermem.ko
# ===========================================================================

{
echo "###########################################################################"
echo "# Module: nvidia-peermem.ko"
echo "###########################################################################"
echo
echo "obj-\$(CONFIG_DRM_NVIDIA_PEERMEM) += nvidia-peermem.o"
echo

write_obj_var "nvidia-peermem-y" "$nv_peermem_objs"

cat << 'PEERMEM_CFLAGS_EOF'
NVIDIA_PEERMEM_CFLAGS := -I$(obj)
NVIDIA_PEERMEM_CFLAGS += -I$(src)/kernel-open/common/inc
NVIDIA_PEERMEM_CFLAGS += -I$(src)/kernel-open
NVIDIA_PEERMEM_CFLAGS += -DNV_KERNEL_INTERFACE_LAYER
NVIDIA_PEERMEM_CFLAGS += -I$(src)/kernel-open/nvidia-peermem
NVIDIA_PEERMEM_CFLAGS += -UDEBUG -U_DEBUG -DNDEBUG -DNV_BUILD_MODULE_INSTANCES=0
NVIDIA_PEERMEM_CFLAGS += -Wno-error

$(call ASSIGN_PER_OBJ_CFLAGS, $(nvidia-peermem-y), $(NVIDIA_PEERMEM_CFLAGS))
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/functions.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/symbols.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/types.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/generic.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/macros.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/patches.h
NVIDIA_PEERMEM_CFLAGS += -include $(obj)/conftest/headers.h
NV_OBJECTS_DEPEND_ON_CONFTEST += $(nvidia-peermem-y)

PEERMEM_CFLAGS_EOF

} >> "$MK"

# ===========================================================================
# Conftest dependency for all interface-layer objects
# ===========================================================================

cat >> "$MK" << 'CONFTEST_DEP_EOF'

###########################################################################
# Wire conftest dependencies
###########################################################################
$(addprefix $(obj)/,$(NV_OBJECTS_DEPEND_ON_CONFTEST)): $(NV_CONFTEST_HEADERS)

CONFTEST_DEP_EOF

echo "    Done."
echo

##############################################################################
# 7. Patch drivers/gpu/drm/Kconfig
##############################################################################

echo "==> Patching drivers/gpu/drm/Kconfig ..."

DRM_KCONFIG="$KERNEL_DIR/drivers/gpu/drm/Kconfig"

if grep -q 'source.*nvidia/Kconfig' "$DRM_KCONFIG" 2>/dev/null; then
    echo "    Already patched, skipping."
else
    # Insert after the nouveau/Kconfig line (alphabetical: nvidia comes after nouveau)
    sed -i '/^source.*"drivers\/gpu\/drm\/nouveau\/Kconfig"/a source "drivers/gpu/drm/nvidia/Kconfig"' \
        "$DRM_KCONFIG"
    echo "    Done."
fi
echo

##############################################################################
# 8. Patch drivers/gpu/drm/Makefile
##############################################################################

echo "==> Patching drivers/gpu/drm/Makefile ..."

DRM_MAKEFILE="$KERNEL_DIR/drivers/gpu/drm/Makefile"

if grep -q 'CONFIG_DRM_NVIDIA' "$DRM_MAKEFILE" 2>/dev/null; then
    echo "    Already patched, skipping."
else
    # Insert after the nouveau line
    sed -i '/^obj-\$(CONFIG_DRM_NOUVEAU)/a obj-$(CONFIG_DRM_NVIDIA) += nvidia/' \
        "$DRM_MAKEFILE"
    echo "    Done."
fi
echo

##############################################################################
# 9. Safe Clang/in-tree symbol detection improvement
##############################################################################

echo "==> Adding safe post-conftest trigger for Clang builds ..."

cat >> "$MK" << 'SAFE_CONFTEST_TRIGGER'

###########################################################################
# Safe trigger: Run after modules_prepare / modpost
# (helps with early conftest issues on Clang without breaking rules)
###########################################################################

.PHONY: nvidia-conftest-refresh

nvidia-conftest-refresh: FORCE
	@echo "  [NVIDIA] Post-conftest refresh (Clang/in-tree compatibility)"

# Make the main conftest headers depend on this phony target
$(NV_CONFTEST_HEADERS): | nvidia-conftest-refresh

SAFE_CONFTEST_TRIGGER

echo "    Done (safe post-conftest trigger added)."
echo

echo "==> Installation complete."
echo
echo "To build:"
echo "  cd $KERNEL_DIR"
echo "  make menuconfig    # Enable: Device Drivers → Graphics → NVIDIA GPU"
echo "  make modules       # or: make -j\$(nproc)"
echo
