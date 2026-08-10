# In-Tree Kernel Build Support for NVIDIA Open GPU Kernel Modules

## Overview

This document describes the changes made to enable building the NVIDIA open GPU
kernel modules as part of a standard Linux kernel build, similar to how amdgpu
or Intel GPU modules are built. The modules appear in `make menuconfig` and
build alongside other kernel modules during `make modules`.

**Minimum supported kernel version:** 7.0 (compatibility shims for older
kernels have been dropped in the build system; the driver source's conftest
mechanism still provides runtime feature detection).

## Files Added

### `install-to-kernel-tree.sh`

A bash script that takes a kernel source directory as its sole argument and
performs the complete integration:

```bash
./install-to-kernel-tree.sh /usr/src/linux-7.0.10
```

It performs these steps:

1. **Copies source files** into `drivers/gpu/drm/nvidia/` preserving the
   original directory layout (`kernel-open/` for interface layer,
   `src/` for the RM core and shared libraries).

2. **Parses upstream source lists** (`*.Kbuild`, `srcs.mk`) dynamically to
   discover which files to compile, so future file additions/removals are
   handled automatically.

3. **Generates `Kconfig`** with three options:
   - `DRM_NVIDIA` — main tristate (depends on DRM, PCI, X86_64 || ARM64)
   - `DRM_NVIDIA_UVM` — UVM tristate (defaults to match DRM_NVIDIA)
   - `DRM_NVIDIA_PEERMEM` — GPUDirect RDMA tristate (depends on INFINIBAND)

4. **Generates a Kbuild `Makefile`** that produces up to five modules:
   - `nvidia.ko` — core GPU resource manager (RM core + interface layer)
   - `nvidia-modeset.ko` — kernel mode setting (C and C++ core + interface)
   - `nvidia-drm.ko` — DRM/KMS interface
   - `nvidia-uvm.ko` — unified virtual memory
   - `nvidia-peermem.ko` — GPUDirect RDMA (only if INFINIBAND is available)

5. **Patches** `drivers/gpu/drm/Kconfig` and `drivers/gpu/drm/Makefile` to
   wire the nvidia subdirectory into the kernel build, inserting lines after
   the nouveau driver entries.

The script is idempotent — re-running it cleans and regenerates everything.

### `kernel-open/conftest.sh` (modified)

The conftest.sh feature-detection script was modified to support kernel 7.0+:

- **`vmlinux.symvers` support:** Kernel 7.0 generates `vmlinux.symvers`
  alongside or instead of `Module.symvers` for built-in symbol exports.
  The original code only checked `Module.symvers`. The fix adds a loop
  that checks both files and only greps files that actually exist (avoiding
  exit code 2 from grep on missing files).

## Architecture Decisions

### Three-Layer CFLAGS Architecture

The NVIDIA source tree has two fundamentally different code layers that need
different compiler flags:

1. **Interface layer** (`kernel-open/`): Bridges kernel APIs and the RM core.
   These files `#include <linux/*.h>` and need the full kbuild environment
   (`__KERNEL__`, kernel include paths, conftest results).

2. **RM core** (`src/nvidia/`, `src/nvidia-modeset/`, `src/common/`):
   Platform-independent code that uses NVIDIA's internal SDK headers. These
   files assume a userspace-like environment and conflict with kernel headers
   in several ways.

The generated Makefile uses kbuild's `CFLAGS_<object>.o` mechanism via an
`ASSIGN_PER_OBJ_CFLAGS` macro to apply different flags to each object:

| Layer | Key Flags | Reason |
|---|---|---|
| Interface | `-DNV_KERNEL_INTERFACE_LAYER`, `-I$(src)/kernel-open/common/inc`, `-Wno-error` | Kernel headers, conftest integration |
| RM core | `-U__KERNEL__`, `-isystem $(CC -print-file-name=include)`, SDK `-I` paths | SDK expects non-kernel environment; needs compiler builtins for `stdatomic.h` |
| C++ (DisplayPort) | `-x c++`, `-std=gnu++11`, custom compilation rule without `compiler_types.h` | Kernel's `auto → __auto_type` rewrite breaks C++ |

### Conftest CFLAGS

The conftest system (compile-time kernel feature detection) requires special
CFLAGS handling for the in-tree build:

- **Absolute paths:** `conftest.sh` does `cd "$SCRIPTDIR"` (into the
  `kernel-open/` directory), which breaks all relative paths in kbuild's
  `LINUXINCLUDE` and `objtree`/`srctree`. The Makefile converts these to
  absolute paths using `$(abspath ...)` and `$(subst ./,...)`.

- **Selective KBUILD_CFLAGS:** Cannot use KBUILD_CFLAGS wholesale because it
  contains `-Werror` which breaks conftest's detection logic (which
  intentionally triggers compiler errors to test for feature presence). Only
  essential flags like `-std=gnu11`, `-fms-extensions`, etc., are extracted
  via `$(filter ...)`.

### C++ Support

The DisplayPort sources use C++, which is unusual for kernel modules. The
solution:

- A custom `cmd_nv_cxx_o_cpp` compilation command is defined that replicates
  kbuild's standard C compilation but omits `-include compiler_types.h`
  (which redefines `auto` to `__auto_type`, breaking C++).
- Per-object CFLAGS include `-x c++` and C++ specific options.
- A pattern rule `$(obj)/%.o: $(src)/%.cpp` handles .cpp files.

### Shader Embedding

`nvidia-modeset.ko` embeds pre-compiled shader binaries. These are:

1. XZ-compressed from raw binary files
2. Converted to ELF objects via `objcopy`
3. Linked into the module

