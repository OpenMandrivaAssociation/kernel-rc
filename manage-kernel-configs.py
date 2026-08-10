#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""OpenMandriva kernel packaging config helpers.

Manages arch defconfigs, generic-omv-defconfig, and *.fragment files so shared
settings live in one place.

IMPORTANT:
  '# CONFIG_* is not set' is intentional policy (disable vs never decided).
  Never strip those lines during cleanup.

Merge order (matches kernel.spec CreateConfig):
  arch-omv-defconfig → generic-omv-defconfig → *.fragment → *.overrides
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Packaging root = directory containing this script / the defconfigs
ROOT = Path(__file__).resolve().parent

FAT_ARCHES = ("x86", "i386", "arm", "arm64")
ALL_ARCHES = ("x86", "i386", "arm", "arm64", "powerpc", "riscv", "loongarch")

# Toolchain / build artifacts that must not live in packaged configs
NOISE_KEYS = {
    "CC_VERSION_TEXT",
    "CC_IS_GCC",
    "CC_IS_CLANG",
    "CC_CAN_LINK",
    "CC_CAN_LINK_STATIC",
    "CC_HAS_ASM_GOTO",
    "CC_HAS_ASM_GOTO_OUTPUT",
    "CC_HAS_ASM_GOTO_TIED_OUTPUT",
    "CC_HAS_ASM_INLINE",
    "CC_HAS_NO_PROFILE_FN_ATTR",
    "CC_HAS_COUNTED_BY",
    "CC_HAS_MULTIDIMENSIONAL_NONSTRING",
    "CC_VERSION",
    "CLANG_VERSION",
    "GCC_VERSION",
    "AS_IS_GNU",
    "AS_IS_LLVM",
    "AS_VERSION",
    "AS_HAS_NON_CONST_ULEB128",
    "LD_IS_BFD",
    "LD_IS_LLD",
    "LD_VERSION",
    "LD_ORPHAN_WARN",
    "LD_ORPHAN_WARN_LEVEL",
    "LD_CAN_USE_KEEP_IN_OVERLAY",
    "LLD_VERSION",
    "BUILD_SALT",
    "RUSTC_VERSION_TEXT",
    "RUSTC_VERSION",
    "RUSTC_LLVM_VERSION",
    "PAHOLE_VERSION",
    "TOOLS_SUPPORT_RELR",
    "CC_HAS_AUTO_VAR_INIT_PATTERN",
    "CC_HAS_AUTO_VAR_INIT_ZERO",
    "CC_HAS_AUTO_VAR_INIT_ZERO_BARE",
    "CC_HAS_SIGN_RETURN_ADDRESS",
    "CC_HAS_SANE_STACKPROTECTOR",
}

# Prefix / predicate → destination fragment (first match wins)
# Unmatched shared keys go to generic-omv-defconfig
FRAGMENT_RULES: List[Tuple[str, object]] = []


def _rule(name: str, pred):
    FRAGMENT_RULES.append((name, pred))


def _startswith(*prefixes: str):
    return lambda k: any(k == p or k.startswith(p + "_") or k.startswith(p) for p in prefixes)


