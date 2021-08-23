# utils/cpuidle-info.c:193: error: undefined reference to 'cpufreq_cpu_exists'
# investigate aarch64
%define _binaries_in_noarch_packages_terminate_build   0
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

%bcond_with gcc
%bcond_without clang

# IMPORTANT
# This is the place where you set kernel version i.e 4.5.0
# compose tar.xz name and release
%define kernelversion	5
%define patchlevel	14
%define sublevel	0
%define relc		7
# Only ever wrong on x.0 releases...
%define previous	%{kernelversion}.%(echo $((%{patchlevel}-1)))

%define buildrel	%{kversion}-%{buildrpmrel}
%define rpmtag		%{disttag}

# IMPORTANT
# This is the place where you set release version %{version}-1omv2015
%if 0%{relc}
%define rpmrel		0.rc%{relc}.1
%define tar_ver		%{kernelversion}.%{patchlevel}-rc%{relc}
%else
%define rpmrel		4
%define tar_ver		%{kernelversion}.%{patchlevel}
%endif
%define buildrpmrel	%{rpmrel}%{rpmtag}

# kernel Makefile extraversion is substituted by
# kpatch wich are either 0 (empty), rc (kpatch)
%define kpatch		%{nil}

# kernel base name (also name of srpm)
%if 0%{relc}
%define kname		kernel-rc
%else
%define kname		kernel-release
%endif

# version defines
%define kversion	%{kernelversion}.%{patchlevel}.%{sublevel}
%define kverrel		%{kversion}-%{rpmrel}

# Having different top level names for packges means that you have to remove
# them by hard :(
%define top_dir_name	%{kname}-%{_arch}

%define build_dir	${RPM_BUILD_DIR}/%{top_dir_name}

# Common target directories
%define _kerneldir /usr/src/linux-%{kversion}-%{buildrpmrel}
%define _bootdir /boot
%define _modulesdir /lib/modules
%define _efidir %{_bootdir}/efi/EFI/openmandriva

# Directories definition needed for building
%define temp_root %{build_dir}/temp-root
%define temp_source %{temp_root}%{_kerneldir}
%define temp_boot %{temp_root}%{_bootdir}
%define temp_modules %{temp_root}%{_modulesdir}

# Build defines
%bcond_with build_doc
%ifarch %{ix86} %{x86_64}
# FIXME re-enable once ported to 5.14
%bcond_with uksm
%else
%bcond_with uksm
%endif

%bcond_with build_source
%bcond_with build_devel
%bcond_without cross_headers

%bcond_with lazy_developer
%bcond_with build_debug
%bcond_with dracut_all_initrd
%bcond_without clr
%bcond_with vbox_orig_mods
# FIXME re-enable by default when the patches have been adapted to 5.8
%bcond_with saa716x
%bcond_with rtl8821ce

%global cross_header_archs	aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv32-linuxmusl riscv64-linuxmusl aarch64-android armv7l-android armv8l-android x86_64-android aarch64-linuxuclibc armv7hnl-linuxuclibc i686-linuxuclibc x86_64-linuxuclibc x32-linuxuclibc riscv32-linuxuclibc riscv64-linuxuclibc ppc64le-linux ppc64-linux ppc64le-linuxmusl ppc64-linuxmusl ppc64le-linuxuclibc ppc64-linuxuclibc
%global long_cross_header_archs %(
	for i in %{cross_header_archs}; do
		CPU=$(echo $i |cut -d- -f1)
		OS=$(echo $i |cut -d- -f2)
		echo -n "$(rpm --target=${CPU}-${OS} -E %%{_target_platform}) "
	done
)

%ifarch %{x86_64}
# BEGIN OF FLAVOURS
%bcond_without build_desktop
%bcond_without build_server
# END OF FLAVOURS
%endif

%ifarch %{ix86}
# BEGIN OF FLAVOURS
%bcond_without build_desktop
%bcond_with build_server
# END OF FLAVOURS
%endif

# build perf and cpupower tools
%if 0%{relc}
# One version of bpf and perf is enough - let's build it for stable only
%bcond_with perf
%bcond_with bpftool
%else
%bcond_without perf
# FIXME figure out why bpftool won't build on aarch64
# as of 5.9.1, error is:
# ./tools/bpf/resolve_btfids/resolve_btfids vmlinux
# FAILED: load BTF from vmlinux: Unknown error -2+ on_exit
%ifarch %{aarch64}
%bcond_with bpftool
%else
%bcond_without bpftool
%endif
%endif
%bcond_without build_x86_energy_perf_policy
%bcond_without build_turbostat
%ifarch %{ix86} %{x86_64}
%bcond_without build_cpupower
%else
# cpupower is currently x86 only
%bcond_with build_cpupower
%endif

# ARM builds
%ifarch %{armx}
%bcond_with build_desktop
%bcond_without build_server
%endif

# RISC-V
%ifarch %{riscv}
%bcond_without build_desktop
%bcond_with build_server
%endif

# End of user definitions

# For the .nosrc.rpm
%bcond_with build_nosrc

###################################################
###  Linker end1 > Check point to build for omv ###
###################################################
# Parallelize xargs invocations on smp machines
%define kxargs xargs %([ -z "$RPM_BUILD_NCPUS" ] \\\
	&& RPM_BUILD_NCPUS="$(/usr/bin/getconf _NPROCESSORS_ONLN)"; \\\
	[ "$RPM_BUILD_NCPUS" -gt 1 ] && echo "-P $RPM_BUILD_NCPUS")

%define target_arch %(echo %{_arch} | sed -e 's/mips.*/mips/' -e 's/arm.*/arm/' -e 's/aarch64/arm64/' -e 's/x86_64/x86/' -e 's/i.86/x86/' -e 's/znver1/x86/' -e 's/riscv.*/riscv/' -e 's/ppc.*/powerpc/')

#
# SRC RPM description
#
Summary:	Linux kernel built for %{distribution}
Name:		%{kname}
Version:	%{kversion}
Release:	%{rpmrel}
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
%if 0%{relc}
Source0:	https://git.kernel.org/torvalds/t/linux-%{tar_ver}.tar.gz
%else
Source0:	http://www.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{tar_ver}.tar.xz
Source1:	http://www.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{tar_ver}.tar.sign
%endif
### This is for stripped SRC RPM
%if %{with build_nosrc}
NoSource:	0
%endif

Source3:	README.kernel-sources
Source4:	%{name}.rpmlintrc
## all in one configs for each kernel
Source10:	x86_64-desktop-gcc-omv-defconfig
Source11:	x86_64-server-gcc-omv-defconfig
Source12:	x86_64-znver-desktop-gcc-omv-defconfig
Source13:	x86_64-znver-server-gcc-omv-defconfig
Source14:	i686-desktop-gcc-omv-defconfig
Source15:	i686-server-gcc-omv-defconfig
Source16:	armv7hnl-desktop-omv-defconfig
Source17:	armv7hnl-server-omv-defconfig
Source18:	aarch64-desktop-omv-defconfig
Source19:	aarch64-server-omv-defconfig

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

