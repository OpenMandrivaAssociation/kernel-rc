# utils/cpuidle-info.c:193: error: undefined reference to 'cpufreq_cpu_exists'
# investigate aarch64
%define _binaries_in_noarch_packages_terminate_build 0
#end
%define _disable_ld_no_undefined 1

%ifarch %{aarch64}
# FIXME this is a workaround for some debug files being created
# but not making it to the debug file lists.
# This should be fixed properly...
%define _unpackaged_files_terminate_build 0
%endif

## STOP: Adding weird and unsupported upstream kernel C/LD flags of any sort
## yes , including ftlo . O3 and whatever else

# (crazy) , well that new way of doing buil-id symlinks
# does not seems to work, see:
# https://issues.openmandriva.org/show_bug.cgi?id=2400
# let us try *old* way for kernel package(s)
%global _build_id_links alldebug

# Work around incomplete debug packages
%global _empty_manifest_terminate_build 0

%global cross_header_archs aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv32-linuxmusl riscv64-linuxmusl aarch64-android armv7l-android armv8l-android x86_64-android aarch64-linuxuclibc armv7hnl-linuxuclibc i686-linuxuclibc x86_64-linuxuclibc x32-linuxuclibc riscv32-linuxuclibc riscv64-linuxuclibc ppc64le-linux ppc64-linux ppc64le-linuxmusl ppc64-linuxmusl ppc64le-linuxuclibc ppc64-linuxuclibc
%global long_cross_header_archs %(
    for i in %{cross_header_archs}; do
	CPU=$(echo $i |cut -d- -f1)
	OS=$(echo $i |cut -d- -f2)
	echo -n "$(rpm --target=${CPU}-${OS} -E %%{_target_platform}) "
    done
)

# Parallelize xargs invocations on smp machines
%define kxargs xargs %([ -z "$RPM_BUILD_NCPUS" ] \\\
    && RPM_BUILD_NCPUS="$(/usr/bin/getconf _NPROCESSORS_ONLN)"; \\\
    [ "$RPM_BUILD_NCPUS" -gt 1 ] && echo "-P $RPM_BUILD_NCPUS")

%define target_arch %(echo %{_arch} | sed -e 's/mips.*/mips/' -e 's/arm.*/arm/' -e 's/aarch64/arm64/' -e 's/x86_64/x86/' -e 's/i.86/x86/' -e 's/znver1/x86/' -e 's/riscv.*/riscv/' -e 's/ppc.*/powerpc/')


# (tpg) define here per arch which kernel flavours you would like to build
%ifarch %{aarch64}
%define kernel_flavours desktop server
%else
%define kernel_flavours desktop server
# desktop-gcc server-gcc
%endif

# (tpg) package these kernel modules as subpackages
%ifarch %{aarch64}
%define modules_subpackages appletalk decnet fddi can
%else
%define modules_subpackages appletalk arcnet infiniband isdn can
%endif

# IMPORTANT
# This is the place where you set kernel version i.e 4.5.0
# compose tar.xz name and release
%define kernelversion 6
%define patchlevel 2
%define sublevel 0
%define relc 6

# Having different top level names for packges means that you have to remove
# them by hard :(
%define top_dir_name %{name}-%{_arch}
%define build_dir ${RPM_BUILD_DIR}/%{top_dir_name}

# Common target directories
%define _kerneldir %{_prefix}/src/linux-%{version}-%{release}%{disttag}
%define _bootdir /boot
# Should really be %{_prefix}/lib/modules, but there's a few hardcodes
# inside kernel Makefiles and it doesn't really matter given /lib is
# a symlink to %{_prefix}/lib anyway
%define _modulesdir /lib/modules

# Directories definition needed for building
%define temp_root %{build_dir}/temp-root
%define temp_source %{temp_root}%{_kerneldir}
%define temp_boot %{temp_root}%{_bootdir}
%define temp_modules %{temp_root}%{_modulesdir}

# Build defines
%bcond_with build_doc
%bcond_with uksm

%bcond_without build_source
%bcond_without build_devel
%bcond_without cross_headers

%bcond_with lazy_developer
%bcond_without build_debug
%bcond_without clr
%bcond_with vbox_orig_mods
# FIXME re-enable by default when the patches have been adapted to 5.8
%bcond_with saa716x
%bcond_with rtl8821ce
# build perf and cpupower tools
%bcond_without perf
%bcond_without bpftool
%bcond_without build_x86_energy_perf_policy
%bcond_without build_turbostat
%ifarch %{ix86} %{x86_64} %{aarch64}
%bcond_without hyperv
%endif
%ifarch %{ix86} %{x86_64}
%bcond_without build_cpupower
%else
# cpupower is currently x86 only
%bcond_with build_cpupower
%endif

# End of user definitions

# For the .nosrc.rpm
%bcond_with build_nosrc

#
# SRC RPM description
#
Summary:	Linux kernel built for %{distribution}
Name:		kernel%{?relc:-rc}
Version:	%{kernelversion}.%{patchlevel}%{?sublevel:.%{sublevel}}
Release:	%{?relc:0.rc%{relc}.}1
License:	GPLv2
Group:		System/Kernel and hardware
ExclusiveArch:	%{ix86} %{x86_64} %{armx} %{riscv}
ExclusiveOS:	Linux
URL:		http://www.kernel.org

####################################################################
#
# Sources
#
### This is for full SRC RPM
%if 0%{?relc:1}
Source0:	https://git.kernel.org/torvalds/t/linux-%{kernelversion}.%{patchlevel}-rc%{relc}.tar.gz
%else
Source0:	http://www.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{kernelversion}.%{patchlevel}.tar.xz
Source1:	http://www.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{kernelversion}.%{patchlevel}.tar.sign
%endif
### This is for stripped SRC RPM
%if %{with build_nosrc}
NoSource:	0
%endif
Source3:	README.kernel-sources
Source4:	%{name}.rpmlintrc
## all in one configs for each kernel
Source10:	x86_64-omv-defconfig
Source11:	i686-omv-defconfig
Source12:	armv7hnl-omv-defconfig
Source13:	aarch64-omv-defconfig
# config and systemd service file from fedora
Source30:	cpupower.service
Source31:	cpupower.config

# Patches
# Numbers 0 to 9 are reserved for upstream patches
# (-stable patch, -rc, ...)
# Added as a Source rather that Patch because it needs to be
# applied with "git apply" -- may contain binary patches.

# Patches to VirtualBox and other external modules are
# pulled in as Source: rather than Patch: because it's arch specific
# and can't be applied by %%autopatch -p1

%if 0%{?sublevel:%{sublevel}}
# The big upstream patch is added as source rather than patch
# because "git apply" is needed to handle binary patches it
# frequently contains (firmware updates etc.)
Source1000:	https://cdn.kernel.org/pub/linux/kernel/v%(echo %{version}|cut -d. -f1).x/patch-%{version}.xz
%endif

# FIXME git bisect shows upstream commit
# 7a8b64d17e35810dc3176fe61208b45c15d25402 breaks
# booting SynQuacer from USB flash drives.
# 9d55bebd9816903b821a403a69a94190442ac043 builds on
# 7a8b64d17e35810dc3176fe61208b45c15d25402.
Source1001:	revert-7a8b64d17e35810dc3176fe61208b45c15d25402.patch
Source1002:	revert-9d55bebd9816903b821a403a69a94190442ac043.patch

Patch31:	die-floppy-die.patch
Patch32:	0001-Add-support-for-Acer-Predator-macro-keys.patch
Patch34:	kernel-5.6-kvm-gcc10.patch
# Work around rpm dependency generator screaming about
# error: Illegal char ']' (0x5d) in: 1.2.1[50983]_custom
# caused by aacraid versioning ("1.2.1[50983]-custom")
Patch36:	aacraid-dont-freak-out-dependency-generator.patch
# Make uClibc-ng happy
Patch37:	socket.h-include-bitsperlong.h.patch
# Make Nouveau work on SynQuacer (and probably all other non-x86 boards)
# FIXME this may need porting, not sure where WC is set in 5.10
#Patch38:	kernel-5.8-nouveau-write-combining-only-on-x86.patch
Patch40:	kernel-5.8-aarch64-gcc-10.2-workaround.patch
# (tpg) https://github.com/ClangBuiltLinux/linux/issues/1341
Patch42:	linux-5.11-disable-ICF-for-CONFIG_UNWINDER_ORC.patch

# (tpg)
# The Ultra Kernel Same Page Deduplication
# http://kerneldedup.org/en/projects/uksm/download/
# sources can be found here https://github.com/dolohow/uksm
# Usually faster ports to new kernel releases can be found at
# https://github.com/sirlucjan/kernel-patches/tree/master/5.16/uksm-patches
%if %{with uksm}
Patch43:	https://raw.githubusercontent.com/sirlucjan/kernel-patches/master/5.18/uksm-patches/0001-UKSM-for-5.18.patch
%endif

# (crazy) see: https://forum.openmandriva.org/t/nvme-ssd-m2-not-seen-by-omlx-4-0/2407
Patch45:	Unknow-SSD-HFM128GDHTNG-8310B-QUIRK_NO_APST.patch
# Restore ACPI loglevels to sane values
Patch46:	https://gitweb.frugalware.org/wip_kernel/raw/86234abea5e625043153f6b8295642fd9f42bff0/source/base/kernel/acpi-use-kern_warning_even_when_error.patch
Patch47:	https://gitweb.frugalware.org/wip_kernel/raw/23f5e50042768b823e18613151cc81b4c0cf6e22/source/base/kernel/fix-acpi_dbg_level.patch
Patch48:	linux-5.4.5-fix-build.patch
Patch51:	linux-5.5-corsair-strafe-quirks.patch
Patch52:	http://crazy.dev.frugalware.org/smpboot-no-stack-protector-for-gcc10.patch
Patch55:	linux-5.16-clang-no-attribute-symver.patch