# Order matters: more specific first
_rule("media.fragment", lambda k: (
    k.startswith("DVB") or k.startswith("VIDEO") or k.startswith("MEDIA")
    or k.startswith("V4L") or k.startswith("RADIO") or k.startswith("CEC")
    or k.startswith("IR_") or k.startswith("RC_") or k.startswith("VIDEO_")
    or k.startswith("DVB_") or k.startswith("MEDIA_") or k.startswith("VIDEOBUF")
    or k.startswith("VIDEO_V4L") or k in ("MEDIA_SUPPORT", "MEDIA_CAMERA_SUPPORT",
        "MEDIA_ANALOG_TV_SUPPORT", "MEDIA_DIGITAL_TV_SUPPORT", "MEDIA_RADIO_SUPPORT",
        "MEDIA_SDR_SUPPORT", "MEDIA_PLATFORM_SUPPORT", "MEDIA_TEST_SUPPORT")
))
_rule("usb.fragment", lambda k: (
    k.startswith("USB") or k.startswith("TYPEC") or k.startswith("UCSI")
    or k.startswith("NCM_") or "USB_GADGET" in k or k.startswith("GADGET")
    or k.startswith("PHY_QCOM_USB") or k.startswith("NOP_USB")
    or k.startswith("FSL_USB") or k.startswith("KEYSTONE_USB")
))
_rule("sound.fragment", lambda k: (
    k.startswith("SND") or k.startswith("SOUND") or k.startswith("AC97")
    or k == "SOUND"
))
_rule("wireless.fragment", lambda k: (
    k.startswith("WLAN") or k.startswith("CFG80211") or k.startswith("MAC80211")
    or k.startswith("RTW") or k.startswith("ATH") or k.startswith("B43")
    or k.startswith("IWL") or k.startswith("MWIFI") or k.startswith("BRCM")
    or k.startswith("RSI_") or k.startswith("MT7") or k.startswith("RTL8")
    or k.startswith("RTL9") or k.startswith("RT2X00") or k.startswith("WILC")
    or k.startswith("WL_") or k.startswith("WLCORE") or k.startswith("WL18")
    or k.startswith("CW1200") or k.startswith("RSI") or k.startswith("ZD12")
    or k.startswith("HERMES") or k.startswith("P54") or k.startswith("LIBERTAS")
    or k.startswith("USB_NET_RNDIS_WLAN") or k.startswith("PCMCIA_RAYCS")
    or k.startswith("PCMCIA_WL3501") or k.startswith("AIRO") or k.startswith("IPW")
    or k.startswith("IWLEGACY") or k.startswith("IWLWIFI") or k.startswith("IWLDVM")
    or k.startswith("IWLMVM") or k.startswith("IWLMLD") or k.startswith("RAY_")
    or k.startswith("WIL6210") or k.startswith("RSI") or k.startswith("QXDM")
    or k.startswith("QTNFMAC") or k.startswith("WCN36") or k.startswith("WFX")
    or k.startswith("SSB_") or k.startswith("BCMA_")  # bus helpers often tied to wireless
))
_rule("input.fragment", lambda k: (
    k.startswith("INPUT") or k.startswith("KEYBOARD") or k.startswith("MOUSE")
    or k.startswith("TOUCHSCREEN") or k.startswith("JOYSTICK") or k.startswith("TABLET")
    or k.startswith("SERIO") or k.startswith("GAMEPORT") or k.startswith("RMI4")
))
_rule("drm.fragment", lambda k: (
    k.startswith("DRM") or k.startswith("FB_") or k.startswith("FRAMEBUFFER")
    or k.startswith("BACKLIGHT") or k.startswith("LCD_") or k.startswith("VGA_")
    or k.startswith("AGP") or k.startswith("TINYDRM") or k.startswith("HDMI")
    or k == "FB" or k.startswith("LCD_CLASS") or k.startswith("BACKLIGHT_CLASS")
))
_rule("crypto.fragment", lambda k: k.startswith("CRYPTO") or k.startswith("CRC") and not k.startswith("CRASH"))
_rule("scsi.fragment", lambda k: (
    k.startswith("SCSI") or k.startswith("ATA") or k.startswith("SATA")
    or k.startswith("PATA") or k.startswith("AIC") or k.startswith("MEGARAID")
    or k.startswith("FUSION") or k.startswith("RAID_") or k.startswith("MD_")
    or k.startswith("BLK_DEV_MD") or k.startswith("BLK_DEV_DM") or k.startswith("DM_")
    or k.startswith("FCOE") or k.startswith("LIBFC") or k.startswith("SCSI_")
    or k.startswith("CHR_DEV_ST") or k.startswith("CHR_DEV_OSST") or k.startswith("CHR_DEV_SG")
    or k.startswith("CHR_DEV_SCH") or k.startswith("SCSI_PROC_FS")
))
_rule("mtd.fragment", lambda k: k.startswith("MTD"))
_rule("net-phy.fragment", lambda k: (
    k.startswith("PHY_") or k.endswith("_PHY") or "PHYLIB" in k
    or k.startswith("MDIO") or k.startswith("FIXED_PHY")
))
_rule("gpio.fragment", lambda k: k.startswith("GPIO") or k.startswith("PINCTRL"))
_rule("infiniband.fragment", lambda k: k.startswith("INFINIBAND") or k.startswith("MLX4") or k.startswith("MLX5") and "INFINIBAND" in k or k.startswith("IB_"))
_rule("virt.fragment", lambda k: (
    k.startswith("VIRTIO") or k.startswith("VHOST") or k.startswith("VFIO")
    or k.startswith("HYPERV") or k.startswith("XEN") or k.startswith("KVM")
    or k.startswith("VBOX") or k.startswith("VMWARE") or k.startswith("VIRT_")
    or k.startswith("PTP_1588_CLOCK_KVM")
))
_rule("misc-drivers.fragment", lambda k: (
    k.startswith("LEDS") or k.startswith("RTC") or k.startswith("SPI")
    or k.startswith("I2C") or k.startswith("W1") or k.startswith("NFC")
    or k.startswith("PPS") or k.startswith("POWER_SUPPLY") or k.startswith("CHARGER")
    or k.startswith("BATTERY") or k.startswith("REGULATOR") or k.startswith("MFD")
    or k.startswith("PWM") or k.startswith("IIO") or k.startswith("HWMON")
    or k.startswith("SENSORS") or k.startswith("WATCHDOG") or k.startswith("SSB")
    or k.startswith("BCMA") or k.startswith("IPMI") or k.startswith("CROS")
    or k.startswith("GOOGLE") or k.startswith("NEW_LEDS") or k.startswith("LEDS_")
    or k.startswith("SERIAL_") or k.startswith("TI_") or k.startswith("MUX_")
    or k.startswith("EXTCON") or k.startswith("IIO_") or k.startswith("NVEMEM")
    or k.startswith("NVMEM") or k.startswith("EEPROM") or k.startswith("MEMSTICK")
    or k.startswith("MMC") or k.startswith("SDIO") or k.startswith("MEMSTICK")
))