%if 0%{sublevel}
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

# (crazy) I really need to send that upstream soon
Patch10:	iwlwifi-fix-5e003982b07ae.patch
Patch11:	linux-5.13-attribute-error.patch
Patch30:	linux-5.6-fix-disassembler-4args-detection.patch
Patch31:	die-floppy-die.patch
Patch32:	0001-Add-support-for-Acer-Predator-macro-keys.patch
Patch33:	linux-4.7-intel-dvi-duallink.patch
Patch34:	kernel-5.6-kvm-gcc10.patch
Patch35:	linux-5.2.9-riscv-compile.patch
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
# FIXME hardening the module loader breaks it when
# using binutils 2.35, https://sourceware.org/bugzilla/show_bug.cgi?id=26378
# Let's revert it for now until there's a good fix.
Patch41:	workaround-aarch64-module-loader.patch
%if %{with clang}
# (tpg) https://github.com/ClangBuiltLinux/linux/issues/1341
Patch42:	linux-5.11-disable-ICF-for-CONFIG_UNWINDER_ORC.patch
%endif

# (tpg)
# The Ultra Kernel Same Page Deduplication
# http://kerneldedup.org/en/projects/uksm/download/
# sources can be found here https://github.com/dolohow/uksm
%if %{with uksm}
# breaks armx builds
Patch43:	https://raw.githubusercontent.com/dolohow/uksm/master/v5.x/uksm-5.13.patch
%endif

# (crazy) see: https://forum.openmandriva.org/t/nvme-ssd-m2-not-seen-by-omlx-4-0/2407
Patch44:	Unknow-SSD-HFM128GDHTNG-8310B-QUIRK_NO_APST.patch
# Restore ACPI loglevels to sane values
Patch45:	https://gitweb.frugalware.org/wip_kernel/raw/86234abea5e625043153f6b8295642fd9f42bff0/source/base/kernel/acpi-use-kern_warning_even_when_error.patch
Patch46:	https://gitweb.frugalware.org/wip_kernel/raw/23f5e50042768b823e18613151cc81b4c0cf6e22/source/base/kernel/fix-acpi_dbg_level.patch
Patch48:	linux-5.4.5-fix-build.patch
Patch51:	linux-5.5-corsair-strafe-quirks.patch
Patch52:	http://crazy.dev.frugalware.org/smpboot-no-stack-protector-for-gcc10.patch

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
Patch203:	0124-Extend-FEC-enum.patch
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
Source1006:	vbox-5.10.patch
Source1007:	vboxnet-clang.patch

# Better support for newer x86 processors
# More actively maintained for newer kernels
Patch211:	https://github.com/sirlucjan/kernel-patches/blob/master/5.2/cpu-patches/0001-cpu-5.2-merge-graysky-s-patchset.patch

# Assorted fixes

# Modular binder and ashmem -- let's try to make anbox happy
#Patch212:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/android-enable-building-ashmem-and-binder-as-modules.patch
#Patch213:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/export-symbols-needed-by-android-drivers.patch

# Fix CPU frequency governor mess caused by recent Intel patches
Patch225:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/0001-Revert-cpufreq-Avoid-configuring-old-governors-as-de.patch
Patch226:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/revert-parts-of-a00ec3874e7d326ab2dffbed92faddf6a77a84e9-no-Intel-NO.patch

# Fix perf
Patch230:	linux-5.11-perf-compile.patch

# (tpg) Armbian ARM Patches
Patch240:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-fix-emmc.patch
Patch241:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-fix-spi1-flash-speed.patch
Patch242:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpro64-work-led-heartbeat.patch
Patch243:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-fix-mmc-signal-voltage-before-reboot.patch
Patch245:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-unlock-temperature.patch
Patch246:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-increasing_DMA_block_memory_allocation_to_2048.patch
Patch247:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/general-rk808-configurable-switch-voltage-steps.patch
Patch248:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-sd-drive-level-8ma.patch
Patch249:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/rk3399-pci-rockchip-support-ep-gpio-undefined-case.patch
Patch250:       https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-5.11/board-rockpi4-FixMMCFreq.patch

# (tpg) Manjaro ARM Patches
Patch260:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0001-net-smsc95xx-Allow-mac-address-to-be-set-as-a-parame.patch
Patch261:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-arm64-dts-rockchip-add-usb3-node-to-roc-cc-rock64.patch
#Patch262:      https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-arm64-dts-allwinner-add-hdmi-sound-to-pine-devices.patch
Patch263:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-arm64-dts-allwinner-add-ohci-ehci-to-h5-nanopi.patch
Patch264:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0005-drm-bridge-analogix_dp-Add-enable_psr-param.patch
Patch265:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0006-gpu-drm-add-new-display-resolution-2560x1440.patch
Patch266:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0007-nuumio-panfrost-Silence-Panfrost-gem-shrinker-loggin.patch
#Patch267:      https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0008-arm64-dts-rockchip-Add-Firefly-Station-p1-support.patch
Patch268:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0009-typec-displayport-some-devices-have-pin-assignments-reversed.patch
Patch269:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0010-usb-typec-add-extcon-to-tcpm.patch
Patch270:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0011-arm64-rockchip-add-DP-ALT-rockpro64.patch
Patch271:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0012-ayufan-drm-rockchip-add-support-for-modeline-32MHz-e.patch
#Patch272:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0013-rk3399-rp64-pcie-Reimplement-rockchip-PCIe-bus-scan-delay.patch
Patch273:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0014-drm-meson-add-YUV422-output-support.patch
#Patch274:      https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0015-arm64-dts-meson-add-initial-Beelink-GT1-Ultimate-dev.patch
Patch275:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0016-add-ugoos-device.patch
Patch278:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0019-drm-panfrost-Handle-failure-in-panfrost_job_hw_submit.patch
Patch279:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0001-phy-rockchip-typec-Set-extcon-capabilities.patch
Patch280:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-usb-typec-altmodes-displayport-Add-hacky-generic-altmode.patch
Patch281:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-arm64-dts-rockchip-add-typec-extcon-hack.patch
Patch282:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-arm64-dts-rockchip-setup-USB-type-c-port-as-dual-data-role.patch
Patch283:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0001-revert-arm64-dts-allwinner-a64-Add-I2S2-node.patch
Patch284:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0002-Bluetooth-Add-new-quirk-for-broken-local-ext-features.patch
#Patch285:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0003-Bluetooth-btrtl-add-support-for-the-RTL8723CS.patch
Patch286:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0004-arm64-allwinner-a64-enable-Bluetooth-On-Pinebook.patch
#Patch287:      https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0005-arm64-dts-allwinner-enable-bluetooth-pinetab-pinepho.patch
Patch289:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0007-pinetab-accelerometer.patch
Patch290:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0008-enable-jack-detection-pinetab.patch
#Patch291:      https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0009-enable-hdmi-output-pinetab.patch
Patch292:       https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/0010-drm-panel-fix-PineTab-display.patch