### Additional hardware support
### TV tuners:
# SAA716x DVB driver
# git clone git@github.com:crazycat69/linux_media
# cd linux_media
# tar cJf saa716x-driver.tar.xz drivers/media/pci/saa716x drivers/media/dvb-frontends/tas2101* drivers/media/dvb-frontends/isl6422* drivers/media/dvb-frontends/stv091x.h drivers/media/tuners/av201x* drivers/media/tuners/stv6120*
# Patches 141 to 145 are a minimal set of patches to the DVB stack to make
# the added driver work.
Source1003:	saa716x-driver.tar.xz
Patch200:	0023-tda18212-Added-2-extra-options.-Based-on-CrazyCat-re.patch
Patch201:	0075-cx24117-Use-a-pointer-to-config-instead-of-storing-i.patch
Patch202:	0076-cx24117-Add-LNB-power-down-callback.-TBS6984-uses-pc.patch
Patch204:	saa716x-driver-integration.patch
Patch205:	saa716x-4.15.patch
Patch206:	saa716x-linux-4.19.patch
Patch207:	saa716x-5.4.patch

# Additional WiFi drivers taken from the Endless kernel
# git clone https://github.com/endlessm/linux.git
# cd linux
# tar cf extra-wifi-drivers-`date +%Y%m%d`.tar drivers/net/wireless/rtl8*
# zstd -19 extra-wifi-drivers*.tar
Source1004:	extra-wifi-drivers-20200301.tar.zst
Patch208:	extra-wifi-drivers-compile.patch
Patch209:	extra-wifi-drivers-port-to-5.6.patch

# VirtualBox patches -- added as Source: rather than Patch:
# because they need to be applied after stuff from the
# virtualbox-kernel-module-sources package is copied around
Source1005:	vbox-6.1-fix-build-on-znver1-hosts.patch
Source1007:	vboxnet-clang.patch

# Assorted fixes

# Bring back ashmem -- anbox and waydroid still need it
Patch211:	revert-721412ed3d819e767cac2b06646bf03aa158aaec.patch
# Modular binder and ashmem -- let's try to make anbox happy
Patch212:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/android-enable-building-ashmem-and-binder-as-modules.patch
Patch213:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/export-symbols-needed-by-android-drivers.patch

Patch215:	linux-5.19-prefer-amdgpu-over-radeon.patch
Patch217:	acpi-chipset-workarounds-shouldnt-be-necessary-on-non-x86.patch

# Fix CPU frequency governor mess caused by recent Intel patches
Patch225:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/0001-Revert-cpufreq-Avoid-configuring-old-governors-as-de.patch
Patch226:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/revert-parts-of-a00ec3874e7d326ab2dffbed92faddf6a77a84e9-no-Intel-NO.patch

# Fix perf
Patch230:	linux-5.11-perf-compile.patch
#Patch231:	ce71038e673ee8291c64631359e56c48c8616dc7.patch

# (tpg) Armbian ARM Patches
Patch240:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-fix-emmc.patch
Patch241:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-fix-spi1-flash-speed.patch
Patch242:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-work-led-heartbeat.patch
Patch243:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-fix-mmc-signal-voltage-before-reboot.patch
Patch245:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-unlock-temperature.patch
Patch246:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-increasing_DMA_block_memory_allocation_to_2048.patch
Patch247:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-rk808-configurable-switch-voltage-steps.patch
Patch248:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-sd-drive-level-8ma.patch
Patch249:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-pci-rockchip-support-ep-gpio-undefined-case.patch
Patch250:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpi4-FixMMCFreq.patch

# (tpg) Manjaro ARM Patches
%if 0
Patch260:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0001-arm64-dts-rockchip-Add-back-cdn_dp-to-Pinebook-Pro.patch
Patch261:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-arm64-dts-allwinner-add-hdmi-sound-to-pine-devices.patch
Patch262:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-arm64-dts-allwinner-add-ohci-ehci-to-h5-nanopi.patch
Patch263:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-drm-bridge-analogix_dp-Add-enable_psr-param.patch
Patch264:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0005-gpu-drm-add-new-display-resolution-2560x1440.patch
Patch265:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0006-nuumio-panfrost-Silence-Panfrost-gem-shrinker-loggin.patch
Patch266:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0007-arm64-dts-rockchip-Add-Firefly-Station-p1-support.patch
Patch267:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0008-typec-displayport-some-devices-have-pin-assignments-reversed.patch
Patch268:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0009-Add-megis-extcon-changes-to-fusb302.patch
Patch269:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0010-usb-typec-Add-megis-typex-to-extcon-bridge-driver.patch
Patch270:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0011-arm64-rockchip-add-DP-ALT-rockpro64.patch
Patch271:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0012-ayufan-drm-rockchip-add-support-for-modeline-32MHz-e.patch
Patch272:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0013-rk3399-rp64-pcie-Reimplement-rockchip-PCIe-bus-scan-delay.patch
Patch273:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0014-arm64-dts-rockchip-add-typec-extcon-hack.patch
Patch274:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0015-drm-meson-add-YUV422-output-support.patch
Patch275:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0016-arm64-dts-meson-add-initial-Beelink-GT1-Ultimate-dev.patch
Patch276:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0017-add-ugoos-device.patch
Patch277:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0018-drm-panfrost-scheduler-fix.patch
Patch278:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0019-arm64-dts-rockchip-Add-pcie-bus-scan-delay-to-rockpr.patch
Patch279:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0020-drm-rockchip-support-gamma-control-on-RK3399.patch
Patch280:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0021-media-rockchip-rga-do-proper-error-checking-in-probe.patch
Patch281:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0022-arm-dts-rockchip-firefly-station-m2.patch
Patch282:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0023-add-dts-rk3568-station-p2.patch
Patch283:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0024-add-dts-rk3568-radxa-rock3a.patch
Patch284:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0001-Bluetooth-Add-new-quirk-for-broken-local-ext-features.patch
Patch285:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-Bluetooth-btrtl-add-support-for-the-RTL8723CS.patch
Patch286:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-arm64-allwinner-a64-enable-Bluetooth-On-Pinebook.patch
Patch287:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-arm64-dts-allwinner-enable-bluetooth-pinetab-pinepho.patch
Patch288:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0005-staging-add-rtl8723cs-driver.patch
Patch289:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0006-pinetab-accelerometer.patch
Patch290:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0007-enable-jack-detection-pinetab.patch
Patch292:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-arm64-dts-rockchip-enable-vop2-and-hdmi-tx-on-quartz64a.patch
Patch293:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-add-GPU-for-RK356x-SoCs.patch
Patch294:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-power-supply-Add-Support-for-RK817-Charger.patch
Patch295:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0005-phy-rockchip-inno-usb2-support-rk356x-usb2phy.patch
Patch296:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0006-HDMI-Audio-on-RK356x-Quartz64-Model-A.patch
Patch297:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0007-phy-rockchip-add-naneng-combo-phy-for-RK3568.patch
Patch298:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0008-arm64-dts-rockchip-enable-sdmmc1-on-Quartz64-Model-A.patch
%endif

# (tpg) patches taken from https://github.com/OpenMandrivaSoftware/os-image-builder/tree/master/device/rockchip/generic/kernel-patches
Patch300:	add-board-orangepi-4.patch
Patch303:	rk3399-add-sclk-i2sout-src-clock.patch
#Patch304:	rtl8723cs-compile.patch
Patch305:	kernel-6.0-rc2-perf-x86-compile.patch

Patch350:	rtla-5.17-fix-make-clean.patch

# V4L2 loopback
# https://github.com/umlaeute/v4l2loopback
Source400:     https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback.c
Source401:     https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback.h
Source402:     https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback_formats.h

# (tpg) patches taken from LibreELEC
#Patch400:	https://raw.githubusercontent.com/LibreELEC/LibreELEC.tv/master/projects/Rockchip/patches/linux/default/linux-2000-v4l-wip-rkvdec-vp9.patch
#Patch401:	https://raw.githubusercontent.com/LibreELEC/LibreELEC.tv/master/projects/Rockchip/patches/linux/default/linux-2001-v4l-wip-rkvdec-hevc.patch

# Patches to external modules
# Marked SourceXXX instead of PatchXXX because the modules
# being touched aren't in the tree at the time %%autopatch -p1
# runs...

%if %{with clr}
# (tpg) some patches from ClearLinux
# https://github.com/clearlinux-pkgs/linux/
Patch900:	0101-i8042-decrease-debug-message-level-to-info.patch
Patch901:	0102-increase-the-ext4-default-commit-age.patch
Patch902:	0103-silence-rapl.patch
Patch903:	0104-pci-pme-wakeups.patch
Patch904:	0105-ksm-wakeups.patch
#Patch905:	0106-intel_idle-tweak-cpuidle-cstates.patch
Patch907:	0108-smpboot-reuse-timer-calibration.patch
Patch908:	0109-initialize-ata-before-graphics.patch
Patch910:	0111-ipv4-tcp-allow-the-memory-tuning-for-tcp-to-go-a-lit.patch
Patch913:	0117-migrate-some-systemd-defaults-to-the-kernel-defaults.patch
Patch914:	0120-use-lfence-instead-of-rep-and-nop.patch
%endif

Autoreqprov:	no
BuildRequires:	zstd
BuildRequires:	findutils
BuildRequires:	bc
BuildRequires:	flex
BuildRequires:	bison
BuildRequires:	binutils
BuildRequires:	hostname
BuildRequires:	clang
BuildRequires:	llvm
BuildRequires:	lld
BuildRequires:	pkgconfig(libcap)
BuildRequires:	pkgconfig(libssl)
BuildRequires:	diffutils
# For git apply
BuildRequires:	git-core
# For power tools
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libkmod)
# For sign-file
BuildRequires:	pkgconfig(openssl)
BuildRequires:	openssl

%ifarch %{x86_64} %{aarch64}
BuildRequires:	pkgconfig(numa)
%endif

# for cpupower
%if %{with build_cpupower}
BuildRequires:	pkgconfig(libpci)
%endif

%if %{with build_turbostat}
BuildRequires:	pkgconfig(libpcap)
%endif

# for docs
%if %{with build_doc}
BuildRequires:	xmlto
%endif

# for ORC unwinder and perf
BuildRequires:	pkgconfig(libelf)

%if %{with bpftool}
# for bpf
BuildRequires:	pahole
%endif

# for perf
%if %{with perf}
# The Makefile prefers python2, python3, python in that
# order. Unless and until we fix that, make sure we use
# the right version by conflicting with the other.
BuildConflicts:	python2
BuildRequires:	asciidoc
BuildRequires:	xmlto
BuildRequires:	pkgconfig(audit)
BuildRequires:	binutils-devel
BuildRequires:	bison
BuildRequires:	flex
BuildRequires:	pkgconfig(libunwind)
BuildRequires:	pkgconfig(libnewt)
BuildRequires:	pkgconfig(gtk+-2.0)
BuildRequires:	pkgconfig(python3)
BuildRequires:	python%{py_ver}dist(setuptools)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(babeltrace2)
BuildRequires:	jdk-current
BuildRequires:	perl-devel
BuildRequires:	perl(ExtUtils::Embed)
%endif