The `objcopy` command uses a subshell `(cd ... && objcopy ...)` to control
symbol names without affecting the parent shell's working directory (which
would break kbuild's `.cmd` file writing).

### Version ID Strings

The upstream build system generates `g_nvid_string.c` with version
identification. The in-tree Makefile generates equivalent files at build time:
- `g_nvrm_nvid_string.c` → provides `pNVRM_ID` for `nvidia.ko`
- `g_nv_kms_nvid_string.c` → provides `pNV_KMS_ID` for `nvidia-modeset.ko`

## Key Build Issues and Solutions

### 1. Missing Compiler Built-in Headers

**Problem:** RM core code `#include`s `<stdatomic.h>` and `<stddef.h>`, which
come from the compiler's built-in include path. The kernel build uses
`-nostdinc` which strips this path.

**Fix:** Added `-isystem $(shell $(CC) -print-file-name=include)` to RM core
and modeset core CFLAGS.

### 2. Include Path Conflicts

**Problem:** Interface-layer headers (`kernel-open/common/inc/`) and RM core
SDK headers have files with colliding names (e.g., `rs_access.h`). Including
interface paths in RM core compilation caused wrong headers to be used.

**Fix:** Strict separation — interface-layer include paths are only in
interface-layer CFLAGS; RM core CFLAGS only reference SDK paths.

### 3. `__KERNEL__` Macro Conflicts

**Problem:** RM core and modeset core code includes files (e.g., `xzminidec`)
that have `#ifdef __KERNEL__` blocks which try to `#include <asm/unaligned.h>`,
a kernel header not available in the RM core compilation environment. Also,
`XZ_INTERNAL_CRC32` defaults to 0 when `__KERNEL__` is defined, breaking the
XZ decoder.

**Fix:** Added `-U__KERNEL__` to RM core and modeset core CFLAGS, and
explicitly defined `-DXZ_INTERNAL_CRC32=1`.

### 4. C++ `auto` Keyword Conflict

**Problem:** Kbuild force-includes `compiler_types.h` which has:
```c
#define auto __auto_type
```
This is a GCC C extension that breaks C++ code using the `auto` keyword.

**Fix:** Custom C++ compilation command (`cmd_nv_cxx_o_cpp`) that replicates
kbuild's standard compilation but omits the `-include compiler_types.h`.

### 5. Conftest Relative Path Breakage

**Problem:** `conftest.sh` changes directory to its own location (`cd
"$SCRIPTDIR"`), but kbuild's `LINUXINCLUDE` and `objtree`/`srctree` use
relative paths (e.g., `-I./include`, `objtree = .`). After the `cd`, these
paths point to the wrong directories, causing ALL conftest tests to produce
wrong results.

**Fix:** The Makefile converts all paths passed to conftest to absolute:
- `NV_KERNEL_SOURCES := $(abspath $(srctree))`
- `NV_KERNEL_OUTPUT  := $(abspath $(objtree))`
- `NV_CONFTEST_LINUXINCLUDE := $(subst ./,$(abspath $(srctree))/,$(LINUXINCLUDE))`

### 6. Conftest uts_release Prerequisite

**Problem:** `$(NV_CONFTEST_HEADERS): $(obj)/conftest/uts_release` as a normal
prerequisite caused the uts_release file's content to be concatenated into all
conftest headers via `cat $^` recipes.

**Fix:** Changed to an order-only prerequisite with `|`:
`$(NV_CONFTEST_HEADERS): | $(obj)/conftest/uts_release`

### 7. `vmlinux.symvers` in Kernel 7.0+

**Problem:** Kernel 7.0 generates `vmlinux.symvers` instead of (or alongside)
`Module.symvers`. `conftest.sh` only checked `Module.symvers`, causing symbol
presence checks (like `timer_delete_sync`) to fail.

**Fix:** Modified `conftest.sh` to check both `Module.symvers` and
`vmlinux.symvers`, iterating over whichever files actually exist.

### 8. Shader Objcopy Working Directory

**Problem:** The `cmd_objcopy_shader` command used `cd $(dir $<) && objcopy
...` to control symbol naming. Kbuild's `if_changed` macro appends `.cmd`
file writes in the same shell, but after the `cd`, the relative `.cmd` path
resolves to the wrong directory.

**Fix:** Wrapped the `cd` in a subshell: `(cd $(dir $<) && objcopy ...)`.
After the subshell exits, the parent shell's working directory is unchanged.

## Updating to Future Versions

The install script is designed to accommodate changes in the upstream
`open-gpu-kernel-modules` repository:

1. **Source file lists** are parsed dynamically from `*.Kbuild` and `srcs.mk`
   files — new/removed/renamed source files are handled automatically.

2. **Conftest tests** are extracted from all `.Kbuild` files — new feature
   detection tests are picked up automatically.

3. **Shader binaries** are discovered by globbing
   `src/nvidia-modeset/src/shaders/g_*_shaders`.

4. **Source trees** are copied wholesale (`cp -a`) preserving the original
   directory structure.

To update: check out the new version and re-run the script:

```bash
cd open-gpu-kernel-modules
git pull  # or checkout new tag
./install-to-kernel-tree.sh /usr/src/linux-X.Y.Z
cd /usr/src/linux-X.Y.Z
make olddefconfig
make modules -j$(nproc)
```

### Things That May Need Manual Attention

- **New subdirectories** under `kernel-open/` (new modules) — the script
  currently copies specific known directories; a new module would need a new
  `cp -a` line and corresponding Makefile section.
- **New CFLAGS defines** or include paths in the upstream build system — these
  may need to be mirrored in the relevant CFLAGS blocks.
- **Kconfig dependency changes** (e.g., new hardware requirements) — the
  Kconfig template in the script would need updating.