def readconfig(path: Path) -> "OrderedDict[str, str]":
    """Return OrderedDict name -> value ('n' for '# CONFIG_x is not set')."""
    d: "OrderedDict[str, str]" = OrderedDict()
    if not path.is_file():
        return d
    with path.open() as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("CONFIG_"):
                name, val = line[7:].split("=", 1)
                d[name] = val
            elif line.endswith(" is not set") and line.startswith("# CONFIG_"):
                name = line[9:-11]
                d[name] = "n"
    return d


def format_entry(name: str, val: str) -> str:
    # Kconfig only accepts lowercase y/m/n
    if val in ("n", "N"):
        return f"# CONFIG_{name} is not set"
    if val in ("y", "Y", "m", "M"):
        val = val.lower()
    return f"CONFIG_{name}={val}"


def writeconfig(path: Path, cfg: Dict[str, str], *, preserve_not_set: bool = True) -> None:
    """Write sorted config entries. Always preserves 'n' as '# is not set'."""
    lines = [format_entry(k, cfg[k]) for k in sorted(cfg)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def writeconfig_merge_style(path: Path, existing: Dict[str, str], updates: Dict[str, str]) -> None:
    """Merge updates into existing and write sorted."""
    out = dict(existing)
    out.update(updates)
    writeconfig(path, out)


def fragment_paths() -> List[Path]:
    return sorted(ROOT.glob("*.fragment"))


def load_all_fragments() -> Dict[str, Tuple[str, str]]:
    """key -> (value, fragment_filename)"""
    out: Dict[str, Tuple[str, str]] = {}
    for p in fragment_paths():
        for k, v in readconfig(p).items():
            out[k] = (v, p.name)
    return out


def arch_defconfig(arch: str) -> Path:
    return ROOT / f"{arch}-omv-defconfig"


def generic_path() -> Path:
    return ROOT / "generic-omv-defconfig"


def is_noise(key: str) -> bool:
    if key in NOISE_KEYS:
        return True
    if key.startswith("CC_") and key not in ("CC_OPTIMIZE_FOR_PERFORMANCE", "CC_OPTIMIZE_FOR_SIZE",
                                               "CC_OPTIMIZE_FOR_PERFORMANCE_O3"):
        # Keep intentional optimization choices; drop compiler capability probes
        if key.startswith("CC_HAS_") or key in ("CC_VERSION_TEXT", "CC_IS_GCC", "CC_IS_CLANG",
                                                  "CC_CAN_LINK", "CC_CAN_LINK_STATIC", "CC_VERSION"):
            return True
    return False


def assign_fragment(key: str) -> Optional[str]:
    for name, pred in FRAGMENT_RULES:
        try:
            if pred(key):
                return name
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_strip_noise(args: argparse.Namespace) -> int:
    targets = list(ROOT.glob("*-omv-defconfig"))
    for path in targets:
        cfg = readconfig(path)
        before = len(cfg)
        for k in list(cfg):
            if is_noise(k):
                del cfg[k]
        writeconfig(path, cfg)
        print(f"{path.name}: {before} → {len(cfg)} (removed {before - len(cfg)} noise)")
    return 0


def cmd_strip_duplicates(args: argparse.Namespace) -> int:
    """Remove keys from arch/generic that exactly match a fragment (or generic for arch)."""
    frags = load_all_fragments()
    generic = readconfig(generic_path())

    # Arch bases: drop exact fragment matches and exact generic matches
    for arch in ALL_ARCHES:
        path = arch_defconfig(arch)
        if not path.is_file():
            continue
        cfg = readconfig(path)
        before = len(cfg)
        removed_frag = removed_gen = removed_noise = 0
        for k in list(cfg):
            if is_noise(k):
                del cfg[k]
                removed_noise += 1
                continue
            # Fragment always wins in merge order — arch value is dead even if different
            if k in frags:
                del cfg[k]
                removed_frag += 1
                continue
            if k in generic and generic[k] == cfg[k]:
                del cfg[k]
                removed_gen += 1
                continue
        writeconfig(path, cfg)
        print(f"{path.name}: {before} → {len(cfg)} "
              f"(frag={removed_frag} generic={removed_gen} noise={removed_noise})")

    # Generic: drop fragment-owned keys + noise (fragments override generic too)
    path = generic_path()
    cfg = readconfig(path)
    before = len(cfg)
    removed = 0
    for k in list(cfg):
        if is_noise(k):
            del cfg[k]
            removed += 1
            continue
        if k in frags:
            del cfg[k]
            removed += 1
    writeconfig(path, cfg)
    print(f"{path.name}: {before} → {len(cfg)} (removed {removed})")
    print("Note: '# CONFIG_* is not set' lines in fragments were left untouched.")
    return 0


def cmd_extract_common(args: argparse.Namespace) -> int:
    """Extract same-valued fat-arch keys into fragments / generic; strip from fat bases."""
    fat_cfgs = {a: readconfig(arch_defconfig(a)) for a in FAT_ARCHES}
    for a, c in fat_cfgs.items():
        if not c:
            print(f"error: missing {a}-omv-defconfig", file=sys.stderr)
            return 1

    frags = load_all_fragments()
    generic = readconfig(generic_path())

    # Keys present in all fat arches with identical value
    common_keys = set(fat_cfgs[FAT_ARCHES[0]])
    for a in FAT_ARCHES[1:]:
        common_keys &= set(fat_cfgs[a])

    extract: Dict[str, str] = {}
    for k in common_keys:
        vals = {fat_cfgs[a][k] for a in FAT_ARCHES}
        if len(vals) != 1:
            continue
        v = vals.pop()
        if is_noise(k):
            continue
        # Already owned by fragment with same value → just strip later
        if k in frags and frags[k][0] == v:
            extract[k] = v  # mark for strip only; don't re-add
            continue
        # Fragment has different value → leave arch alone (rare; fragment wins at merge)
        if k in frags and frags[k][0] != v:
            continue
        # Already in generic with same value → strip only
        if k in generic and generic[k] == v:
            extract[k] = v
            continue
        if k in generic and generic[k] != v:
            continue
        extract[k] = v

    # Partition into new fragment content vs generic, skipping keys already in fragments
    by_dest: Dict[str, Dict[str, str]] = {}
    to_generic: Dict[str, str] = {}
    strip_only = 0
    for k, v in extract.items():
        if k in frags:
            strip_only += 1
            continue
        if k in generic and generic[k] == v:
            strip_only += 1
            continue
        dest = assign_fragment(k)
        if dest:
            by_dest.setdefault(dest, {})[k] = v
        else:
            to_generic[k] = v

    dry = args.dry_run
    print(f"Shared same-value fat keys considered: {len(extract)}")
    print(f"  already in fragment/generic (strip-only): {strip_only}")
    for dest in sorted(by_dest):
        print(f"  → {dest}: {len(by_dest[dest])}")
    print(f"  → generic-omv-defconfig: {len(to_generic)}")

    if dry:
        return 0

    # Write / extend fragments (preserve existing entries including 'is not set')
    for dest, new_entries in sorted(by_dest.items()):
        path = ROOT / dest
        existing = readconfig(path)
        # Do not overwrite existing keys (especially intentional 'n')
        added = 0
        for k, v in new_entries.items():
            if k not in existing:
                existing[k] = v
                added += 1
            # if exists with same value, fine; if different, keep existing
        writeconfig(path, existing)
        print(f"wrote {path.name}: now {len(existing)} keys (+{added} new)")

    # Extend generic
    if to_generic:
        for k, v in to_generic.items():
            if k not in generic:
                generic[k] = v
        writeconfig(generic_path(), generic)
        print(f"wrote generic-omv-defconfig: now {len(generic)} keys")

    # Strip extracted keys from ALL arches (and noise); for slim arches only strip
    # keys that match fragment/generic after extraction (safe dedupe).
    # Reload fragments after write
    frags = load_all_fragments()
    generic = readconfig(generic_path())
    extract_keys = set(extract)

    for arch in ALL_ARCHES:
        path = arch_defconfig(arch)
        if not path.is_file():
            continue
        cfg = readconfig(path)
        before = len(cfg)
        for k in list(cfg):
            if is_noise(k):
                del cfg[k]
                continue
            if k in extract_keys and arch in FAT_ARCHES:
                # Fat: always strip extracted shared keys (now in fragment/generic)
                del cfg[k]
                continue
            if k in frags:
                del cfg[k]
                continue
            if k in generic and generic[k] == cfg[k]:
                del cfg[k]
                continue
        writeconfig(path, cfg)
        print(f"stripped {path.name}: {before} → {len(cfg)}")

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    frags = load_all_fragments()
    generic = readconfig(generic_path())
    print(f"fragments: {len(fragment_paths())} files, {len(frags)} unique keys")
    print(f"generic: {len(generic)} keys")
    fat = {a: readconfig(arch_defconfig(a)) for a in FAT_ARCHES}
    common = set(fat[FAT_ARCHES[0]])
    for a in FAT_ARCHES[1:]:
        common &= set(fat[a])
    same = sum(1 for k in common if len({fat[a][k] for a in FAT_ARCHES}) == 1)
    print(f"fat-arch same-value keys still in all four bases: {same}")
    for a in ALL_ARCHES:
        p = arch_defconfig(a)
        if p.is_file():
            cfg = readconfig(p)
            dup = sum(1 for k, v in cfg.items() if k in frags and frags[k][0] == v)
            print(f"  {a}: {len(cfg)} keys, {dup} exact fragment dups")
    return 0


def find_kernel_src(explicit: Optional[str]) -> Path:
    if explicit:
        p = Path(explicit)
        if not (p / "Makefile").is_file():
            raise SystemExit(f"kernel src not found: {p}")
        return p
    if os.environ.get("KERNEL_SRC"):
        p = Path(os.environ["KERNEL_SRC"])
        if (p / "Makefile").is_file():
            return p
    candidates = sorted(ROOT.glob("BUILD/kernel-*-build/linux-*"), reverse=True)
    for c in candidates:
        if (c / "Makefile").is_file() and (c / "scripts/kconfig/merge_config.sh").is_file():
            return c
    raise SystemExit("No kernel source found; pass --kernel-src or set KERNEL_SRC")


def merge_for_arch(kernel_src: Path, arch: str, out_config: Path, *,
                   overrides: Sequence[Path] = ()) -> None:
    """Reproduce CreateConfig merge + olddefconfig for one packaging arch name."""
    karch = arch
    base = arch_defconfig(arch)
    if not base.is_file():
        raise SystemExit(f"missing {base}")

    fragments = fragment_paths()
    generic = generic_path()
    # Match kernel.spec: arch.overrides / cfgarch.overrides / temporary-workarounds
    auto_over = []
    for name in (f"{arch}.overrides", "temporary-workarounds.overrides"):
        p = ROOT / name
        if p.is_file():
            auto_over.append(p)
    merge_inputs = (
        [str(base), str(generic)]
        + [str(p) for p in fragments]
        + [str(p) for p in auto_over]
        + [str(p) for p in overrides]
    )

    work = (out_config.parent / f"work-{arch}").resolve()
    out_config = out_config.resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    env = os.environ.copy()
    env.pop("KBUILD_OUTPUT", None)

    # Absolute paths: merge_config.sh runs with cwd=kernel_src
    merge_inputs = [str(Path(p).resolve()) for p in merge_inputs]
    merge_sh = kernel_src / "scripts/kconfig/merge_config.sh"
    cmd = ["bash", str(merge_sh), "-m", "-O", str(work)] + merge_inputs
    r = subprocess.run(cmd, cwd=str(kernel_src), env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:] if r.stdout else "", file=sys.stderr)
        print(r.stderr[-2000:] if r.stderr else "", file=sys.stderr)
        raise subprocess.CalledProcessError(r.returncode, cmd)

    # olddefconfig into the same output dir
    r = subprocess.run(
        ["make", f"ARCH={karch}", f"O={work}", "olddefconfig"],
        cwd=str(kernel_src), env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(r.stdout[-3000:] if r.stdout else "", file=sys.stderr)
        print(r.stderr[-3000:] if r.stderr else "", file=sys.stderr)
        raise subprocess.CalledProcessError(r.returncode, r.args)

    src_cfg = work / ".config"
    if not src_cfg.is_file():
        raise SystemExit(f"no .config produced for {arch} in {work}")
    shutil.copy(src_cfg, out_config)
    nlines = sum(1 for _ in out_config.open())
    print(f"  wrote {out_config} ({nlines} lines)")


def cmd_verify(args: argparse.Namespace) -> int:
    kernel_src = find_kernel_src(args.kernel_src)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    arches = args.arches.split(",") if args.arches else list(ALL_ARCHES)
    print(f"kernel: {kernel_src}")
    print(f"outdir: {outdir}")
    # Ensure source tree is clean enough for O= builds
    subprocess.run(["make", "mrproper"], cwd=str(kernel_src), check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for d in kernel_src.glob("arch/*/include/generated"):
        shutil.rmtree(d, ignore_errors=True)
    for arch in arches:
        print(f"=== {arch} ===")
        try:
            merge_for_arch(kernel_src, arch, outdir / f"{arch}.config")
        except subprocess.CalledProcessError as e:
            print(f"FAILED {arch}: {e}", file=sys.stderr)
            return 1
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two configs; fat-style strict or slim-style (baseline ⊆ new)."""
    a = readconfig(Path(args.config_a))
    b = readconfig(Path(args.config_b))
    only_a = []
    only_b = []
    changed = []
    for k in sorted(set(a) | set(b)):
        if k in a and k not in b:
            only_a.append(k)
        elif k in b and k not in a:
            only_b.append(k)
        elif a[k] != b[k]:
            changed.append(k)

    mode = args.mode
    print(f"only in A: {len(only_a)}, only in B: {len(only_b)}, changed: {len(changed)}")
    if args.verbose:
        for k in only_a[:50]:
            print(f"  -{k}={a[k]}")
        for k in only_b[:50]:
            print(f"  +{k}={b[k]}")
        for k in changed[:50]:
            print(f"  {k}: {a[k]} → {b[k]}")

    if mode == "strict":
        # fat arches: no differences allowed except pure noise keys
        real_a = [k for k in only_a if not is_noise(k)]
        real_b = [k for k in only_b if not is_noise(k)]
        real_c = [k for k in changed if not is_noise(k)]
        if real_a or real_b or real_c:
            print(f"STRICT FAIL: -{len(real_a)} +{len(real_b)} ~{len(real_c)}")
            for k in real_a[:20]:
                print(f"  -{k}={a[k]}")
            for k in real_b[:20]:
                print(f"  +{k}={b[k]}")
            for k in real_c[:20]:
                print(f"  {k}: {a[k]} → {b[k]}")
            return 1
        print("STRICT OK")
        return 0
    if mode == "subset":
        # slim: every non-noise key in A must remain same in B
        bad = []
        for k, v in a.items():
            if is_noise(k):
                continue
            if k not in b:
                bad.append((k, v, None))
            elif b[k] != v:
                bad.append((k, v, b[k]))
        if bad:
            print(f"SUBSET FAIL: {len(bad)} baseline keys lost/changed")
            for k, ov, nv in bad[:30]:
                print(f"  {k}: {ov} → {nv}")
            return 1
        print(f"SUBSET OK (B may have {len(only_b)} additions)")
        return 0
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("stats", help="Show duplication statistics")
    p.set_defaults(func=cmd_stats)

    p = sp.add_parser("strip-noise", help="Remove toolchain noise from defconfigs")
    p.set_defaults(func=cmd_strip_noise)

    p = sp.add_parser("strip-duplicates", help="Remove fragment/generic dups from arch bases")
    p.set_defaults(func=cmd_strip_duplicates)

    p = sp.add_parser("extract-common", help="Extract fat-arch shared keys into fragments/generic")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_extract_common)

    p = sp.add_parser("verify", help="Merge configs like the package build and save final .config")
    p.add_argument("--kernel-src", default=None)
    p.add_argument("--outdir", default=str(ROOT / "config-verify"))
    p.add_argument("--arches", default=",".join(ALL_ARCHES))
    p.set_defaults(func=cmd_verify)

    p = sp.add_parser("compare", help="Compare two config files")
    p.add_argument("config_a")
    p.add_argument("config_b")
    p.add_argument("--mode", choices=("strict", "subset", "report"), default="report")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