%ifarch %{arm}
BuildRequires:	uboot-mkimage
%endif


# Let's pull in some of the most commonly used DKMS modules
# so end users don't have to install compilers (and worse,
# get compiler error messages on failures)
%ifarch %{x86_64}
BuildRequires:	virtualbox-kernel-module-sources >= 6.1.38
%if %{with vbox_orig_mods}
BuildRequires:	virtualbox-guest-kernel-module-sources >= 6.1.38
%endif
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of your
%{distribution} operating system. The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.

# (tpg) generate subpackages for kernel flavours
%(for flavour in %{kernel_flavours}; do
	cat <<EOF
%package -n %{name}-${flavour}
Summary:	The heart of the %{distribution} built for ${flavour}
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware
%if "${flavour}" == "desktop-gcc" || "${flavour}" == "server-gcc"
BuildRequires:	gcc
BuildRequires:	gcc-c++
%else
Provides:	kernel-release-${flavour}-clang
Provides:	kernel-release-${flavour}-clang-%{version}-%{release}%{disttag} = %{version}-%{release}
Provides:	kernel-release-${flavour}-clang%_isa = %{version}-%{release}
%endif
Requires(pre):	kmod >= 27-3
Recommends:	kernel-firmware
Provides:	kernel = %{kernelversion}.%{patchlevel}
Provides:	%{name} = %{version}-%{release}
Provides:	%{name}-${flavour}-%{version}-%{release}%{disttag}
Obsoletes:	dkms-r8192se <= 0019.1207.2010-2
Obsoletes:	dkms-lzma <= 4.43-32
Obsoletes:	dkms-psb <= 4.41.1-7
Conflicts:	dkms-broadcom-wl < 5.100.82.112-12
Conflicts:	dkms-fglrx < 13.200.5-1
Conflicts:	dkms-nvidia-current < 325.15-1
Conflicts:	dkms-nvidia-long-lived < 319.49-1
Conflicts:	dkms-nvidia304 < 304.108-1
Conflicts:	%{name}-${flavour}-latest <= %{version}-%{release}
Obsoletes:	%{name}-${flavour}-latest <= %{version}-%{release}
Provides:	kernel-release
Provides:	kernel-release-${flavour}
Provides:	installonlypkg(kernel)
Recommends:	iw
%ifarch %{ix86} %{x86_64}
Requires(post):	grub2 >= 2.02-27
%endif
%ifnarch %{armx}
Recommends:	cpupower
Recommends:	microcode-intel
Suggests:	dracut >= 047
%endif
%ifarch %{ix86}
Conflicts:	arch(x86_64)
Conflicts:	arch(znver1)
%endif
%ifnarch %{armx} %{riscv}
# might be useful too:
Suggests:	microcode-intel
%endif

%description -n %{name}-${flavour}
%summary .

%posttrans -n %{name}-${flavour} -f kernel_files.${flavour}-posttrans
%postun -n %{name}-${flavour} -f kernel_files.${flavour}-postun

%files -n %{name}-${flavour} -f kernel_files.${flavour}
EOF

%if %{with build_devel}
	cat <<EOF
%package -n %{name}-${flavour}-devel
Summary:	The kernel-devel files for %{name}-${flavour}-%{version}-%{release}%{disttag}
Version:	%{version}
Release:	%{release}
Group:		Development/Kernel
Requires:	glibc-devel
Requires:	ncurses-devel
Requires:	make
%ifarch %{x86_64}
Requires:	pkgconfig(libelf)
%endif
Provides:	kernel-devel = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Provides:	%{name}-${flavour}-devel-%{version}-%{release}%{disttag}
Conflicts:	%{name}-${flavour}-devel-latest <= %{version}-%{release}
Obsoletes:	%{name}-${flavour}-devel-latest <= %{version}-%{release}
Provides:	installonlypkg(kernel)
Requires:	%{name}-${flavour} = %{version}-%{release}
%rename kernel-release-${flavour}-devel
AutoReqProv:	no
%ifarch %{ix86}
Conflicts:	arch(x86_64)
Conflicts:	arch(znver1)
%endif

%description -n %{name}-${flavour}-devel
This package contains the kernel files (headers and build tools)
that should be enough to build additional drivers for
use with %{name}-${flavour}-%{version}-%{release}%{disttag}.
If you want to build your own kernel, you need to install the full
%{name}-source-%{version}-%{release}%{disttag}.

%post -n %{name}-${flavour}-devel -f kernel_devel_files.${flavour}-post
%preun -n %{name}-${flavour}-devel -f kernel_devel_files.${flavour}-preun
%postun -n %{name}-${flavour}-devel -f kernel_devel_files.${flavour}-postun

%files -n %{name}-${flavour}-devel -f kernel_devel_files.${flavour}
EOF
%endif # end build_devel

%if %{with build_debug}
	cat <<EOF
%package -n %{name}-${flavour}-debuginfo
Summary:	Files with debuginfo for %{name}-${flavour}-%{version}-%{release}%{disttag}
Version:	%{version}
Release:	%{release}
Group:		Development/Debug
Provides:	kernel-debug = %{version}-%{release}
Provides:	kernel-${flavour}-%{version}-%{release}%{disttag}-debuginfo
Provides:	installonlypkg(kernel)
Requires:	%{name}-${flavour} = %{version}-%{release}
%rename kernel-release-${flavour}-debuginfo
AutoReqProv:	no
%ifarch %{ix86}
Conflicts:	arch(x86_64)
Conflicts:	arch(znver1)
%endif

%description -n %{name}-${flavour}-debuginfo
This package contains the files with debuginfo to aid in debug tasks
when using %{name}-${flavour}-%{version}-%{release}%{disttag}.
If you need to look at debug information or use some application that
needs debugging info from the kernel, this package may help.

%files -n %{name}-${flavour}-debuginfo -f kernel_debug_files.${flavour}
EOF
%endif  # end build_debug
done
)

%(
for modules in %{modules_subpackages}; do
    for flavour in %{kernel_flavours}; do
	cat <<EOF
%package -n %{name}-${flavour}-modules-${modules}
Summary:	 ${modules} for kernel %{name}-${flavour}
Group:		System/Kernel and hardware
Requires:	%{name}-${flavour} = %{version}-%{release}
Provides:	installonlypkg(kernel-module)
AutoReq:	no
AutoProv:	yes

%description -n %{name}-${flavour}-modules-${modules}
%{modules} modules for kernel %{name}-${flavour} .

%files -n %{name}-${flavour}-modules-${modules}
%optional %{_modulesdir}/%{version}-${flavour}-%{release}%{disttag}/kernel/net/${modules}
%optional %{_modulesdir}/%{version}-${flavour}-%{release}%{disttag}/kernel/drivers/${modules}
%optional %{_modulesdir}/%{version}-${flavour}-%{release}%{disttag}/kernel/drivers/net/${modules}

EOF
    done
done
)

#
# kernel-source
#
%if %{with build_source}
%package -n %{name}-source
Summary:	The Linux source code for %{name}-%{version}-%{release}%{disttag}
Version:	%{version}
Release:	%{release}
Group:		Development/Kernel
Requires:	glibc-devel
Requires:	ncurses-devel
Requires:	make
Requires:	gcc >= 7.2.1_2017.11-3
Requires:	perl
Requires:	diffutils
Autoreqprov:	no
Provides:	kernel-source = %{version}-%{release}
Provides:	kernel-source-%{version}-%{release}%{disttag}
Provides:	installonlypkg(kernel)
Conflicts:	%{name}-source-latest <= %{version}-%{release}
Obsoletes:	%{name}-source-latest <= %{version}-%{release}
Conflicts:	kernel-release-source-latest <= %{version}-%{release}
Obsoletes:	kernel-release-source-latest <= %{version}-%{release}
%rename kernel-release-source
Buildarch:	noarch

%description -n %{name}-source
The %{name}-source package contains the source code files for the %{distribution}
kernel. These source files are only needed if you want to build your own
custom kernel that is better tuned to your particular hardware.

If you only want the files needed to build 3rdparty (nVidia, Ati, dkms-*,...)
drivers against, install the *-devel rpm that is matching your kernel.
%endif

#
# kernel-doc: documentation for the Linux kernel
#
%if %with build_doc
%package -n %{name}-doc
Summary:	Various documentation bits for %{distribution} %{name}
Version:	%{version}
Release:	%{release}
Group:		Documentation
Buildarch:	noarch

%description -n %{name}-doc
This package contains documentation files from the %{name} source.
Various bits of information about the Linux kernel and the device drivers
shipped with it are documented in these files. You also might want install
this package if you need a reference to the options that can be passed to
Linux kernel modules at load time.
%endif

#
# kernel/tools
#
%if %{with perf}
%package -n perf
Summary:	perf tool and the supporting documentation
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware

%description -n perf
The perf tool and the supporting documentation.
%endif

%if %{with build_cpupower}
%package -n cpupower
Summary:	The cpupower tools
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware
Obsoletes:	cpufreq < 2.0-3
Provides:	cpufreq = 2.0-3
Obsoletes:	cpufrequtils < 008-6
Provides:	cpufrequtils = 008-6

%description -n cpupower
The cpupower tools.

%package -n cpupower-devel
Summary:	Devel files for cpupower
Version:	%{version}
Release:	%{release}
Group:		Development/Kernel
Requires:	cpupower = %{version}-%{release}
Conflicts:	%{_lib}cpufreq-devel

%description -n cpupower-devel
This package contains the development files for cpupower.
%endif

%if %{with build_x86_energy_perf_policy}
%package -n x86_energy_perf_policy
Summary:	Tool to control energy vs. performance on recent X86 processors
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware

%description -n x86_energy_perf_policy
Tool to control energy vs. performance on recent X86 processors.
%endif

%if %{with build_turbostat}
%package -n turbostat
Summary:	Tool to report processor frequency and idle statistics
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware

%description -n turbostat
Tool to report processor frequency and idle statistics.
%endif