# (tpg) patches taken from https://github.com/OpenMandrivaSoftware/os-image-builder/tree/master/device/rockchip/generic/kernel-patches
Patch295:	add-board-orangepi-4.patch
Patch299:	general-btsdio-ignore-uart-devs.patch
Patch300:	general-emmc-hs400es-init-tweak.patch
Patch301:	rk3399-add-sclk-i2sout-src-clock.patch

# NTFS kernel patches
# https://lore.kernel.org/lkml/20210402155347.64594-1-almaz.alexandrovich@paragon-software.com/
# (when losing track of what the latest version is, google "PATCH v26" NTFS and increase the
# version number until nothing is found -- short of always keeping track of the mailing lists,
# there doesn't seem to be a better way to always have the current version)
# Versions > 19 require kernel 5.12+
# (tpg) does not compile as of 2021-07-18
%if 0
Patch350:	PATCH-v26-01-10-fs-ntfs3-Add-headers-and-misc-files.patch
Patch351:	PATCH-v26-02-10-fs-ntfs3-Add-initialization-of-super-block.patch
Patch352:	PATCH-v26-03-10-fs-ntfs3-Add-bitmap.patch
Patch353:	PATCH-v26-04-10-fs-ntfs3-Add-file-operations-and-implementation.patch
Patch354:	PATCH-v26-05-10-fs-ntfs3-Add-attrib-operations.patch
Patch355:	PATCH-v26-06-10-fs-ntfs3-Add-compression.patch
Patch356:	PATCH-v26-07-10-fs-ntfs3-Add-NTFS-journal.patch
Patch357:	PATCH-v26-08-10-fs-ntfs3-Add-Kconfig-Makefile-and-doc.patch
Patch358:	PATCH-v26-09-10-fs-ntfs3-Add-NTFS3-in-fs-Kconfig-and-fs-Makefile.patch
Patch359:	PATCH-v26-10-10-fs-ntfs3-Add-MAINTAINERS.patch
%endif

# Bootsplash support
# based on https://gitlab.manjaro.org/packages/core/linux511/-/tree/master
Patch401:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0401-revert-fbcon-remove-now-unusued-softback_lines-cursor-argument.patch
Patch402:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0402-revert-fbcon-remove-no-op-fbcon_set_origin.patch
Patch403:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0403-revert-fbcon-remove-soft-scrollback-code.patch
Patch501:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0501-bootsplash.patch
Patch502:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0502-bootsplash.patch
Patch503:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0503-bootsplash.patch
Patch504:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0504-bootsplash.patch
Patch505:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0505-bootsplash.patch
Patch506:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0506-bootsplash.patch
Patch507:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0507-bootsplash.patch
Patch508:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0508-bootsplash.patch
Patch509:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0509-bootsplash.patch
Patch510:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0510-bootsplash.patch
Patch511:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0511-bootsplash.patch
Patch512:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0512-bootsplash.patch
Source513:	https://gitlab.manjaro.org/packages/core/linux511/-/raw/master/0513-bootsplash.gitpatch

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
Patch905:	0106-intel_idle-tweak-cpuidle-cstates.patch
Patch907:	0108-smpboot-reuse-timer-calibration.patch
Patch908:	0109-initialize-ata-before-graphics.patch
Patch909:	0110-give-rdrand-some-credit.patch
Patch910:	0111-ipv4-tcp-allow-the-memory-tuning-for-tcp-to-go-a-lit.patch
Patch913:	0117-migrate-some-systemd-defaults-to-the-kernel-defaults.patch
Patch914:	0120-use-lfence-instead-of-rep-and-nop.patch
%endif

# Defines for the things that are needed for all the kernels
#
%define common_desc_kernel The kernel package contains the Linux kernel (vmlinuz), the core of your \
OpenMandriva Lx operating system. The kernel handles the basic functions \
of the operating system: memory allocation, process allocation, device \
input and output, etc. \
This version is a preview of an upcoming kernel version, and may be helpful if you are using \
very current hardware.

### Global Requires/Provides
# do not require dracut, please it bloats dockers and other minimal instllations
# better solution needs to be figured out
# (crazy) it needs dracut >= 050-4 bc ZSTD support
%ifnarch %{armx} %{riscv}
%define requires2	dracut >= 050-4
%endif
# (crazy) it needs kmod >= 27-3 bc ZSTD support
%define requires3	kmod >= 27-3
%define requires4	sysfsutils >=  2.1.0-12
%define requires5	kernel-firmware

%define kprovides1	%{kname} = %{kverrel}
%define kprovides2	kernel = %{tar_ver}
%define kprovides_server	drbd-api = 88

%define kobsoletes1	dkms-r8192se <= 0019.1207.2010-2
%define kobsoletes2	dkms-lzma <= 4.43-32
%define kobsoletes3	dkms-psb <= 4.41.1-7

## FIXME
%define kconflicts1	dkms-broadcom-wl < 5.100.82.112-12
%define kconflicts2	dkms-fglrx < 13.200.5-1
%define kconflicts3	dkms-nvidia-current < 325.15-1
%define kconflicts4	dkms-nvidia-long-lived < 319.49-1
%define kconflicts5	dkms-nvidia304 < 304.108-1

Autoreqprov:	no
BuildRequires:	zstd
BuildRequires:	findutils
BuildRequires:	bc
BuildRequires:	flex
BuildRequires:	bison
BuildRequires:	binutils
BuildRequires:	hostname
%if %{with clang}
BuildRequires:	clang
BuildRequires:	llvm
BuildRequires:	lld
%endif
%if %{with gcc}
BuildRequires:	gcc
BuildRequires:	gcc-c++
%endif
BuildRequires:  pkgconfig(libcap)
BuildRequires:	pkgconfig(libssl)
BuildRequires:	diffutils
# For git apply
BuildRequires:	git-core
# For power tools
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libkmod)

%ifarch %{x86_64} %{aarch64}
BuildRequires:	pkgconfig(numa)
%endif

# for cpupower
%if %{with build_cpupower}
BuildRequires:	pkgconfig(libpci)
%endif

%if %{with build_turbostat}
BuildRequires:  pkgconfig(libpcap)
%endif

# for docs
%if %{with build_doc}
BuildRequires:	xmlto
%endif

# for ORC unwinder and perf
BuildRequires:	pkgconfig(libelf)

# for bpf
BuildRequires:	pahole

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
BuildRequires:	pkgconfig(python)
BuildRequires:	pkgconfig(zlib)
BuildRequires:	pkgconfig(babeltrace)
BuildRequires:	jdk-current
BuildRequires:	perl-devel
BuildRequires:	perl(ExtUtils::Embed)
%endif

%ifarch %{arm}
BuildRequires:	uboot-mkimage
%endif

%ifnarch %{armx} %{riscv}
# might be useful too:
Suggests:	microcode-intel
%endif

