# OpenMandriva kernel config layout

## Merge order

`CreateConfig` in `kernel.spec` builds each architecture’s final `.config` as:

1. `ARCH-omv-defconfig` — arch / platform / CPU / SoC specifics  
2. `generic-omv-defconfig` — cross-arch shared settings not in a fragment  
3. `*.fragment` — shared subsystem policy (later fragments override earlier only by filename glob order; prefer one owner per key)  
4. `*.overrides` / `temporary-workarounds.overrides` — variant and temporary fixes  
5. `clangify` / `serverize` / `FIXED_CONFIGS`  
6. `olddefconfig`

Later files win. Invalid options for an arch are dropped by `olddefconfig`.

## Ownership rules

| Setting kind | Where it lives |
|---|---|
| Shared intentional enable/disable for all arches that support it | `*.fragment` or `generic-omv-defconfig` |
| Arch / platform / CPU only | `*-omv-defconfig` |
| Temporary workaround | `temporary-workarounds.overrides` |
| znver1-only | `znver1.overrides` |

### `# CONFIG_* is not set`

These lines are **intentional policy**, not noise. They record an explicit disable vs “option never mentioned / did not exist in an older tree”. **Do not strip them** from fragments (or anywhere else they appear).

### Toolchain noise

Do not store `CONFIG_CC_VERSION_TEXT`, `CONFIG_CLANG_VERSION`, `CONFIG_BUILD_SALT`, `CONFIG_CC_IS_*`, etc. in packaged configs; the build recomputes them.

## Maintenance

```bash
# Duplication stats
./manage-kernel-configs.py stats

# Strip fragment-owned / generic-dup / toolchain noise from arch bases
./manage-kernel-configs.py strip-duplicates

# Extract same-valued fat-arch (x86/i386/arm/arm64) keys into fragments/generic
./manage-kernel-configs.py extract-common
./manage-kernel-configs.py extract-common --dry-run

# Merge like the package build and save final .config files
./manage-kernel-configs.py verify --outdir config-verify/out

# Compare two final configs (fat = strict, slim = subset)
./manage-kernel-configs.py compare --mode strict  before.config after.config
./manage-kernel-configs.py compare --mode subset  before.config after.config
```

`./auto-clean-base-configs.sh` is a thin wrapper around the same tool.

## Slim architectures

Fragments apply to every arch. Growing enablement on powerpc/riscv/loongarch toward the same module set (e.g. media devices as modules) is intentional. Options that do not exist on an arch disappear at `olddefconfig`. Uncommon modules can later be split into subpackages.

## Verification notes (post-extraction)

Fat arches (`x86`, `i386`, `arm`, `arm64`): final merged `.config` must match pre-cleanup
baselines (`compare --mode strict`), aside from toolchain noise.

Slim arches (`powerpc`, `riscv`, `loongarch`): expect **growth** toward the shared
fragment set (many `n→m` / `n→y`). Built-in drivers that fat arches carry as modules
may become modules (`y→m`); that is intentional for a unified module-oriented config
(initramfs loads boot drivers).

Known arch Kconfig interactions after unification:

- **powerpc + hibernation:** enabling `HIBERNATION` (shared policy) disables
  `ARCH_HAS_STRICT_KERNEL_RWX` on powerpc (`select … if !HIBERNATION`). That drops
  `STRICT_KERNEL_RWX` / `DEBUG_WX` on that arch only — an upstream limitation, not a
  merge bug.
- **`SYSFB_SIMPLEFB`:** shared policy prefers simplefb/simpledrm; `DRM_EFIDRM` is
  mutually exclusive with `SYSFB_SIMPLEFB` and will not appear where simplefb is on.

## Arch-specific overrides

- `znver1.overrides` — AMD znver1 CPU-focused build
- `arm64.overrides` — USB boot path built-in (`USB`/`xhci`/`ehci`/`SCSI`/
  `BLK_DEV_SD`/`USB_STORAGE`/`USB_UAS` =y). Needed because many aarch64 boards
  boot from USB mass-storage and `USB_STORAGE` cannot be `=y` while `SCSI` is
  modular. Other arches keep these as modules via fragments.
- `temporary-workarounds.overrides` — short-lived force-offs

## LSM / MAC policy

`security.fragment` default stack is minimal:

```
CONFIG_LSM="landlock,bpf"
```

**AppArmor**, **SELinux**, **Yama**, and related stacking LSMs stay **built-in**
(bool options) so users can opt in at boot, but they are **not** in the default
list (no ptrace hardening / full MAC unless chosen):

```
lsm=landlock,yama,bpf
lsm=landlock,lockdown,yama,loadpin,safesetid,apparmor,integrity,bpf
lsm=landlock,lockdown,yama,loadpin,safesetid,selinux,integrity,bpf
```