%if %{with hyperv}
%package -n hyperv-tools
Summary:	Tools needed to communicate with a Hyper-V host
Source7000:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervkvpd.service
Source7001:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervkvp.rules
Source7002:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervvssd.service
Source7003:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervvss.rules
Source7004:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervfcopyd.service
Source7005:	https://src.fedoraproject.org/rpms/hyperv-daemons/raw/rawhide/f/hypervfcopy.rules

%description -n hyperv-tools
Tools needed to communicate with a Hyper-V host

%files -n hyperv-tools
%{_sbindir}/hv_kvp_daemon
%{_unitdir}/hypervkvpd.service
%{_udevrulesdir}/70-hypervkvp.rules
%{_sbindir}/hv_vss_daemon
%{_unitdir}/hypervvssd.service
%{_udevrulesdir}/70-hypervvss.rules
%{_sbindir}/hv_fcopy_daemon
%{_unitdir}/hypervfcopyd.service
%{_udevrulesdir}/70-hypervfcopy.rules
%{_sbindir}/lsvmbus
%{_libexecdir}/hypervkvpd
%endif

%if %{with bpftool}
%define bpf_major 1
%define libbpf %mklibname bpf %{bpf_major}
%define libbpfdevel %mklibname bpf -d

%package -n bpftool
Summary:	Inspection and simple manipulation of eBPF programs and maps
Group:		System/Kernel and hardware

%description -n bpftool
This package contains the bpftool, which allows inspection and simple
manipulation of eBPF programs and maps.

%package -n %{libbpf}
Summary:	The bpf library from kernel source
Group:		System/Libraries

%description -n %{libbpf}
This package contains the kernel source bpf library.

%package -n %{libbpfdevel}
Summary:	Developement files for the bpf library from kernel source
Group:		Development/Kernel
Requires:	%{libbpf} = %{EVRD}

%description -n %{libbpfdevel}
This package includes libraries and header files needed for development
of applications which use bpf library from kernel sour
%endif

%package headers
Summary:	Linux kernel header files mostly used by your C library
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware
Epoch:		1
%if 0%{?relc:1}
# (tpg) fix bug https://issues.openmandriva.org/show_bug.cgi?id=1580
Provides:	kernel-headers = 1:%{version}-%{release}
Obsoletes:	kernel-headers < 1:%{version}-%{release}
%endif

%description headers
C header files from the Linux kernel. The header files define
structures and constants that are needed for building most
standard programs, notably the C library.

This package is not suitable for building kernel modules, you
should use the 'kernel-devel' package instead.