# Let's pull in some of the most commonly used DKMS modules
# so end users don't have to install compilers (and worse,
# get compiler error messages on failures)
%ifarch %{x86_64}
BuildRequires:	virtualbox-kernel-module-sources >= 6.1.10
%if %{with vbox_orig_mods}
BuildRequires:	virtualbox-guest-kernel-module-sources >= 6.1.10
%endif
%endif

%description
%common_desc_kernel

# Define obsolete/provides to help automatic upgrades of old kernel-xen-pvops
%define latest_obsoletes_server kernel-xen-pvops-latest < 3.2.1-1
%define latest_provides_server kernel-xen-pvops-latest = %{kverrel}
%define latest_obsoletes_devel_server kernel-xen-pvops-devel-latest < 3.2.1-1
%define latest_provides_devel_server kernel-xen-pvops-devel-latest = %{kverrel}

# mkflavour() name flavour processor
# name: the flavour name in the package name
# flavour: first parameter of CreateKernel()
%define mkflavour()					\
%package -n %{kname}-%{1}				\
Version:	%{kversion}				\
Release:	%{rpmrel}				\
Provides:	%kprovides1 %kprovides2			\
%{expand:%%{?kprovides_%{1}:Provides: %{kprovides_%{1}}}} \
Provides:	%{kname}-%{1}-%{buildrel}		\
Requires(pre):	%requires3 %requires4			\
Requires:	%requires5				\
Obsoletes:	%kobsoletes1 %kobsoletes2 %kobsoletes3	\
Conflicts:	%kconflicts1 %kconflicts2 %kconflicts3	\
Conflicts:	%kconflicts4 %kconflicts5 \
Conflicts:	%{kname}-%{1}-latest <= %{kversion}-%{rpmrel}	\
Obsoletes:	%{kname}-%{1}-latest <= %{kversion}-%{rpmrel}	\
Provides:	installonlypkg(kernel)			\
Provides:	should-restart = system			\
Recommends:	iw					\
%ifarch %{ix86} %{x86_64}				\
Requires:	grub2 >= 2.02-27			\
Requires(post):	grub2 >= 2.02-27			\
%endif							\
%ifnarch %armx						\
Recommends:	cpupower				\
Recommends:	microcode-intel				\
Suggests:	dracut >= 047				\
%endif							\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
Summary:	%{expand:%{summary_%(echo %{1} | sed -e "s/-/_/")}} \
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}				\
%common_desc_kernel %{expand:%{info_%(echo %{1} | sed -e "s/-/_/")}} \
							\
%if %{with build_devel}					\
%package -n	%{kname}-%{1}-devel			\
Version:	%{kversion}				\
Release:	%{rpmrel}				\
Requires:	glibc-devel				\
Requires:	ncurses-devel				\
Requires:	make					\
%ifarch %{x86_64}					\
Requires:	pkgconfig(libelf)			\
%endif							\
Summary:	The kernel-devel files for %{kname}-%{1}-%{buildrel} \
Group:		Development/Kernel			\
Provides:	kernel-devel = %{kverrel}		\
Provides:	%{kname}-devel = %{kverrel} 		\
Provides:	%{kname}-%{1}-devel-%{buildrel}		\
Conflicts:	%{kname}-%{1}-devel-latest <= %{kversion}-%{rpmrel} \
Obsoletes:	%{kname}-%{1}-devel-latest <= %{kversion}-%{rpmrel} \
Provides:	installonlypkg(kernel)			\
Requires:	%{kname}-%{1} = %{kversion}-%{rpmrel}	\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
%description -n %{kname}-%{1}-devel			\
This package contains the kernel files (headers and build tools) \
that should be enough to build additional drivers for   \
use with %{kname}-%{1}-%{buildrel}.			\
							\
If you want to build your own kernel, you need to install the full \
%{kname}-source-%{buildrel} rpm.			\
							\
%endif							\
							\
%if %{with build_debug}					\
%package -n	%{kname}-%{1}-debuginfo			\
Version:	%{kversion}				\
Release:	%{rpmrel}				\
Summary:	Files with debuginfo for %{kname}-%{1}-%{buildrel} \
Group:		Development/Debug			\
Provides:	kernel-debug = %{kverrel} 		\
Provides:	kernel-%{1}-%{buildrel}-debuginfo	\
Provides:	installonlypkg(kernel)			\
Requires:	%{kname}-%{1} = %{kversion}-%{rpmrel}	\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
%description -n %{kname}-%{1}-debuginfo			\
This package contains the files with debuginfo to aid in debug tasks \
when using %{kname}-%{1}-%{buildrel}.			\
							\
If you need to look at debug information or use some application that \
needs debugging info from the kernel, this package may help. \
							\
%endif							\
							\
%post -n %{kname}-%{1} -f kernel_files.%{1}-post 	\
%posttrans -n %{kname}-%{1} -f kernel_files.%{1}-posttrans \
%postun -n %{kname}-%{1} -f kernel_files.%{1}-postun 	\
							\
%if %{with build_devel}					\
%post -n %{kname}-%{1}-devel -f kernel_devel_files.%{1}-post \
%preun -n %{kname}-%{1}-devel -f kernel_devel_files.%{1}-preun \
%postun -n %{kname}-%{1}-devel -f kernel_devel_files.%{1}-postun \
%endif							\
							\
%files -n %{kname}-%{1} -f kernel_files.%{1} 		\
							\
%package -n %{kname}-%{1}-modules-appletalk		\
Summary:	AppleTalk modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-appletalk		\
AppleTalk modules for kernel %{kname}-%{1}		\
AppleTalk is an obsolete protocol for networking Apple	\
devices. If you don't know what this is, you don't	\
need it.						\
%files -n %{kname}-%{1}-modules-appletalk		\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/net/appletalk \
							\
%ifnarch %{armx}					\
%package -n %{kname}-%{1}-modules-arcnet		\
Summary:	ARCNET modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-arcnet		\
ARCNET modules for kernel %{kname}-%{1}			\
ARCNET is an obsolete networking protocol.		\
If you don't know what this is, you don't need it.	\
%files -n %{kname}-%{1}-modules-arcnet			\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/drivers/net/arcnet \
%endif							\
							\
%package -n %{kname}-%{1}-modules-decnet		\
Summary:	DECnet modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-decnet		\
DECnet modules for kernel %{kname}-%{1}			\
DECnet is an obsolete networking protocol.		\
If you don't know what this is, you don't need it.	\
%files -n %{kname}-%{1}-modules-decnet			\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/net/decnet \
							\
%package -n %{kname}-%{1}-modules-fddi			\
Summary:	FDDI modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-fddi		\
FDDI modules for kernel %{kname}-%{1}			\
FDDI is an obsolete networking protocol.		\
If you don't know what this is, you don't need it.	\
%files -n %{kname}-%{1}-modules-fddi			\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/drivers/net/fddi \
							\