%files headers
%{_includedir}/*
# Don't conflict with cpupower-devel
%if %{with build_cpupower}
%exclude %{_includedir}/cpufreq.h
%endif

%if %{with cross_headers}
%(
for i in %{long_cross_header_archs}; do
	[ "$i" = "%{_target_platform}" ] && continue
	cat <<EOF
%package -n cross-${i}-%{name}-headers
Version:	%{version}
Release:	%{release}
Summary:	Linux kernel header files for ${i} cross toolchains
Group:		System/Kernel and hardware
BuildArch:	noarch
%if "%{name}" != "kernel"
Provides:	cross-${i}-kernel-headers = %{EVRD}
%endif
%rename cross-${i}-kernel-release-headers

%description -n cross-${i}-%{name}-headers
C header files from the Linux kernel. The header files define
structures and constants that are needed for building most
standard programs, notably the C library.

This package is only of interest if you're cross-compiling for
${i} targets.

%files -n cross-${i}-%{name}-headers
%{_prefix}/${i}/include/*
EOF
done
)
%endif

#
# End packages - here begins build stage
#
%prep

%setup -q -n linux-%{kernelversion}.%{patchlevel}%{?relc:-rc%{relc}} -a 1003 -a 1004
%if 0%{?sublevel:%{sublevel}}
[ -e .git ] || git init
xzcat %{SOURCE1000} |git apply - || git apply %{SOURCE1000}
rm -rf .git
%endif
%autopatch -p1

%if %{with saa716x}
# merge SAA716x DVB driver from extra tarball
sed -i -e '/saa7164/isource "drivers/media/pci/saa716x/Kconfig"' drivers/media/pci/Kconfig
sed -i -e '/saa7164/iobj-$(CONFIG_SAA716X_CORE) += saa716x/' drivers/media/pci/Makefile
find drivers/media/tuners drivers/media/dvb-frontends -name "*.c" -o -name "*.h" -type f | xargs sed -i -e 's,"dvb_frontend.h",<media/dvb_frontend.h>,g'
%endif

%if %{with rtl8821ce}
# Merge RTL8723DE and RTL8821CE drivers
cd drivers/net/wireless
sed -i -e '/quantenna\/Kconfig/asource "drivers/net/wireless/rtl8821ce/Kconfig' Kconfig
sed -i -e '/quantenna\/Kconfig/asource "drivers/net/wireless/rtl8723de/Kconfig' Kconfig
sed -i -e '/QUANTENNA/aobj-$(CONFIG_RTL8821CE) += rtl8821ce/' Makefile
sed -i -e '/QUANTENNA/aobj-$(CONFIG_RTL8723DE) += rtl8723de/' Makefile
cd -
%endif

%if 0%{?sublevel:1}
# make sure the kernel has the sublevel we know it has...
LC_ALL=C sed -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{sublevel}/" Makefile
%endif

# Pull in some externally maintained modules
%ifarch %{x86_64}
# === VirtualBox guest additions ===
%if %{with vbox_orig_mods}
# There is an in-kernel version of vboxvideo -- unfortunately
# it doesn't seem to work properly with vbox just yet
# Let's replace it with the one that comes with VB for now
rm -rf drivers/gpu/drm/vboxvideo
cp -a $(ls --sort=time -1d /usr/src/vboxadditions-*|head -n1)/vboxvideo drivers/gpu/drm/
cat >drivers/gpu/drm/vboxvideo/Kconfig <<'EOF'
config DRM_VBOXVIDEO
	tristate "Virtual Box Graphics Card"
	depends on DRM && X86 && PCI
	select DRM_KMS_HELPER
	select DRM_TTM
	select GENERIC_ALLOCATOR
	help
	  This is a KMS driver for the virtual Graphics Card used in
	  Virtual Box virtual machines.
	  Although it is possible to build this driver built-in to the
	  kernel, it is advised to build it as a module, so that it can
	  be updated independently of the kernel. Select M to build this
	  driver as a module and add support for these devices via drm/kms
	  interfaces.
EOF
sed -i -e 's,\$(KBUILD_EXTMOD),drivers/gpu/drm/vboxvideo,g' drivers/gpu/drm/vboxvideo/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/gpu/drm/vboxvideo/Makefile*
%endif

# 800x600 is too small to be useful -- even calamares doesn't
# fit into that anymore (this fix is needed for both the in-kernel
# version and the vbox version of the driver)
sed -i -e 's|800, 600|1024, 768|g' drivers/gpu/drm/vboxvideo/vbox_mode.c
# VirtualBox shared folders now come in through patch 300

## NONE upstream this stuff will be here for a while
# === VirtualBox host modules ===
# VirtualBox
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxdrv drivers/virt/
sed -i -e 's,\$(VBOXDRV_DIR),drivers/virt/vboxdrv/,g' drivers/virt/vboxdrv/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/virt/vboxdrv/Makefile*
echo 'obj-m += vboxdrv/' >>drivers/virt/Makefile
# VirtualBox network adapter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetadp drivers/net/
sed -i -e 's,\$(VBOXNETADP_DIR),drivers/net/vboxnetadp/,g' drivers/net/vboxnetadp/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetadp/Makefile*
echo 'obj-m += vboxnetadp/' >>drivers/net/Makefile
# VirtualBox network filter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetflt drivers/net/
sed -i -e 's,\$(VBOXNETFLT_DIR),drivers/net/vboxnetflt/,g' drivers/net/vboxnetflt/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetflt/Makefile*
echo 'obj-m += vboxnetflt/' >>drivers/net/Makefile
%if 0
# VirtualBox PCI
# https://forums.gentoo.org/viewtopic-t-1105508-start-0.html -- not very
# useful (yet), but a source of many errors.
# Potentially re-enable if it ever gets fixed to support PCIE.
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxpci drivers/pci/
sed -i -e 's,\$(VBOXPCI_DIR),drivers/pci/vboxpci/,g' drivers/pci/vboxpci/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/pci/vboxpci/Makefile*
echo 'obj-m += vboxpci/' >>drivers/pci/Makefile
%endif
patch -p1 -z .1005~ -b <%{S:1005}
patch -p1 -z .1007~ -b <%{S:1007}
%endif

# V4L2 loopback support
cp %{S:401} %{S:402} include/media
sed -e 's,"v4l2loopback.h",<media/v4l2loopback.h>,g;s,"v4l2loopback_formats.h",<media/v4l2loopback_formats.h>,g' %{S:400} >drivers/media/v4l2-core/v4l2loopback.c
cat >>drivers/media/v4l2-core/Kconfig <<'EOF'

config V4L2_LOOPBACK
	tristate "Video4Linux loopback support"
	help
	  This module allows you to create "virtual video devices". Normal (v4l2)
	  applications will read these devices as if they were ordinary video devices,
	  but the video will not be read from e.g. a capture card but instead it is
	  generated by another application.
EOF
cat >>drivers/media/v4l2-core/Makefile <<'EOF'

obj-$(CONFIG_V4L2_LOOPBACK) += v4l2loopback.o
EOF

# get rid of unwanted files
find . -name '*~' -o -name '*.orig' -o -name '*.append' -o -name '*.g*ignore' | %kxargs rm -f

# fix missing exec flag on file introduced in 4.14.10-rc1
chmod 755 tools/objtool/sync-check.sh

%build
%set_build_flags

###
### Functions definitions needed to build kernel
###

CheckConfig() {

    if [ ! -e $(pwd)/.config ]; then
	printf '%s\n' "Kernel config in $(pwd) missing, killing the build."
	exit 1
    fi

# (tpg) please add CONFIG that were carelessly enabled, while it is known these MUST be disabled
    if grep -Fxq "CONFIG_RT_GROUP_SCHED=y" .config ; then
	printf '%s\n' "Please stop enabling CONFIG_RT_GROUP_SCHED - this option is not recommended with systemd systemd/systemd#553, killing the build."
	exit 1
    fi
# (tpg) kernel modules are compresed manually inside spec file
    if ! grep -Fxq "CONFIG_MODULE_COMPRESS_NONE=y" .config ; then
	printf '%s\n' "Please do not disable CONFIG_MODULE_COMPRESS_NONE=y or set any other module compression inside .config, as this will bloat main package instead of debuginfo subpackage, killing the build."
	exit 1
    fi
# (tpg) stop enabling CONFIG_DEBUG_KERNEL
    if grep -Fxq "CONFIG_DEBUG_KERNEL=y" .config ; then
	printf '%s\n' "Please do not set CONFIG_DEBUG_KERNEL=y as this is relase build, and we are not developing kernel or its modules."
	exit 1
    fi
}

clangify() {
	sed -i \
		-e '/^CONFIG_CC_VERSION_TEXT=/d' \
		-e '/^CONFIG_CC_IS_GCC=/d' \
		-e '/^CONFIG_CC_IS_CLANG=/d' \
		-e '/^CONFIG_GCC_VERSION=/d' \
		-e '/^CONFIG_CLANG_VERSION=/d' \
		-e '/^CONFIG_LD_VERSION=/d' \
		-e '/^CONFIG_LD_IS_LLD=/d' \
		-e '/^CONFIG_LD_IS_BFD=/d' \
		-e '/^CONFIG_GCC_PLUGINS=/d' \
		"$1"
	cat >>"$1" <<'EOF'
CONFIG_CC_IS_CLANG=y
CONFIG_CC_HAS_ASM_GOTO_OUTPUT=y
CONFIG_LD_IS_LLD=y
CONFIG_INIT_STACK_NONE=y
# CONFIG_INIT_STACK_ALL_PATTERN is not set
# CONFIG_INIT_STACK_ALL_ZERO is not set
# CONFIG_KCSAN is not set
# CONFIG_SHADOW_CALL_STACK is not set
# CONFIG_LTO_NONE is not set
# CONFIG_LTO_CLANG_FULL is not set
CONFIG_LTO_CLANG_THIN=y
CONFIG_CFI_CLANG=y
CONFIG_CFI_CLANG_SHADOW=y
CONFIG_CFI_PERMISSIVE=y
CONFIG_RELR=y
EOF
}

amdify() {
	# Yes, it is intentional that CONFIG_AMD_NUMA gets disabled
	# for the AMD kernel -- AMD_NUMA is only for pre-ACPI systems
	# such as initial Opterons. Not useful for current AMD boxes.
	sed -i -E \
		-e 's/^CONFIG_GENERIC_CPU=y/# CONFIG_GENERIC_CPU is not set/' \
		-e 's/^# CONFIG_MZEN is not set/CONFIG_MZEN=y/' \
		-e '/CONFIG_HAVE_INTEL_TXT/d' \
		-e 's/^CONFIG_X86_INTEL_LPSS=y/# CONFIG_X86_INTEL_LPSS is not set/' \
		-e 's/^CONFIG_CPU_SUP_(INTEL|CENTAUR|ZHAOXIN)=y/# CONFIG_CPU_SUP_\1 is not set/' \
		-e 's/^CONFIG_X86_MCE_INTEL=y/# CONFIG_X86_MCE_INTEL is not set/' \
		-e 's/^CONFIG_MICROCODE_INTEL=y/# CONFIG_MICROCODE_INTEL is not set/' \
		-e 's/^CONFIG_X86_INTEL_PSTATE=y/# CONFIG_X86_INTEL_PSTATE is not set/' \
		-e 's/^CONFIG_INTEL_IDLE=y/# CONFIG_INTEL_IDLE is not set/' \
		-e 's/^CONFIG_INTEL_WMI(.*)=(y|m)/# CONFIG_INTEL_WMI\1 is not set/' \
		-e 's,^CONFIG_SND_SOC_INTEL(.*)=.*,# CONFIG_SND_SOC_INTEL\1 is not set,' \
		-e 's,^CONFIG_SND_SOC_SOF_INTEL(.*)=.*,# CONFIG_SND_SOC_SOF_INTEL\1 is not set,' \
		-e 's,^CONFIG_AMD_NUMA=y,# CONFIG_AMD_NUMA is not set,' \
		-e 's,^CONFIG_KVM_INTEL=m,# CONFIG_KVM_INTEL is not set,' \
		-e 's,^CONFIG_INTEL_SOC(.*)=(y|m),# CONFIG_INTEL_SOC\1 is not set,' \
		-e 's,^CONFIG_AGP_(INTEL|SIS|VIA)=(y|m),# CONFIG_AGP_\1 is not set,' \
		-e 's,^CONFIG_PECI=(y|m),# CONFIG_PECI is not set,' \
		-e 's,^CONFIG_INTEL_TDX_GUEST=(y|m),# CONFIG_INTEL_TDX_GUEST is not set,' \
		-e 's,^CONFIG_INTEL_IFS=(y|m),# CONFIG_INTEL_IFS is not set,' \
		"$1"
}

serverize() {
	sed -i -E \
		-e 's/^CONFIG_PREEMPT=y/# CONFIG_PREEMPT is not set/' \
		-e 's/^# CONFIG_PREEMPT_NONE is not set/CONFIG_PREEMPT_NONE=y/' \
		-e 's/CONFIG_HZ_1000=y/# CONFIG_HZ_1000 is not set/' \
		-e 's/^CONFIG_HZ_100 is not set/CONFIG_HZ_100=y/' \
		-e 's/^CONFIG_HZ=1000/CONFIG_HZ=100/' \
		"$1"
}

CreateConfig() {
	arch="$1"
	type="$2"
	config_dir=%{_sourcedir}
	CONFIGS=""
	rm -fv .config

	printf '%s\n' "<-- Creating config for kernel type ${type} for ${arch}"
	if echo $type |grep -qv gcc; then
		CC=clang
		CXX=clang++
		BUILD_LD="ld.lld --icf=none --no-gc-sections"
		BUILD_KBUILD_LDFLAGS="-Wl,--icf=none -Wl,--no-gc-sections"
		BUILD_TOOLS='LLVM=1 LLVM_IAS=1'
	else
		CC=gcc
		CXX=g++
		# force ld.bfd, Kbuild logic issues when ld is linked to something else
		BUILD_LD="%{_target_platform}-ld.bfd"
		BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_TOOLS=""
	fi

# (crazy) do not use %{S:X} to copy, if someone messes up we end up with broken stuff again
	case ${arch} in
	i?86)
		case ${type} in
		desktop|desktop-gcc|server|server-gcc)
			rm -f .config
			cp -v ${config_dir}/i686-omv-defconfig .config
			echo ${type} |grep -qv gcc && clangify .config
			echo ${type} |grep -q server && serverize .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	x86_64|x86|znver1)
		case ${type} in
		desktop|desktop-gcc|server|server-gcc)
			rm -f .config
			cp -v ${config_dir}/x86_64-omv-defconfig .config
			[ "${arch}" = "znver1" ] && amdify .config
			echo ${type} |grep -qv gcc && clangify .config
			echo ${type} |grep -q server && serverize .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	arm)
		case ${type} in
		desktop|desktop-gcc|server|server-gcc)
			rm -f .config
			cp -v ${config_dir}/armv7hnl-omv-defconfig .config
			echo ${type} |grep -qv gcc && clangify .config
			echo ${type} |grep -q server && serverize .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	arm64)
		case ${type} in
		desktop|desktop-gcc|server|server-gcc)
			rm -f .config
			cp -v ${config_dir}/aarch64-omv-defconfig .config
			echo ${type} |grep -qv gcc && clangify .config
			echo ${type} |grep -q server && serverize .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	ppc64)
		CONFIGS=pseries_defconfig
		;;
	ppc64le)
		CONFIGS="pseries_defconfig arch/powerpc/configs/le.config"
		;;
	*)
		CONFIGS=defconfig
		;;
	esac

# ( crazy) remove along with the old configs once ARM* and ppc* is finished
	if [[ -n "${CONFIGS}" ]]; then
		for i in common common-${type}; do
			[ -e kernel/configs/$i.config ] && CONFIGS="$CONFIGS $i.config"
		done
		for i in ${arch}-common ${arch}-${type}; do
			[ -e kernel/configs/$i.config ] && CONFIGS="$CONFIGS $i.config"
		done
	fi

	cfgarch=$arch
	if [ "$arch" = "znver1" ] || [ "$arch" = "x86_64" ]; then
		arch=x86
	elif echo $arch |grep -q ^ppc; then
		arch=powerpc
	fi

# ( crazy) remove along with the old configs once ARM* and ppc* is finished
	if [[ -n "${CONFIGS}" ]]; then
		make ARCH="${arch}" CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" V=0 $CONFIGS
	else
%if %{without lazy_developer}
## YES, intentionally, DIE on wrong config
		echo "=== Configuring ${arch} ${type} kernel ==="
		CheckConfig
		make ARCH="${arch}" CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" V=0 oldconfig
%else
		printf '%s\n' "Lazy developer option is enabled!!. Don't be lazy!."
## that takes kernel defaults on missing or changed things
## olddefconfig is similar to yes ... but not that verbose
		CheckConfig
		yes "" | make ARCH="${arch}" CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" oldconfig
%endif
	fi

	scripts/config --set-val BUILD_SALT \"$(echo "$arch-$type-%{EVRD}"|sha1sum|awk '{ print $1; }')\"
# " <--- workaround for vim syntax highlighting bug, ignore
	cp .config kernel/configs/omv-${cfgarch}-${type}.config
}

PrepareKernel() {
	name=$1
	extension=$2
	config_dir=%{_sourcedir}
	printf '%s\n' "<-- Preparing kernel $extension"
	%make_build -s mrproper
%ifarch znver1
	CreateConfig %{_target_cpu} ${flavour}
%else
	CreateConfig %{target_arch} ${flavour}
%endif
# make sure EXTRAVERSION says what we want it to say
	sed -ri "s|^(EXTRAVERSION =).*|\1 -$extension|" Makefile
}

BuildKernel() {
	KernelVer=$1
	printf '%s\n' "<--- Building kernel $KernelVer"

	if echo $1 |grep -qv gcc; then
		CC=clang
		CXX=clang++
		BUILD_LD="ld.lld --icf=none --no-gc-sections"
		BUILD_KBUILD_LDFLAGS="-Wl,--icf=none -Wl,--no-gc-sections"
		BUILD_TOOLS='LLVM=1 LLVM_IAS=1'
	else
		CC=gcc
		CXX=g++
# force ld.bfd, Kbuild logic issues when ld is linked  to something else
		BUILD_LD="%{_target_platform}-ld.bfd"
		BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_TOOLS=""
	fi

%ifarch %{arm}
	IMAGE=zImage
	TARGETS="${IMAGE} modules"
%else
%ifarch %{aarch64}
# (tpg) when booting with UEFI then uboot-tools is looking for a vmlinuz in PE-COFF format
	IMAGE=Image
	TARGETS="${IMAGE} modules dtbs"
%else
	IMAGE=bzImage
	TARGETS="${IMAGE} modules"
%endif
%endif
	%make_build V=0 VERBOSE=0 ARCH=%{target_arch} CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" $TARGETS

# Start installing stuff
	install -d %{temp_boot}
	install -d %{temp_modules}/$KernelVer

	install -m 644 System.map %{temp_modules}/$KernelVer/System.map
	install -m 644 .config %{temp_modules}/$KernelVer/config
	cp -f arch/%{target_arch}/boot/$IMAGE %{temp_boot}/vmlinuz-$KernelVer
	ln -sr %{_bootdir}/vmlinuz-$KernelVer %{temp_modules}/$KernelVer/vmlinuz
	ln -s %{_modulesdir}/$KernelVer/System.map %{temp_boot}/System.map-$KernelVer
	ln -s %{_modulesdir}/$KernelVer/config %{temp_boot}/config-$KernelVer

# modules
	install -d %{temp_modules}/$KernelVer
	%make_build V=0 VERBOSE=0 INSTALL_MOD_PATH=%{temp_root} ARCH=%{target_arch} SRCARCH=%{target_arch} KERNELRELEASE=$KernelVer CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" DEPMOD=/bin/true INSTALL_MOD_STRIP=1 modules_install

# headers
	%make_build V=0 VERBOSE=0 INSTALL_HDR_PATH=%{temp_root}%{_prefix} KERNELRELEASE=$KernelVer ARCH=%{target_arch} SRCARCH=%{target_arch} headers_install

%ifarch %{armx} %{ppc}
	%make_build  V=0 VERBOSE=0 ARCH=%{target_arch} CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" INSTALL_DTBS_PATH=%{temp_modules}/$KernelVer/dtb dtbs_install
	ln -s %{_modulesdir}/$KernelVer/dtb %{temp_boot}/dtb-$KernelVer
%endif

# remove /lib/firmware, we use a separate kernel-firmware
	rm -rf %{temp_root}/lib/firmware
}

SaveDevel() {
	devel_flavour=$1

	DevelRoot=/usr/src/linux-%{version}-$devel_flavour-%{release}%{disttag}
	TempDevelRoot=%{temp_root}$DevelRoot

	mkdir -p $TempDevelRoot
	for i in $(find . -name 'Makefile*'); do cp -R --parents $i $TempDevelRoot;done
	for i in $(find . -name 'Kconfig*' -o -name 'Kbuild*'); do cp -R --parents $i $TempDevelRoot;done
	cp -fR include $TempDevelRoot
	cp -fR scripts $TempDevelRoot
	cp -fR kernel/time/timeconst.bc $TempDevelRoot/kernel/time/
	cp -fR kernel/bounds.c $TempDevelRoot/kernel
	cp -fR tools/include $TempDevelRoot/tools/
%ifarch %{arm}
	cp -fR arch/%{target_arch}/tools $TempDevelRoot/arch/%{target_arch}/
%endif

%ifarch %{ix86} %{x86_64}
	cp -fR arch/x86/kernel/asm-offsets.{c,s} $TempDevelRoot/arch/x86/kernel/
	cp -fR arch/x86/kernel/asm-offsets_{32,64}.c $TempDevelRoot/arch/x86/kernel/
	cp -fR arch/x86/purgatory/* $TempDevelRoot/arch/x86/purgatory/
	cp -fR arch/x86/entry/syscalls/syscall* $TempDevelRoot/arch/x86/entry/syscalls/
	cp -fR arch/x86/include $TempDevelRoot/arch/x86/
	cp -fR arch/x86/tools $TempDevelRoot/arch/x86/
%else
	cp -fR arch/%{target_arch}/kernel/asm-offsets.{c,s} $TempDevelRoot/arch/%{target_arch}/kernel/
	for f in $(find arch/%{target_arch} -name include); do cp -fR --parents $f $TempDevelRoot; done
%endif

	cp -fR .config Module.symvers $TempDevelRoot

# Needed for truecrypt build (Danny)
	cp -fR drivers/md/dm.h $TempDevelRoot/drivers/md/

# Needed for lirc_gpio (#39004)
	cp -fR drivers/media/pci/bt8xx/bttv{,p}.h $TempDevelRoot/drivers/media/pci/bt8xx/
	cp -fR drivers/media/pci/bt8xx/bt848.h $TempDevelRoot/drivers/media/pci/bt8xx/
	cp -fR drivers/media/common/btcx-risc.h $TempDevelRoot/drivers/media/common/

# Needed for external dvb tree (#41418)
	cp -fR drivers/media/dvb-frontends/lgdt330x.h $TempDevelRoot/drivers/media/dvb-frontends/

# orc unwinder needs theese
	cp -fR tools/build/Build{,.include} $TempDevelRoot/tools/build
	cp -fR tools/build/fixdep.c $TempDevelRoot/tools/build
	cp -fR tools/lib/{str_error_r.c,string.c} $TempDevelRoot/tools/lib
	cp -fR tools/lib/subcmd/* $TempDevelRoot/tools/lib/subcmd
	cp -fR tools/objtool/* $TempDevelRoot/tools/objtool
	cp -fR tools/scripts/utilities.mak $TempDevelRoot/tools/scripts

# Make clean fails on the include statements in the Makefiles - and the drivers aren't relevant for -devel
	rm -rf $TempDevelRoot/drivers/net/wireless/rtl8*
	sed -i -e '/rtl8.*/d' $TempDevelRoot/drivers/net/wireless/{Makefile,Kconfig}
	sed -i -e '/rtl8723cs.*/d' $TempDevelRoot/drivers/staging/{Makefile,Kconfig}

	for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 loongarch m32r m68k m68knommu metag microblaze \
		 mips mn10300 nds32 nios2 openrisc parisc s390 score sh sparc tile unicore32 xtensa; do
		rm -rf $TempDevelRoot/arch/$i
	done