%ifnarch %{armx}					\
%package -n %{kname}-%{1}-modules-infiniband		\
Summary:	Infiniband modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-infiniband	\
Infiniband modules for kernel %{kname}-%{1}		\
Infiniband is an alternative to Ethernet commonly used	\
for communication between supercomputers. If you don't	\
know what it is, you don't need it.			\
%files -n %{kname}-%{1}-modules-infiniband		\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/drivers/infiniband \
							\
%package -n %{kname}-%{1}-modules-isdn			\
Summary:	ISDN modules for kernel %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-modules-isdn		\
ISDN modules for kernel %{kname}-%{1}			\
ISDN (also known as RNIS in France) is an obsolete-ish	\
telephony network interface. If you don't know what it	\
is, you don't need it.					\
%files -n %{kname}-%{1}-modules-isdn			\
%{_modulesdir}/%{kversion}-%{1}-%{buildrpmrel}/kernel/drivers/isdn \
%endif							\
							\
%if %{with build_devel}					\
%files -n %{kname}-%{1}-devel -f kernel_devel_files.%{1} \
%endif							\
							\
%if %{with build_debug}					\
%files -n %{kname}-%{1}-debuginfo -f kernel_debug_files.%{1} \
%endif

# kernel-desktop: i686, smp-alternatives, 4 GB / x86_64
#
%if %{with build_desktop}
%ifarch %{ix86}
%define summary_desktop Linux Kernel for desktop use with i686 & 4GB RAM
%define summary_desktop_clang Clang-built Linux Kernel for desktop use with i686 & 4GB RAM
%define info_desktop This kernel is compiled for desktop use, single or \
multiple i686 processor(s)/core(s) and less than 4GB RAM, using HZ_1000, \
voluntary preempt, CFS cpu scheduler and BFQ i/o scheduler.
%else
%define summary_desktop Linux Kernel for desktop use with %{_arch}
%define summary_desktop_clang Clang-built Linux Kernel for desktop use with %{_arch}
%define info_desktop This kernel is compiled for desktop use, single or \
multiple %{_arch} processor(s)/core(s), using HZ_1000, \
voluntary preempt, CFS cpu scheduler and BFQ i/o scheduler, ONDEMAND governor.
%endif
%if %{with gcc}
%mkflavour desktop
%endif
%if %{with clang}
%mkflavour desktop-clang
%endif
%endif


%if %{with build_server}
%ifarch %{ix86}
%define summary_server Linux Kernel for server use with i686 & 64GB RAM
%define summary_server_clang Clang-built Linux Kernel for server use with i686 & 64GB RAM
%define info_server This kernel is compiled for server use, single or \
multiple i686 processor(s)/core(s) and up to 64GB RAM using PAE, using \
no preempt, HZ_300, CFS cpu scheduler and BFQ i/o scheduler, PERFORMANCE governor.
%else
%define summary_server Linux Kernel for server use with %{_arch}
%define summary_server_clang Clang-built Linux Kernel for server use with %{_arch}
%define info_server This kernel is compiled for server use, single or \
CFS cpu scheduler and BFQ i/o scheduler, PERFORMANCE governor.
%endif
%if %{with gcc}
%mkflavour server
%endif
%if %{with clang}
%mkflavour server-clang
%endif
%endif

#
# kernel-source
#
%if %{with build_source}
%package -n %{kname}-source
Version:	%{kversion}
Release:	%{rpmrel}
Requires:	glibc-devel
Requires:	ncurses-devel
Requires:	make
Requires:	gcc >= 7.2.1_2017.11-3
Requires:	perl
Requires:	diffutils
Summary:	The Linux source code for %{kname}-%{buildrel}
Group:		Development/Kernel
Autoreqprov:	no
Provides:	kernel-source = %{kverrel}
Provides:	kernel-source-%{buildrel}
Provides:	installonlypkg(kernel)
Conflicts:	%{kname}-source-latest <= %{kversion}-%{rpmrel}
Obsoletes:	%{kname}-source-latest <= %{kversion}-%{rpmrel}
Buildarch:	noarch

%description -n %{kname}-source
The %{kname}-source package contains the source code files for the OpenMandriva
kernel. These source files are only needed if you want to build your own
custom kernel that is better tuned to your particular hardware.

If you only want the files needed to build 3rdparty (nVidia, Ati, dkms-*,...)
drivers against, install the *-devel rpm that is matching your kernel.
%endif

#
# kernel-doc: documentation for the Linux kernel
#
%if %with build_doc
%package -n %{kname}-doc
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Various documentation bits found in the %{kname} source
Group:		Documentation
Buildarch:	noarch

%description -n %{kname}-doc
This package contains documentation files from the %{kname} source.
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
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	perf tool and the supporting documentation
Group:		System/Kernel and hardware

%description -n perf
the perf tool and the supporting documentation.
%endif

%if %{with build_cpupower}
%package -n cpupower
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	The cpupower tools
Group:		System/Kernel and hardware
Requires(post):		rpm-helper >= 0.24.0-3
Requires(preun):	rpm-helper >= 0.24.0-3
Obsoletes:	cpufreq < 2.0-3
Provides:	cpufreq = 2.0-3
Obsoletes:	cpufrequtils < 008-6
Provides:	cpufrequtils = 008-6

%description -n cpupower
The cpupower tools.

%package -n cpupower-devel
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Devel files for cpupower
Group:		Development/Kernel
Requires:	cpupower = %{kversion}-%{rpmrel}
Conflicts:	%{_lib}cpufreq-devel

%description -n cpupower-devel
This package contains the development files for cpupower.
%endif

%if %{with build_x86_energy_perf_policy}
%package -n x86_energy_perf_policy
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Tool to control energy vs. performance on recent X86 processors
Group:		System/Kernel and hardware

%description -n x86_energy_perf_policy
Tool to control energy vs. performance on recent X86 processors.
%endif

%if %{with build_turbostat}
%package -n turbostat
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Tool to report processor frequency and idle statistics
Group:		System/Kernel and hardware

%description -n turbostat
Tool to report processor frequency and idle statistics.
%endif

%define bpf_major 0
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

%package headers
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Linux kernel header files mostly used by your C library
Group:		System/Kernel and hardware
Epoch:		1
# (tpg) fix bug https://issues.openmandriva.org/show_bug.cgi?id=1580
Provides:	kernel-headers = 1:%{kverrel}
Obsoletes:	kernel-headers < 1:%{kverrel}
%rename linux-userspace-headers

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
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Linux kernel header files for ${i} cross toolchains
Group:		System/Kernel and hardware
BuildArch:	noarch
%if "%{name}" != "kernel"
Provides:	cross-${i}-kernel-headers = %{EVRD}
%endif

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

%setup -q -n linux-%{tar_ver} -a 1003 -a 1004
%if 0%{sublevel}
[ -e .git ] || git init
xzcat %{SOURCE1000} |git apply - || git apply %{SOURCE1000}
rm -rf .git
%endif
%autopatch -p1
git apply %{S:513}

%ifarch %{aarch64}
# FIXME SynQuacer workaround
#patch -p1 -b -z .1002~ <%{S:1002}
#patch -p1 -b -z .1001~ <%{S:1001}
%endif

%if %{with saa716x}
# merge SAA716x DVB driver from extra tarball
sed -i -e '/saa7164/isource "drivers/media/pci/saa716x/Kconfig"' drivers/media/pci/Kconfig
sed -i -e '/saa7164/iobj-$(CONFIG_SAA716X_CORE) += saa716x/' drivers/media/pci/Makefile
find drivers/media/tuners drivers/media/dvb-frontends -name "*.c" -o -name "*.h" |xargs sed -i -e 's,"dvb_frontend.h",<media/dvb_frontend.h>,g'
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

%if %{with build_debug}
%define debug --debug
%else
%define debug --no-debug
%endif

# make sure the kernel has the sublevel we know it has...
LC_ALL=C sed -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{sublevel}/" Makefile

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
patch -p1 -z .1006~ -b <%{S:1006}
patch -p1 -z .1007~ -b <%{S:1007}
%endif

# get rid of unwanted files
find . -name '*~' -o -name '*.orig' -o -name '*.append' -delete
# wipe all .gitignore/.get_maintainer.ignore files
find . -name "*.g*ignore" -delete

# fix missing exec flag on file introduced in 4.14.10-rc1
chmod 755 tools/objtool/sync-check.sh

%build
%set_build_flags

############################################################
###  Linker end2 > Check point to build for omv ###
############################################################
CheckConfig() {

	if [ ! -e $(pwd)/.config ]; then
		printf '%s\n' "Kernel config in $(pwd) missing, killing the build."
		exit 1
	fi
}

VerifyConfig() {
# (tpg) please add CONFIG that were carelessly enabled, while it is known these MUST be disabled
    if grep -Fxq "CONFIG_RT_GROUP_SCHED=y" .config kernel/configs/omv-*config; then
	printf '%s\n' "Please stop enabling CONFIG_RT_GROUP_SCHED - this option is not recommended with systemd systemd/systemd#553, killing the build."
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
CONFIG_LTO_CLANG_FULL=y
# CONFIG_LTO_CLANG_THIN is not set
EOF
}

CreateConfig() {
	arch="$1"
	type="$2"
	config_dir=%{_sourcedir}
	CONFIGS=""
	rm -fv .config


	if echo $type |grep -q clang; then
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

	# (crazy) do not use %{S:X} to copy, if someone messes up we end up with broken stuff again
	case ${arch} in
	i?86)
		case ${type} in
		desktop|desktop-clang)
			rm -rf .config
			cp -v ${config_dir}/i686-desktop-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		server|server-clang)
			rm -rf .config
			cp -v ${config_dir}/i686-server-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	x86_64|x86)
		case ${type} in
		desktop|desktop-clang)
			rm -rf .config
			cp -v ${config_dir}/x86_64-desktop-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		server|server-clang)
			rm -rf .config
			cp -v ${config_dir}/x86_64-server-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	arm)
		case ${type} in
		desktop|desktop-clang)
			rm -rf .config
			cp -v ${config_dir}/armv7hnl-desktop-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		server|server-clang)
			rm -rf .config
			cp -v ${config_dir}/armv7hnl-desktop-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	arm64)
		case ${type} in
		desktop|desktop-clang)
			rm -rf .config
			cp -v ${config_dir}/aarch64-desktop-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		server|server-clang)
			rm -rf .config
			cp -v ${config_dir}/aarch64-server-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		*)
			printf '%s\n' "ERROR: no such type ${type} for ${arch}"
			exit 1
			;;
		esac
		;;
	znver1)
		case ${type} in
		desktop|desktop-clang)
			rm -rf .config
			cp -v ${config_dir}/x86_64-znver-desktop-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
			;;
		server|server-clang)
			rm -rf .config
			cp -v ${config_dir}/x86_64-znver-server-gcc-omv-defconfig .config
			echo ${type} |grep -q clang && clangify .config
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
	if [[ -n ${CONFIGS} ]]; then
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
	if [[ -n ${CONFIGS} ]]; then
		make ARCH="${arch}" CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" V=1 $CONFIGS
	else
		%if %{without lazy_developer}
		## YES, intentionally, DIE on wrong config
		CheckConfig
		make ARCH="${arch}" CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" V=1 oldconfig
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
	printf '%s\n' "Make config for kernel $extension"
	VerifyConfig
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
	printf '%s\n' "Building kernel $KernelVer"

	if echo $1 |grep -q clang; then
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

	TARGETS=all
%ifarch %{aarch64}
	TARGETS="$TARGETS dtbs"
%endif
	%make_build ARCH=%{target_arch} CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" $TARGETS

	# Start installing stuff
	install -d %{temp_boot}
	install -m 644 System.map %{temp_boot}/System.map-$KernelVer
	install -m 644 .config %{temp_boot}/config-$KernelVer


%ifarch %{arm}
	if [ -f arch/arm/boot/uImage ]; then
		cp -f arch/arm/boot/uImage %{temp_boot}/uImage-$KernelVer
	else
		cp -f arch/arm/boot/zImage %{temp_boot}/vmlinuz-$KernelVer
	fi
%else
%ifarch %{aarch64}
	cp -f arch/arm64/boot/Image.gz %{temp_boot}/vmlinuz-$KernelVer
%else
	cp -f arch/%{target_arch}/boot/bzImage %{temp_boot}/vmlinuz-$KernelVer
%endif
%endif

	# modules
	install -d %{temp_modules}/$KernelVer
	%make_build INSTALL_MOD_PATH=%{temp_root} ARCH=%{target_arch} SRCARCH=%{target_arch} KERNELRELEASE=$KernelVer CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" INSTALL_MOD_STRIP=1 modules_install

	# headers
	%make_build INSTALL_HDR_PATH=%{temp_root}%{_prefix} KERNELRELEASE=$KernelVer ARCH=%{target_arch} SRCARCH=%{target_arch} headers_install

%ifarch %{armx} %{ppc}
	%make_build ARCH=%{target_arch} CC="$CC" HOSTCC="$CC" CXX="$CXX" HOSTCXX="$CXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" INSTALL_DTBS_PATH=%{temp_boot}/dtb-$KernelVer dtbs_install
%endif

	# remove /lib/firmware, we use a separate kernel-firmware
	rm -rf %{temp_root}/lib/firmware
}