# Clean the scripts tree, and make sure everything is ok (sanity check)
# running prepare+scripts (tree was already "prepared" in build)
	cd $TempDevelRoot >/dev/null
	%make_build V=0 VERBOSE=0 ARCH=%{target_arch} clean
	cd - >/dev/null

	rm -f $TempDevelRoot/.config.old

# fix permissions
	chmod -R a+rX $TempDevelRoot

	kernel_devel_files=kernel_devel_files.$devel_flavour

### Create the kernel_devel_files.*
	cat > $kernel_devel_files <<EOF
%dir $DevelRoot
%dir $DevelRoot/arch
%dir $DevelRoot/include
$DevelRoot/Documentation
$DevelRoot/arch/arm
$DevelRoot/arch/arm64
$DevelRoot/arch/powerpc
$DevelRoot/arch/riscv
$DevelRoot/arch/um
$DevelRoot/arch/x86
$DevelRoot/block
$DevelRoot/crypto
# here
$DevelRoot/certs
$DevelRoot/drivers
$DevelRoot/fs
$DevelRoot/include/acpi
$DevelRoot/include/asm-generic
$DevelRoot/include/clocksource
$DevelRoot/include/config
$DevelRoot/include/crypto
$DevelRoot/include/drm
$DevelRoot/include/dt-bindings
$DevelRoot/include/generated
$DevelRoot/include/keys
$DevelRoot/include/kunit
$DevelRoot/include/kvm
$DevelRoot/include/linux
$DevelRoot/include/math-emu
$DevelRoot/include/media
$DevelRoot/include/memory
$DevelRoot/include/misc
$DevelRoot/include/net
$DevelRoot/include/pcmcia
$DevelRoot/include/ras
$DevelRoot/include/rdma
$DevelRoot/include/rv
$DevelRoot/include/scsi
$DevelRoot/include/soc
$DevelRoot/include/sound
$DevelRoot/include/target
$DevelRoot/include/trace
$DevelRoot/include/uapi
$DevelRoot/include/ufs
$DevelRoot/include/vdso
$DevelRoot/include/video
$DevelRoot/include/xen
$DevelRoot/init
$DevelRoot/io_uring
$DevelRoot/ipc
$DevelRoot/kernel
$DevelRoot/lib
$DevelRoot/mm
$DevelRoot/net
$DevelRoot/rust
$DevelRoot/samples
$DevelRoot/scripts
$DevelRoot/security
$DevelRoot/sound
$DevelRoot/tools
$DevelRoot/usr
$DevelRoot/virt
$DevelRoot/.config
$DevelRoot/Kbuild
$DevelRoot/Kconfig
$DevelRoot/Makefile
$DevelRoot/Module.symvers
$DevelRoot/arch/Kconfig
EOF

### Create -devel Post script on the fly
cat > $kernel_devel_files-post <<EOF
if [ -d %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag} ]; then
    rm -f %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/{build,source}
    ln -sf $DevelRoot %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/build
    ln -sf $DevelRoot %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/source
fi
EOF


### Create -devel Preun script on the fly
cat > $kernel_devel_files-preun <<EOF
if [ -L %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/build ]; then
    rm -f %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/build
fi
if [ -L %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/source ]; then
    rm -f %{_modulesdir}/%{version}-$devel_flavour-%{release}%{disttag}/source
fi
exit 0
EOF

### Create -devel Postun script on the fly
cat > $kernel_devel_files-postun <<EOF
rm -rf /usr/src/linux-%{version}-$devel_flavour-%{release}%{disttag} >/dev/null
EOF
}

SaveDebug() {
	debug_flavour=$1

	install -m 644 vmlinux %{temp_boot}/vmlinux-%{version}-$debug_flavour-%{release}%{disttag}
	kernel_debug_files=kernel_debug_files.$debug_flavour
	printf '%s\n' "%{_bootdir}/vmlinux-%{version}-$debug_flavour-%{release}%{disttag}" >> $kernel_debug_files

	find %{temp_modules}/%{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko" -type f | %kxargs -I '{}' objcopy --only-keep-debug '{}' '{}'.debug
	find %{temp_modules}/%{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko" -type f | %kxargs -I '{}' sh -c 'cd $(dirname {}); objcopy --add-gnu-debuglink=$(basename {}).debug --strip-debug $(basename {})'
	find %{temp_modules}/%{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko" -type f -exec strip --strip-debug {} +
	find %{temp_modules}/%{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko" -type f |while read r; do
# sign modules after stripping
		scripts/sign-file sha1 certs/signing_key.pem certs/signing_key.x509 $r
	done

	cd %{temp_modules}
	    find %{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko.debug" -type f > debug_module_list
	cd -
	cat %{temp_modules}/debug_module_list | sed 's|\(.*\)|%{_modulesdir}/\1|' >> $kernel_debug_files
	cat %{temp_modules}/debug_module_list | sed 's|\(.*\)|%exclude %{_modulesdir}/\1|' >> ../kernel_exclude_debug_files.$debug_flavour
	rm -f %{temp_modules}/debug_module_list
}

CreateFiles() {
	kernel_flavour=$1
	kernel_files=kernel_files.$kernel_flavour

### Create the kernel_files.*
	cat > $kernel_files <<EOF
%{_bootdir}/System.map-%{version}-$kernel_flavour-%{release}%{disttag}
%{_bootdir}/config-%{version}-$kernel_flavour-%{release}%{disttag}
%{_bootdir}/vmlinuz-%{version}-$kernel_flavour-%{release}%{disttag}
%dir %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/System.map
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/config
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/vmlinuz
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/net/appletalk
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/net/can
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/net/decnet
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/drivers/infiniband
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/drivers/isdn
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/drivers/net/arcnet
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/drivers/net/can
%exclude %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/kernel/drivers/net/fddi
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/modules.*
# device tree binary
%ifarch %{armx}
%{_bootdir}/dtb-%{version}-$kernel_flavour-%{release}%{disttag}
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/dtb
%endif
EOF

%if %{with build_debug}
    cat ../kernel_exclude_debug_files.$kernel_flavour >> $kernel_files
%endif

### Create kernel Posttrans script
cat > $kernel_files-posttrans <<EOF
[ -x %{_bindir}/depmod ] && %{_bindir}/depmod -a %{version}-$kernel_flavour-%{release}%{disttag}

%ifnarch %{armx} %{riscv}
[ -x %{_bindir}/dracut ] && %{_bindir}/dracut -f --kver %{version}-$kernel_flavour-%{release}%{disttag}
[ -x %{_bindir}/update-grub2 ] && %{_bindir}/update-grub2 ||:
%endif

%ifarch %{aarch64}
if [ -d /boot/efi ] && [ -x %{_bindir}/kernel-install ]; then
    %{_bindir}/kernel-install add %{version}-$kernel_flavour-%{release}%{disttag} %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/vmlinuz
fi
%endif

## cleanup some werid symlinks we never used anyway
rm -rf vmlinuz-{server,desktop} initrd0.img initrd-{server,desktop} || :

%if %{with build_devel}
# create kernel-devel symlinks if matching -devel- rpm is installed
if [ -d /usr/src/linux-%{version}-$kernel_flavour-%{release}%{disttag} ]; then
    rm -f %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/{build,source}
    ln -sf /usr/src/linux-%{version}-$kernel_flavour-%{release}%{disttag} %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/build
    ln -sf /usr/src/linux-%{version}-$kernel_flavour-%{release}%{disttag} %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/source
fi
%endif

if [ -x %{_bindir}/dkms_autoinstaller ] && [ -d /usr/src/linux-%{version}-$kernel_flavour-%{release}%{disttag} ]; then
    %{_bindir}/dkms_autoinstaller start %{version}-$kernel_flavour-%{release}%{disttag}
fi

if [ -x %{_bindir}/dkms ] && [ -e %{_unitdir}/dkms.service ] && [ -d /usr/src/linux-%{version}-$kernel_flavour-%{release}%{disttag} ]; then
    %{_bindir}/systemctl --quiet restart dkms.service
    %{_bindir}/systemctl --quiet try-restart loadmodules.service
    %{_bindir}/dkms autoinstall --verbose --kernelver %{version}-$kernel_flavour-%{release}%{disttag}
fi
EOF

### Create kernel Postun script on the fly
cat > $kernel_files-postun <<EOF

[ -e %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/modules.{alias{,.bin},builtin.bin,dep{,.bin},devname,softdep,symbols{,.bin}} ||:
[ -e /boot/vmlinuz-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/vmlinuz-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/initrd-%{version}-$kernel_flavour-%{release}%{disttag}.img ] && rm -rf /boot/initrd-%{version}-$kernel_flavour-%{release}%{disttag}.img
[ -e /boot/System.map-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/System.map-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/config-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/config-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/dtb-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/dtb-%{version}-$kernel_flavour-%{release}%{disttag}

%ifarch %{aarch64}
if [ -d /boot/efi ] && [ -x %{_bindir}/kernel-install ]; then
    %{_bindir}/kernel-install remove %{version}-$kernel_flavour-%{release}%{disttag} || :
fi
%endif

rm -rf %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag} >/dev/null
if [ -d /var/lib/dkms ]; then
    rm -f /var/lib/dkms/*/kernel-%{version}-$devel_flavour-%{release}%{disttag}-%{_target_cpu} >/dev/null
    rm -rf /var/lib/dkms/*/*/%{version}-$devel_flavour-%{release}%{disttag} >/dev/null
    rm -f /var/lib/dkms-binary/*/kernel-%{version}-$devel_flavour-%{release}%{disttag}-%{_target_cpu} >/dev/null
    rm -rf /var/lib/dkms-binary/*/*/%{version}-$devel_flavour-%{release}%{disttag} >/dev/null
fi

%if %{with build_devel}
if [ -L %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/build ]; then
    rm -f %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/build
fi
if [ -L %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/source ]; then
    rm -f %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/source
fi
%endif
exit 0
EOF
}

# Create a simulacro of buildroot
rm -rf %{temp_root}
install -d %{temp_root}

###
### Let's build some kernel
###

# Build the configs for every arch we care about
# that way, we can be sure all *.config files have the right additions
for a in arm arm64 i386 x86_64 znver1 powerpc riscv; do
	for t in desktop server; do
		CreateConfig $a $t
		export ARCH=$a
		[ "$ARCH" = "znver1" ] && export ARCH=x86
%if %{with cross_headers}
		if [ "$t" = "desktop" ]; then
# While we have a kernel configured for it, let's package
# headers for crosscompilers...
# Done in a for loop because we may have to install the same
# headers multiple times, e.g.
# aarch64-linux-gnu, aarch64-linux-musl, aarch64-linux-android
# all share the same kernel headers.
# This is a little ugly because the kernel's arch names don't match
# triplets...
			for i in %{long_cross_header_archs}; do
				[ "$i" = "%{_target_platform}" ] && continue
				TripletArch=$(echo ${i} |cut -d- -f1)
				SARCH=${a}
				case $TripletArch in
				aarch64)
					[ "$a" != "arm64" ] && continue
					;;
				arm*)
					[ "$a" != "arm" ] && continue
					;;
				i?86|athlon|pentium?)
					[ "$a" != "i386" ] && continue
					ARCH=x86
					SARCH=x86
					;;
				x86_64|znver1)
					[ "$a" != "x86_64" ] && continue
					SARCH=x86
					;;
				riscv*)
					SARCH=riscv
					;;
				ppc*)
					ARCH=powerpc
					SARCH=powerpc
					;;
				*)
					[ "$a" != "$TripletArch" ] && continue
					;;
				esac
				%make_build V=0 VERBOSE=0 ARCH=${a} SRCARCH=${SARCH} INSTALL_HDR_PATH=%{temp_root}%{_prefix}/${i} headers_install
			done
		fi
%endif
	done
done
unset ARCH
make mrproper

# (tpg) build kernels for all flavours
for flavour in %{kernel_flavours}; do
    PrepareKernel ${flavour} ${flavour}-%{release}%{disttag}
    BuildKernel %{version}-${flavour}-%{release}%{disttag}
%if %{with build_devel}
	SaveDevel ${flavour}
%endif
%if %{with build_debug}
	SaveDebug ${flavour}
%endif
	CreateFiles ${flavour}
done

# set extraversion to match srpm to get nice version reported by the tools
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{release}|" Makefile

# We install all tools here too (rather than in %%install
# where it really belongs): make mrproper in preparation
# for packaging kernel-source would force a rebuild

%if %{with build_cpupower}
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%make_build -C tools/power/cpupower CPUFREQ_BENCH=false LDFLAGS="%{optflags}"
%make_install -C tools/power/cpupower DESTDIR=%{temp_root} libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false CC=%{__cc} LDFLAGS="%{optflags}"
%endif

%ifarch %{ix86} %{x86_64}
%if %{with build_x86_energy_perf_policy}
%make_build -C tools/power/x86/x86_energy_perf_policy CC=clang LDFLAGS="-Wl,--build-id=none"
mkdir -p %{temp_root}%{_bindir} %{temp_root}%{_mandir}/man8
%make_install -C tools/power/x86/x86_energy_perf_policy DESTDIR="%{temp_root}"
%endif

%if %{with build_turbostat}
%make_build -C tools/power/x86/turbostat CC=clang
mkdir -p %{temp_root}%{_bindir} %{temp_root}%{_mandir}/man8
%make_install -C tools/power/x86/turbostat DESTDIR="%{temp_root}"
%endif
%endif

%if %{with bpftool}
# FIXME As of lld 12.0 and kernel 5.11, lld results in unresolved symbols, ld.bfd works
%make_build -C tools/lib/bpf CC=clang LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd VMLINUX_BPF=%{temp_root}%{_bootdir}/vmlinuz-%{version}-desktop-%{release}%{disttag} libbpf.a libbpf.pc libbpf.so -j1
%make_build -C tools/bpf/bpftool CC=clang LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd VMLINUX_BPF=%{temp_root}%{_bootdir}/vmlinuz-%{version}-desktop-%{release}%{disttag} bpftool -j1
%make_install -C tools/lib/bpf install_headers DESTDIR=%{temp_root} prefix=%{_prefix} libdir=%{_libdir} CC=clang CXX=clang++ LD=ld.bfd HOSTLD=ld.bfd VMLINUX_BPF=%{temp_root}%{_bootdir}/vmlinuz-%{version}-desktop-%{release}%{disttag}
%make_install -C tools/bpf/bpftool CC=clang CXX=clang++ LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd DESTDIR=%{temp_root} prefix=%{_prefix} bash_compdir=%{_sysconfdir}/bash_completion.d/ mandir=%{_mandir} VMLINUX_BPF=%{temp_root}%{_bootdir}/vmlinuz-%{version}-desktop-%{release}%{disttag}
%endif