SaveDevel() {
	devel_flavour=$1

	DevelRoot=/usr/src/linux-%{kversion}-$devel_flavour-%{buildrpmrel}
	TempDevelRoot=%{temp_root}$DevelRoot

	mkdir -p $TempDevelRoot
	for i in $(find . -name 'Makefile*'); do cp -R --parents $i $TempDevelRoot;done
	for i in $(find . -name 'Kconfig*' -o -name 'Kbuild*'); do cp -R --parents $i $TempDevelRoot;done
	cp -fR include $TempDevelRoot
	# ln -s ../generated/uapi/linux/version.h $TempDevelRoot/include/linux/version.h
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

	for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
		 mips mn10300 nds32 nios2 openrisc parisc s390 score sh sparc tile unicore32 xtensa; do
		rm -rf $TempDevelRoot/arch/$i
	done

	# Clean the scripts tree, and make sure everything is ok (sanity check)
	# running prepare+scripts (tree was already "prepared" in build)
	cd $TempDevelRoot >/dev/null
	%make_build ARCH=%{target_arch} clean
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
$DevelRoot/include/scsi
$DevelRoot/include/soc
$DevelRoot/include/sound
$DevelRoot/include/target
$DevelRoot/include/trace
$DevelRoot/include/uapi
$DevelRoot/include/vdso
$DevelRoot/include/video
$DevelRoot/include/xen
$DevelRoot/init
$DevelRoot/ipc
$DevelRoot/kernel
$DevelRoot/lib
$DevelRoot/mm
$DevelRoot/net
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
if [ -d /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel} ]; then
	rm -f /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/{build,source}
	ln -sf $DevelRoot /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/build
	ln -sf $DevelRoot /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/source
fi
EOF


	### Create -devel Preun script on the fly
	cat > $kernel_devel_files-preun <<EOF
if [ -L /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/build ]; then
	rm -f /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/build
fi
if [ -L /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/source ]; then
	rm -f /lib/modules/%{kversion}-$devel_flavour-%{buildrpmrel}/source
fi
exit 0
EOF

	### Create -devel Postun script on the fly
	cat > $kernel_devel_files-postun <<EOF
rm -rf /usr/src/linux-%{kversion}-$devel_flavour-%{buildrpmrel} >/dev/null
EOF
}

SaveDebug() {
	debug_flavour=$1

	install -m 644 vmlinux %{temp_boot}/vmlinux-%{kversion}-$debug_flavour-%{buildrpmrel}
	kernel_debug_files=../kernel_debug_files.$debug_flavour
	echo "%{_bootdir}/vmlinux-%{kversion}-$debug_flavour-%{buildrpmrel}" >> $kernel_debug_files

	find %{temp_modules}/%{kversion}-$debug_flavour-%{buildrpmrel}/kernel -name "*.ko" | %kxargs -I '{}' objcopy --only-keep-debug '{}' '{}'.debug
	find %{temp_modules}/%{kversion}-$debug_flavour-%{buildrpmrel}/kernel -name "*.ko" | %kxargs -I '{}' sh -c 'cd $(dirname {}); objcopy --add-gnu-debuglink=$(basename {}).debug --strip-debug $(basename {})'

	cd %{temp_modules}
	find %{kversion}-$debug_flavour-%{buildrpmrel}/kernel -name "*.ko.debug" > debug_module_list
	cd -
	cat %{temp_modules}/debug_module_list | sed 's|\(.*\)|%{_modulesdir}/\1|' >> $kernel_debug_files
	cat %{temp_modules}/debug_module_list | sed 's|\(.*\)|%exclude %{_modulesdir}/\1|' >> ../kernel_exclude_debug_files.$debug_flavour
	rm -f %{temp_modules}/debug_module_list
}