%if %{with perf}
[ -e %{_sysconfdir}/profile.d/90java.sh ] && . %{_sysconfdir}/profile.d/90java.sh
%make_build -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.bfd HOSTLD=ld.bfd WERROR=0 prefix=%{_prefix} all man
# Not SMP safe
make -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.bfd HOSTLD=ld.bfd WERROR=0 prefix=%{_prefix} DESTDIR_SQ=%{temp_root} DESTDIR=%{temp_root} install install-man
%endif

%if %{with hyperv}
%make_build -C tools/hv -s CC=%{__cc} HOSTCC=%{__cc} prefix=%{_prefix} sbindir=%{_sbindir}
%make_install -C tools/hv -s CC=%{__cc} HOSTCC=%{__cc} prefix=%{_prefix} sbindir=%{_sbindir} DESTDIR=%{temp_root}
mkdir -p %{temp_root}%{_unitdir}
install -c -m 644 %{S:7000} %{S:7002} %{S:7004} %{temp_root}%{_unitdir}/
mkdir -p %{temp_root}%{_udevrulesdir}
install -c -m 644 %{S:7001} %{temp_root}%{_udevrulesdir}/70-hypervkvp.rules
install -c -m 644 %{S:7003} %{temp_root}%{_udevrulesdir}/70-hypervvss.rules
install -c -m 644 %{S:7005} %{temp_root}%{_udevrulesdir}/70-hypervfcopy.rules
%endif

# We don't make to repeat the depend code at the install phase
%if %{with build_source}
PrepareKernel "" %{release}custom
%make_build -s mrproper
%endif

###
### install
###

%install
# Directories definition needed for installing
%define target_source %{buildroot}%{_kerneldir}
%define target_boot %{buildroot}%{_bootdir}
%define target_modules %{buildroot}%{_modulesdir}

# We want to be able to test several times the install part
rm -rf %{buildroot}
cp -a %{temp_root} %{buildroot}

# We used to have a copy of PrepareKernel here
# Now, we make sure that the thing in the linux dir is what we want it to be
for i in %{target_modules}/*; do
    rm -f $i/build $i/source
done

# binmerge
%if "%{_bindir}" == "%{_sbindir}"
mv %{buildroot}%{_prefix}/sbin/* %{buildroot}%{_bindir}/
rmdir %{buildroot}%{_prefix}/sbin
%endif

# (tpg) let's compress all modules
find %{target_modules} -name "*.ko" -type f | %kxargs zstd --format=zstd --ultra -22 -T0 --rm -f -q

# sniff, if we compressed all the modules, we change the stamp :(
# we really need the depmod -ae here
pushd %{target_modules}
for i in *; do
    %{_bindir}/depmod -ae -b %{buildroot} -F %{target_modules}/"$i"/System.map "$i"
    echo $?
done

for i in *; do
    pushd $i
	printf '%s\n' "Creating modules.description for $i"
	modules=$(find . -name "*.ko.[gxz]*[z|st]" -type f)
	echo $modules | %kxargs %{_bindir}/modinfo | perl -lne 'print "$name\t$1" if $name && /^description:\s*(.*)/; $name = $1 if m!^filename:\s*(.*)\.k?o!; $name =~ s!.*/!!' > modules.description
    popd
done
popd

# need to set extraversion to match srpm again to avoid rebuild
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{release}|" Makefile

%if %{with build_cpupower}
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{SOURCE30} %{buildroot}%{_unitdir}/cpupower.service
install -m644 %{SOURCE31} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
%endif

# Create directories infastructure
%if %{with build_source}
install -d %{target_source}

# Package what remains
tar cf - . | tar xf - -C %{target_source}
chmod -R a+rX %{target_source}

rm -f %{target_source}/*.lang

# File lists aren't needed
rm -f %{target_source}/*_files.* %{target_source}/README.kernel-sources

# we remove all the source files that we don't ship
# first architecture files
for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 loongarch m32r m68k m68knommu metag microblaze \
	mips nds32 nios2 openrisc parisc s390 score sh sh64 sparc tile unicore32 v850 xtensa mn10300; do
    rm -rf %{target_source}/arch/$i
    rm -rf %{target_source}/scripts/dtc/include-prefixes/$i
    rm -rf %{target_source}/tools/arch/$i
    rm -rf %{target_source}/tools/testing/selftests/$i
done

# other misc files
rm -f %{target_source}/{.config.old,.config.cmd,.gitignore,.lst,.mailmap,.gitattributes,.get_maintainer.ignore}
rm -f %{target_source}/{.missing-syscalls.d,arch/.gitignore,firmware/.gitignore,.gitattributes}
rm -rf %{target_source}/.tmp_depmod/
rm -rf %{buildroot}/usr/src/linux-*/uksm.txt

# more cleaning
rm -f %{target_source}/arch/x86_64/boot/bzImage
cd %{target_source}
# lots of gitignore files
find -iname ".gitignore" -delete
# clean tools tree
%make_build -C tools clean -j1 V=0 VERBOSE=0
%make_build -C tools/build clean -j1 V=0 VERBOSE=0
%make_build -C tools/build/feature clean -j1 V=0 VERBOSE=0
rm -f .cache.mk

# Drop script binaries that can be rebuilt
find tools scripts -executable |while read r; do
    if file $r |grep -q ELF; then
	rm -f $r
    fi
done
cd -

#endif %{with build_source}
%endif

%if %{with build_source}
%files -n %{name}-source
%dir %{_kerneldir}
%dir %{_kerneldir}/arch
%dir %{_kerneldir}/include
%dir %{_kerneldir}/certs
%{_kerneldir}/.clang-format
%{_kerneldir}/.cocciconfig
%{_kerneldir}/Documentation
%{_kerneldir}/arch/Kconfig
%{_kerneldir}/arch/arm
%{_kerneldir}/arch/arm64
%{_kerneldir}/arch/powerpc
%{_kerneldir}/arch/riscv
%{_kerneldir}/arch/um
%{_kerneldir}/arch/x86
%{_kerneldir}/block
%{_kerneldir}/crypto
%{_kerneldir}/drivers
%{_kerneldir}/fs
%{_kerneldir}/certs/*
%{_kerneldir}/include/acpi
%{_kerneldir}/include/asm-generic
%{_kerneldir}/include/clocksource
%{_kerneldir}/include/crypto
%{_kerneldir}/include/drm
%{_kerneldir}/include/dt-bindings
%{_kerneldir}/include/keys
%{_kerneldir}/include/kunit
%{_kerneldir}/include/kvm
%{_kerneldir}/include/linux
%{_kerneldir}/include/math-emu
%{_kerneldir}/include/media
%{_kerneldir}/include/memory
%{_kerneldir}/include/misc
%{_kerneldir}/include/net
%{_kerneldir}/include/pcmcia
%{_kerneldir}/include/ras
%{_kerneldir}/include/rdma
%{_kerneldir}/include/rv
%{_kerneldir}/include/scsi
%{_kerneldir}/include/soc
%{_kerneldir}/include/sound
%{_kerneldir}/include/target
%{_kerneldir}/include/trace
%{_kerneldir}/include/uapi
%{_kerneldir}/include/ufs
%{_kerneldir}/include/vdso
%{_kerneldir}/include/video
%{_kerneldir}/include/xen
%{_kerneldir}/init
%{_kerneldir}/io_uring
%{_kerneldir}/ipc
%{_kerneldir}/kernel
%{_kerneldir}/lib
%{_kerneldir}/mm
%{_kerneldir}/net
%{_kerneldir}/rust
%{_kerneldir}/.rustfmt.toml
%{_kerneldir}/samples
%{_kerneldir}/scripts
%{_kerneldir}/security
%{_kerneldir}/sound
%{_kerneldir}/tools
%{_kerneldir}/usr
%{_kerneldir}/virt
%{_kerneldir}/COPYING
%{_kerneldir}/CREDITS
%{_kerneldir}/Kbuild
%{_kerneldir}/Kconfig
%{_kerneldir}/LICENSES
%{_kerneldir}/MAINTAINERS
%{_kerneldir}/Makefile
%{_kerneldir}/README
%endif

%if %{with build_doc}
%files -n %{name}-doc
%doc Documentation/*
%endif

%if %{with perf}
%files -n perf
%{_bindir}/perf
%ifarch %{x86_64}
%optional %{_bindir}/perf-read-vdso32
%endif
%{_bindir}/trace
%dir %{_prefix}/libexec/perf-core
%{_prefix}/libexec/perf-core/*
%doc %{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
%{_prefix}/lib/perf
%ifarch %{x86_64}
%{_libdir}/libperf-jvmti.so
%else
%{_prefix}/lib/libperf-jvmti.so
%endif
%doc %{_docdir}/perf-tip
%{_datadir}/perf-core
%endif

%if %{with build_cpupower}
%files -n cpupower -f cpupower.lang
%{_bindir}/cpupower
%{_libdir}/libcpupower.so.0
%{_libdir}/libcpupower.so.0.0.1
%{_unitdir}/cpupower.service
%doc %{_mandir}/man[1-8]/cpupower*
%{_datadir}/bash-completion/completions/cpupower
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower

%files -n cpupower-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h
%endif

%ifarch %{ix86} %{x86_64}
%if %{with build_x86_energy_perf_policy}
%files -n x86_energy_perf_policy
%{_bindir}/x86_energy_perf_policy
%doc %{_mandir}/man8/x86_energy_perf_policy.8*
%endif

%if %{with build_turbostat}
%files -n turbostat
%{_bindir}/turbostat
%doc %{_mandir}/man8/turbostat.8*
%endif
%endif

%if %{with bpftool}
%files -n bpftool
%{_bindir}/bpftool
%{_sysconfdir}/bash_completion.d/bpftool

%files -n %{libbpf}
%{_libdir}/libbpf.so.%{bpf_major}*

%files -n %{libbpfdevel}
%{_libdir}/libbpf.so
%{_libdir}/pkgconfig/*.pc
%dir %{_includedir}/bpf
%{_includedir}/bpf/*.h
%endif