CreateFiles() {
	kernel_flavour=$1
	kernel_files=kernel_files.$kernel_flavour

	ker="vmlinuz"
	### Create the kernel_files.*
	cat > $kernel_files <<EOF
%{_bootdir}/System.map-%{kversion}-$kernel_flavour-%{buildrpmrel}
%{_bootdir}/config-%{kversion}-$kernel_flavour-%{buildrpmrel}
%{_bootdir}/$ker-%{kversion}-$kernel_flavour-%{buildrpmrel}
%dir %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/
%{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/net/appletalk
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/net/decnet
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/drivers/infiniband
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/drivers/isdn
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/drivers/net/arcnet
%exclude %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel/drivers/net/fddi
%{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/modules.*
# device tree binary
%ifarch %{armx}
%{_bootdir}/dtb-%{kversion}-$kernel_flavour-%{buildrpmrel}
%endif
EOF

%if %{with build_debug}
	cat kernel_exclude_debug_files.$kernel_flavour >> $kernel_files
%endif

### Create kernel Post script
	cat > $kernel_files-post <<EOF
%ifnarch %{armx} %{riscv}
%if %{with dracut_all_initrd}
[ -x /sbin/dracut ] && /sbin/dracut -f --regenerate-all
%endif

/sbin/depmod -a %{kversion}-$kernel_flavour-%{buildrpmrel}
[ -x /sbin/dracut ] && /sbin/dracut -f --kver %{kversion}-$kernel_flavour-%{buildrpmrel}
%endif

## cleanup some werid symlinks we never used anyway
rm -rf vmlinuz-{server,desktop} initrd0.img initrd-{server,desktop}

# run update-grub2
[ -x /usr/sbin/update-grub2 ] && /usr/sbin/update-grub2

cd - > /dev/null
%if %{with build_devel}
# create kernel-devel symlinks if matching -devel- rpm is installed
if [ -d /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
	rm -f /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/{build,source}
	ln -sf /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/build
	ln -sf /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/source
fi
%endif
EOF

	### Create kernel Posttrans script
	cat > $kernel_files-posttrans <<EOF
if [ -x /usr/sbin/dkms_autoinstaller ] && [ -d /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
	/usr/sbin/dkms_autoinstaller start %{kversion}-$kernel_flavour-%{buildrpmrel}
fi

if [ -x %{_sbindir}/dkms ] && [ -e %{_unitdir}/dkms.service ] && [ -d /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
	/bin/systemctl --quiet restart dkms.service
	/bin/systemctl --quiet try-restart loadmodules.service
	%{_sbindir}/dkms autoinstall --verbose --kernelver %{kversion}-$kernel_flavour-%{buildrpmrel}
fi
EOF

### Create kernel Postun script on the fly
cat > $kernel_files-postun <<EOF

rm -rf /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/modules.{alias{,.bin},builtin.bin,dep{,.bin},devname,softdep,symbols{,.bin}} ||:
cd /boot > /dev/null

if [ -e vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
	rm -rf vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel}
fi

if [ -e initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img ]; then
	rm -rf initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img
fi


cd - > /dev/null

rm -rf /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel} >/dev/null
if [ -d /var/lib/dkms ]; then
	rm -f /var/lib/dkms/*/kernel-%{kversion}-$devel_flavour-%{buildrpmrel}-%{_target_cpu} >/dev/null
	rm -rf /var/lib/dkms/*/*/%{kversion}-$devel_flavour-%{buildrpmrel} >/dev/null
	rm -f /var/lib/dkms-binary/*/kernel-%{kversion}-$devel_flavour-%{buildrpmrel}-%{_target_cpu} >/dev/null
	rm -rf /var/lib/dkms-binary/*/*/%{kversion}-$devel_flavour-%{buildrpmrel} >/dev/null
fi

%if %{with build_devel}
if [ -L /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/build ]; then
	rm -f /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/build
fi
if [ -L /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/source ]; then
	rm -f /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel}/source
fi
%endif
exit 0
EOF
}

CreateKernel() {
	flavour=$1

	PrepareKernel $flavour $flavour-%{buildrpmrel}

	BuildKernel %{kversion}-$flavour-%{buildrpmrel}
%if %{with build_devel}
	SaveDevel $flavour
%endif
%if %{with build_debug}
	SaveDebug $flavour
%endif
	CreateFiles $flavour
}

# Create a simulacro of buildroot
rm -rf %{temp_root}
install -d %{temp_root}

###
# DO it...
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
				%make_build ARCH=${a} SRCARCH=${SARCH}  INSTALL_HDR_PATH=%{temp_root}%{_prefix}/${i} headers_install
			done
		fi
%endif
	done
done
unset ARCH
make mrproper

%if %{with build_desktop}
%if %{with clang}
CreateKernel desktop-clang
%endif
%if %{with gcc}
CreateKernel desktop
%endif
%endif

%if %{with build_server}
%if %{with clang}
CreateKernel server-clang
%endif
%if %{with gcc}
CreateKernel server
%endif
%endif

# how to build own flavour
# if %build_nrjQL_desktop
# CreateKernel nrjQL-desktop
# endif

# set extraversion to match srpm to get nice version reported by the tools
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{rpmrel}|" Makefile

############################################################
### Linker start3 > Check point to build for omv         ###
############################################################

# We install all tools here too (rather than in %%install
# where it really belongs): make mrproper in preparation
# for packaging kernel-source would force a rebuilda

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
%make_build -C tools/lib/bpf CC=clang LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd libbpf.a libbpf.pc libbpf.so -j1
%make_build -C tools/bpf/bpftool CC=clang LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd bpftool -j1
%make_install -C tools/lib/bpf install_headers DESTDIR=%{temp_root} prefix=%{_prefix} libdir=%{_libdir} CC=clang CXX=clang++ LD=ld.bfd HOSTLD=ld.bfd
%make_install -C tools/bpf/bpftool CC=clang CXX=clang++ LD=ld.bfd HOSTCC=clang HOSTLD=ld.bfd DESTDIR=%{temp_root} prefix=%{_prefix} bash_compdir=%{_sysconfdir}/bash_completion.d/ mandir=%{_mandir}
%endif

%if %{with perf}
[ -e %{_sysconfdir}/profile.d/90java.sh ] && . %{_sysconfdir}/profile.d/90java.sh
%make_build -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.bfd HOSTLD=ld.bfd WERROR=0 prefix=%{_prefix} all man
%make_build -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.bfd HOSTLD=ld.bfd WERROR=0 prefix=%{_prefix} DESTDIR_SQ=%{temp_root} DESTDIR=%{temp_root} install install-man
%endif

############################################################
###  Linker end3 > Check point to build for omv          ###
############################################################

# We don't make to repeat the depend code at the install phase
%if %{with build_source}
PrepareKernel "" %{buildrpmrel}custom
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

# sniff, if we compressed all the modules, we change the stamp :(
# we really need the depmod -ae here
pushd %{target_modules}
for i in *; do
    /sbin/depmod -ae -b %{buildroot} -F %{target_boot}/System.map-"$i" "$i"
    echo $?
done

for i in *; do
    pushd $i
    printf '%s\n' "Creating modules.description for $i"
    modules=$(find . -name "*.ko.[gxz]*[z|st]")
    echo $modules | %kxargs /sbin/modinfo | perl -lne 'print "$name\t$1" if $name && /^description:\s*(.*)/; $name = $1 if m!^filename:\s*(.*)\.k?o!; $name =~ s!.*/!!' > modules.description
    popd
done
popd

# need to set extraversion to match srpm again to avoid rebuild
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{rpmrel}|" Makefile

############################################################
### Linker start4 > Check point to build for omv         ###
############################################################
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
for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
	mips nds32 nios2 openrisc parisc s390 score sh sh64 sparc tile unicore32 v850 xtensa mn10300; do
	rm -rf %{target_source}/arch/$i
done

# other misc files
rm -f %{target_source}/{.config.old,.config.cmd,.gitignore,.lst,.mailmap,.gitattributes}
rm -f %{target_source}/{.missing-syscalls.d,arch/.gitignore,firmware/.gitignore}
rm -rf %{target_source}/.tmp_depmod/
rm -rf %{buildroot}/usr/src/linux-*/uksm.txt

# more cleaning
rm -f %{target_source}/arch/x86_64/boot/bzImage
cd %{target_source}
# lots of gitignore files
find -iname ".gitignore" -delete
# clean tools tree
%make_build -C tools clean -j1
%make_build -C tools/build clean -j1
%make_build -C tools/build/feature clean -j1
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


############################################################
### Linker start4 > Check point to build for omv         ###
############################################################

%if %{with build_source}
%files -n %{kname}-source
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
%{_kerneldir}/include/scsi
%{_kerneldir}/include/soc
%{_kerneldir}/include/sound
%{_kerneldir}/include/target
%{_kerneldir}/include/trace
%{_kerneldir}/include/uapi
%{_kerneldir}/include/vdso
%{_kerneldir}/include/video
%{_kerneldir}/include/xen
%{_kerneldir}/init
%{_kerneldir}/ipc
%{_kerneldir}/kernel
%{_kerneldir}/lib
%{_kerneldir}/mm
%{_kerneldir}/net
%{_kerneldir}/virt
%{_kerneldir}/samples
%{_kerneldir}/scripts
%{_kerneldir}/security
%{_kerneldir}/sound
%{_kerneldir}/tools
%{_kerneldir}/usr
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
%files -n %{kname}-doc
%doc Documentation/*
%endif

%if %{with perf}
%files -n perf
%{_bindir}/perf
%ifarch %{x86_64}
%{_bindir}/perf-read-vdso32
%endif
%{_bindir}/trace
%ifarch %{x86_64}
%dir %{_libdir}/traceevent
%dir %{_libdir}/traceevent/plugins
%{_libdir}/traceevent/plugins/plugin_*
%else
%dir %{_prefix}/lib/traceevent
%dir %{_prefix}/lib/traceevent/plugins
%{_prefix}/lib/traceevent/plugins/plugin_*
%endif
%dir %{_prefix}/libexec/perf-core
%{_prefix}/libexec/perf-core/*
%{_mandir}/man[1-8]/perf*
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
%{_mandir}/man[1-8]/cpupower*
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
%{_mandir}/man8/x86_energy_perf_policy.8*
%endif

%if %{with build_turbostat}
%files -n turbostat
%{_bindir}/turbostat
%{_mandir}/man8/turbostat.8*
%endif
%endif

%if %{with bpftool}
%files -n bpftool
%{_sbindir}/bpftool
%{_sysconfdir}/bash_completion.d/bpftool

%files -n %{libbpf}
%{_libdir}/libbpf.so.%{bpf_major}*

%files -n %{libbpfdevel}
%{_libdir}/libbpf.so
%{_libdir}/pkgconfig/*.pc
%dir %{_includedir}/bpf
%{_includedir}/bpf/*.h
%endif
