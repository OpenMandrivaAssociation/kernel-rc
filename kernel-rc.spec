# utils/cpuidle-info.c:193: error: undefined reference to 'cpufreq_cpu_exists'
%define _disable_ld_no_undefined 1

# (tpg) try to speed up things
%global optflags %{optflags} -Ofast

# While perf comes with python2 scripts
%define _python_bytecompile_build 0

# IMPORTANT
# This is the place where you set kernel version i.e 4.5.0
# compose tar.xz name and release
%define kernelversion	5
%define patchlevel	0
%define sublevel	0
%define relc		6
# Only ever wrong on x.0 releases...
#define previous	%{kernelversion}.%(echo $((%{patchlevel}-1)))
%define previous	4.20

%define buildrel	%{kversion}-%{buildrpmrel}
%define rpmtag	%{disttag}

# (crazy) , well that new way of doing buil-id symlinks
# does not seems to work, see:
# https://issues.openmandriva.org/show_bug.cgi?id=2400
# let us try *old* way for kernel package(s)
%global _build_id_links alldebug

# IMPORTANT
# This is the place where you set release version %{version}-1omv2015
%if 0%{relc}
%define rpmrel		0.rc%{relc}.1
%define tar_ver   	%{kernelversion}.%{patchlevel}-rc%{relc}
%else
%define rpmrel		1
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

# fakerel and fakever never change, they are used to fool
# rpm/urpmi/smart
%define fakever		1
%define fakerel		%mkrel 1

# version defines
%define kversion	%{kernelversion}.%{patchlevel}.%{sublevel}
%define kverrel		%{kversion}-%{rpmrel}

# Having different top level names for packges means that you have to remove
# them by hard :(
%define top_dir_name	%{kname}-%{_arch}

%define build_dir	${RPM_BUILD_DIR}/%{top_dir_name}

# Disable useless debug rpms...
%define _enable_debug_packages	%{nil}
%define debug_package		%{nil}

# Build defines
%bcond_with build_doc
%bcond_without build_source
%bcond_without build_devel
%bcond_with build_debug
%bcond_with clang
# (tpg) enable patches from ClearLinux
%bcond_without clr
%if %mdvver > 3000000
%bcond_without cross_headers
%else
%bcond_with cross_headers
%endif

%global	cross_header_archs	aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv32-linuxmusl riscv64-linuxmusl aarch64-android armv7l-android armv8l-android
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
%bcond_with build_perf
%bcond_without build_x86_energy_perf_policy
%bcond_without build_turbostat
%ifarch %{ix86} %{x86_64}
%bcond_without build_cpupower
%else
# cpupower is currently x86 only
%bcond_with build_cpupower
%endif

# compress modules with zstd
# (tpg) currently it supports only x86 arch
%ifnarch %{armx}
%bcond_without build_modzstd
%else
%bcond_without build_modxz
%endif

# ARM builds
%ifarch %{armx}
%bcond_with build_desktop
%bcond_without build_server
%endif
# End of user definitions

# For the .nosrc.rpm
%bcond_with build_nosrc

############################################################
### Linker start1 > Check point to build for omv or rosa ###
############################################################
%define kmake ARCH=%{target_arch} %{make} LD="$LD"
# there are places where parallel make don't work
# usually we use this
%define smake make LD="$LD"

###################################################
###  Linker end1 > Check point to build for omv ###
###################################################
# Parallelize xargs invocations on smp machines
%define kxargs xargs %([ -z "$RPM_BUILD_NCPUS" ] \\\
	&& RPM_BUILD_NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"; \\\
	[ "$RPM_BUILD_NCPUS" -gt 1 ] && echo "-P $RPM_BUILD_NCPUS")

# Sparc arch wants sparc64 kernels
%define target_arch %(echo %{_arch} | sed -e 's/mips.*/mips/' -e 's/arm.*/arm/' -e 's/aarch64/arm64/')

#
# SRC RPM description
#
Summary:	Linux kernel built for %{distribution}
Name:		%{kname}
Version:	%{kversion}
Release:	%{rpmrel}
License:	GPLv2
Group:		System/Kernel and hardware
ExclusiveArch:	%{ix86} %{x86_64} %{armx}
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

Source4:	README.kernel-sources
Source5:	%{name}.rpmlintrc
# Global configs
Source6:	common.config
Source8:	common-desktop.config
Source9:	common-server.config
# Architecture specific configs
Source7:	x86_64-common.config
Source10:	i386-common.config
Source11:	arm64-common.config
Source12:	arm-common.config
Source13:	znver1-common.config
# Files called $ARCH-$FLAVOR.config are merged as well,
# currently there's no need to have specific overloads there.

# config and systemd service file from fedora
Source50:	cpupower.service
Source51:	cpupower.config

# Patches
# Numbers 0 to 9 are reserved for upstream patches
# (-stable patch, -rc, ...)
# Added as a Source rather that Patch because it needs to be
# applied with "git apply" -- may contain binary patches.
%if 0%{sublevel}
Source90:	https://cdn.kernel.org/pub/linux/kernel/v4.x/patch-%{version}.xz
%endif
Patch2:		die-floppy-die.patch
Patch3:		0001-Add-support-for-Acer-Predator-macro-keys.patch
Patch4:		linux-4.7-intel-dvi-duallink.patch
Patch5:		linux-4.8.1-buildfix.patch

%if %{with clang}
# Patches to make it build with clang
Patch1000:	0001-kbuild-LLVMLinux-Set-compiler-flags-for-clang.patch
Patch1001:	0002-fs-LLVMLinux-Remove-warning-from-COMPATIBLE_IOCTL.patch
Patch1002:	0003-kbuild-LLVMLinux-Add-support-for-generating-LLVM-bit.patch
Patch1003:	0004-kbuild-LLVMLinux-Make-asm-offset-generation-work-wit.patch
Patch1004:	0005-md-sysfs-LLVMLinux-Remove-nested-function-from-bcach.patch
Patch1005:	0006-apparmor-LLVMLinux-Remove-VLAIS.patch
Patch1006:	0007-exofs-LLVMLinux-Remove-VLAIS-from-exofs-FIXME-Check-.patch
Patch1007:	0008-md-raid10-LLVMLinux-Remove-VLAIS-from-raid10-driver.patch
Patch1008:	0009-fs-nfs-LLVMLinux-Remove-VLAIS-from-nfs.patch
Patch1009:	0010-net-wimax-i2400-LLVMLinux-Remove-VLAIS-from-wimax-i2.patch
Patch1010:	0011-Kbuild-LLVMLinux-Use-Oz-instead-of-Os-when-using-cla.patch
Patch1011:	0012-WORKAROUND-x86-boot-LLVMLinux-Work-around-clang-PR39.patch
Patch1012:	0013-DO-NOT-UPSTREAM-xen-LLVMLinux-Remove-VLAIS-from-xen-.patch
Patch1013:	0014-DO-NOT-UPSTREAM-arm-LLVMLinux-Provide-__aeabi_-symbo.patch
Patch1014:	0015-DO-NOT-UPSTREAM-arm-firmware-LLVMLinux-replace-naked.patch
Patch1015:	0016-arm-LLVMLinux-Remove-unreachable-from-naked-function.patch
Patch1016:	0017-MIPS-LLVMLinux-Fix-a-cast-to-type-not-present-in-uni.patch
Patch1017:	0018-MIPS-LLVMLinux-Fix-an-inline-asm-input-output-type-m.patch
Patch1018:	0019-MIPS-LLVMLinux-Silence-variable-self-assignment-warn.patch
Patch1019:	0020-MIPS-LLVMLinux-Silence-unicode-warnings-when-preproc.patch
Patch1020:	0021-Don-t-use-attributes-error-and-warning-with-clang.patch
Patch1021:	0022-Fix-undefined-references-to-acpi_idle_driver-on-aarc.patch
Patch1022:	0023-HACK-firmware-LLVMLinux-fix-EFI-libstub-with-clang.patch
Patch1023:	0024-aarch64-crypto-LLVMLinux-Fix-inline-assembly-for-cla.patch
Patch1024:	0025-aarch64-LLVMLinux-Make-spin_lock_prefetch-asm-code-c.patch
Patch1025:	0026-LLVMLinux-Don-t-use-attribute-externally_visible-whe.patch
Patch1026:	0027-x86-crypto-LLVMLinux-Fix-building-x86_64-AES-extensi.patch
Patch1027:	0028-x86-LLVMLinux-Qualify-mul-as-mulq-to-make-clang-happ.patch
Patch1028:	0029-kbuild-LLVMLinux-Add-Werror-to-cc-option-in-order-to.patch
Patch1029:	0030-x86-kbuild-LLVMLinux-Check-for-compiler-support-of-f.patch
#Patch1030:	0031-x86-cmpxchg-break.patch
Patch1031:	0001-Fix-for-compilation-with-clang.patch
%endif

# Bootsplash system
# https://lkml.org/lkml/2017/10/25/346
# https://patchwork.kernel.org/patch/10172665/, rebased
Patch100:	RFC-v3-01-13-bootsplash-Initial-implementation-showing-black-screen.patch
# https://patchwork.kernel.org/patch/10172669/
Patch101:	RFC-v3-02-13-bootsplash-Add-file-reading-and-picture-rendering.patch
# https://patchwork.kernel.org/patch/10172715/
Patch102:	RFC-v3-03-13-bootsplash-Flush-framebuffer-after-drawing.patch
# https://patchwork.kernel.org/patch/10172699/
Patch103:	RFC-v3-04-13-bootsplash-Add-corner-positioning.patch
# https://patchwork.kernel.org/patch/10172667/
Patch104:	RFC-v3-05-13-bootsplash-Add-animation-support.patch
# https://patchwork.kernel.org/patch/10172605/, rebased
Patch105:	RFC-v3-06-13-vt-Redraw-bootsplash-fully-on-console_unblank.patch
# https://patchwork.kernel.org/patch/10172599/
Patch106:	RFC-v3-07-13-vt-Add-keyboard-hook-to-disable-bootsplash.patch
# https://patchwork.kernel.org/patch/10172603/
Patch107:	RFC-v3-08-13-sysrq-Disable-bootsplash-on-SAK.patch
# https://patchwork.kernel.org/patch/10172601/
Patch108:	RFC-v3-09-13-fbcon-Disable-bootsplash-on-oops.patch
# https://patchwork.kernel.org/patch/10172663/
Patch109:	RFC-v3-10-13-Documentation-Add-bootsplash-main-documentation.patch
# https://patchwork.kernel.org/patch/10172685/
Patch110:	RFC-v3-11-13-bootsplash-sysfs-entries-to-load-and-unload-files.patch
# https://patchwork.kernel.org/patch/10172597/
Patch111:	RFC-v3-12-13-tools-bootsplash-Add-a-basic-splash-file-creation-tool.patch
# https://patchwork.kernel.org/patch/10172661/
# Contains git binary patch -- needs to be applied with git apply instead of apply_patches
Source112:	RFC-v3-13-13-tools-bootsplash-Add-script-and-data-to-create-sample-file.patch

# (tpg) The Ultra Kernel Same Page Deduplication
# (tpg) http://kerneldedup.org/en/projects/uksm/download/
# (tpg) sources can be found here https://github.com/dolohow/uksm
# Temporarily disabled until ported upstream
#Patch120:	https://raw.githubusercontent.com/dolohow/uksm/master/uksm-4.19.patch
# Sometimes other people are ahead of upstream porting to new releases...
#Patch120:	https://github.com/sirlucjan/kernel-patches/raw/master/4.19/pf-uksm/0001-uksm-4.19-initial-submission.patch

# VirtualBox module patches are added as SOURCE: instead of PATCH:
# because it needs to be applied after sources are compied in
# (long after %%autosetup)
Source115:	vbox-kernel-5.0.patch

%if %{with build_modzstd}
# https://patchwork.kernel.org/patch/10003007/
Patch126:	v2-1-2-lib-Add-support-for-ZSTD-compressed-kernel.patch
# https://patchwork.kernel.org/patch/10003011/
Patch127:	v2-2-2-x86-Add-support-for-ZSTD-compressed-kernel.patch
%endif

### Additional hardware support
### TV tuners:
# SAA716x DVB driver
# git clone git@github.com:crazycat69/linux_media
# cd linux_media
# tar cJf saa716x-driver.tar.xz drivers/media/pci/saa716x drivers/media/dvb-frontends/tas2101* drivers/media/dvb-frontends/isl6422* drivers/media/dvb-frontends/stv091x.h drivers/media/tuners/av201x* drivers/media/tuners/stv6120*
# Patches 141 to 145 are a minimal set of patches to the DVB stack to make
# the added driver work.
Source140:	saa716x-driver.tar.xz
Patch141:	0023-tda18212-Added-2-extra-options.-Based-on-CrazyCat-re.patch
Patch142:	0075-cx24117-Use-a-pointer-to-config-instead-of-storing-i.patch
Patch143:	0076-cx24117-Add-LNB-power-down-callback.-TBS6984-uses-pc.patch
Patch144:	0124-Extend-FEC-enum.patch
Patch145:	saa716x-driver-integration.patch
Patch146:	saa716x-4.15.patch
Patch147:	saa716x-linux-4.19.patch

# Add LIMA driver for Mali 400/450
# From https://gitlab.freedesktop.org/lima/linux.git
Patch150:	kernel-4.17-rc7-add-lima-driver.patch

# Anbox (http://anbox.io/) patches to Android IPC, rebased to 4.11
# NOT YET
#Patch200:	0001-ipc-namespace-a-generic-per-ipc-pointer-and-peripc_o.patch
# NOT YET
#Patch201:	0002-binder-implement-namepsace-support-for-Android-binde.patch

# NOT YET
#Patch250:	4.14-C11.patch

# VirtualBox shared folders support
# https://patchwork.kernel.org/patch/10315707/
# For newer versions, check
# https://patchwork.kernel.org/project/LKML/list/?submitter=582
Patch300:	v7-fs-Add-VirtualBox-guest-shared-folder-vboxsf-support.patch
Patch301:	vbox-4.18.patch

# Better support for newer x86 processors
# Original patch:
#Patch310:	https://raw.githubusercontent.com/graysky2/kernel_gcc_patch/master/enable_additional_cpu_optimizations_for_gcc_v8.1%2B_kernel_v4.13%2B.patch
# More actively maintained for newer kernels
Patch310:	https://github.com/sirlucjan/kernel-patches/raw/master/4.18/gcc-patch-backup-from-pf/0001-gcctunes-4.18-merge-graysky-s-patchset.patch

# Assorted fixes
## Intel Core2Duo got always unstable tsc , with changes in 4.18
## some models cannot boot anymore , they are stuck in a endless loop.
## see: https://lkml.org/lkml/2018/8/30/341
##      https://bugzilla.kernel.org/show_bug.cgi?id=200957
## patch is an backport from : https://lkml.org/lkml/2018/9/3/253
Patch330:	https://raw.githubusercontent.com/frugalware/frugalware-current/71a887a9f309345f966c4d09c920642a62efb66f/source/base/kernel/fix-C2D-CPUs-booting.patch
Patch331:	https://gitweb.frugalware.org/frugalware-current/raw/master/source/base/kernel/drop_ancient-and-wrong-msg.patch

# Modular binder and ashmem -- let's try to make anbox happy
Patch340:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/android-enable-building-ashmem-and-binder-as-modules.patch
# based on https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/export-symbols-needed-by-android-drivers.patch -- rebased
Patch341:	export-symbols-needed-by-android-drivers.patch

%if %{with clr}
# (tpg) some patches from ClearLinux
Patch400:	0101-i8042-decrease-debug-message-level-to-info.patch
Patch401:	0103-Increase-the-ext4-default-commit-age.patch
#Patch402:	0105-pci-pme-wakeups.patch
Patch404:	0107-intel_idle-tweak-cpuidle-cstates.patch
Patch405:	0109-init_task-faster-timerslack.patch
# Needs rebase
#Patch406:	0110-fs-ext4-fsync-optimize-double-fsync-a-bunch.patch
# Needs rebase
#Patch407:	0111-overload-on-wakeup.patch
# needs a rediff
#Patch408:	0113-fix-initcall-timestamps.patch
# This is actually a bad idea.
# Especially in the ARM world, not every core is necessarily
# the same speed.
#Patch409:	0114-smpboot-reuse-timer-calibration.patch
Patch410:	0116-Initialize-ata-before-graphics.patch
Patch411:	0117-reduce-e1000e-boot-time-by-tightening-sleep-ranges.patch
Patch412:	0119-e1000e-change-default-policy.patch
Patch413:	0120-ipv4-tcp-allow-the-memory-tuning-for-tcp-to-go-a-lit.patch
Patch414:	0121-igb-no-runtime-pm-to-fix-reboot-oops.patch
Patch415:	0122-tweak-perfbias.patch
Patch416:	0123-e1000e-increase-pause-and-refresh-time.patch
Patch417:	0124-kernel-time-reduce-ntp-wakeups.patch
Patch418:	0125-init-wait-for-partition-and-retry-scan.patch
Patch419:	0151-mm-Export-do_madvise.patch
# Needs rebase
#Patch420:	0152-x86-kvm-Notify-host-to-release-pages.patch
# Relies on 420
#Patch421:	0153-x86-Return-memory-from-guest-to-host-kernel.patch
# Needs rebase
#Patch422:	0154-sysctl-vm-Fine-grained-cache-shrinking.patch
%endif

# (crazy) see: https://forum.openmandriva.org/t/nvme-ssd-m2-not-seen-by-omlx-4-0/2407
# Not even sure what Vendor that one is .. However it seems be one of the ones random doing that
# like some Toshibas and some Samsung ones , so disable APST for this one..
Patch800: Unknow-SSD-HFM128GDHTNG-8310B-QUIRK_NO_APST.patch

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
%define requires2	dracut >= 047
%define requires3	kmod >= 25
%define requires4	sysfsutils >=  2.1.0-12
%define requires5	kernel-firmware

%define kprovides1	%{kname} = %{kverrel}
%define kprovides2	kernel = %{tar_ver}
%define kprovides_server	drbd-api = 88

%define kobsoletes1	dkms-r8192se <= 0019.1207.2010-2
%define kobsoletes2	dkms-lzma <= 4.43-32
%define kobsoletes3	dkms-psb <= 4.41.1-7

%define kconflicts1	dkms-broadcom-wl < 5.100.82.112-12
%define kconflicts2	dkms-fglrx < 13.200.5-1
%define kconflicts3	dkms-nvidia-current < 325.15-1
%define kconflicts4	dkms-nvidia-long-lived < 319.49-1
%define kconflicts5	dkms-nvidia304 < 304.108-1
# nvidia173 does not support this kernel

Autoreqprov:	no
%if %{with build_modzstd}
BuildRequires:	zstd
%endif
%if %{with build_modxz}
BuildRequires:	xz
%endif
BuildRequires:	findutils
BuildRequires:	bc
BuildRequires:	flex
BuildRequires:	bison
BuildRequires:	binutils
BuildRequires:	gcc >= 7.2.1_2017.11-3
BuildRequires:	gcc-plugin-devel >= 7.2.1_2017.11-3
BuildRequires:	gcc-c++ >= 7.2.1_2017.11-3
BuildRequires:	pkgconfig(libssl)
BuildRequires:	diffutils
# For git apply
BuildRequires:	git-core
# For power tools
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	pkgconfig(libkmod)

%ifarch %{x86_64}
BuildRequires:	numa-devel
%endif

# for cpupower
%if %{with build_cpupower}
BuildRequires:	pkgconfig(libpci)
%endif

# for docs
%if %{with build_doc}
BuildRequires:	xmlto
%endif

# for ORC unwinder and perf
BuildRequires:	pkgconfig(libelf)

# for perf
%if %{with build_perf}
BuildRequires:	asciidoc
BuildRequires:	pkgconfig(audit)
BuildRequires:	binutils-devel
BuildRequires:	bison
# BuildRequires:	docbook-style-xsl
BuildRequires:	flex
# BuildRequires:	gettext
# BuildRequires:	gtk2-devel
BuildRequires:	pkgconfig(libunwind)
BuildRequires:	pkgconfig(libnewt)
BuildRequires:	perl-devel
# BuildRequires:	perl(ExtUtils::Embed)
BuildRequires:	pkgconfig(gtk+-2.0)
BuildRequires:	pkgconfig(python2)
BuildRequires:	pkgconfig(zlib)
%endif

%ifarch %{arm}
BuildRequires:	uboot-mkimage
%endif

# might be useful too:
Suggests:	microcode-intel

# Let's pull in some of the most commonly used DKMS modules
# so end users don't have to install compilers (and worse,
# get compiler error messages on failures)
%if %mdvver >= 3000000
%ifarch %{ix86} %{x86_64}
BuildRequires:	dkms-virtualbox >= 5.2.22-1
BuildRequires:	dkms-vboxadditions >= 5.2.22-1
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
%package -n %{kname}-%{1}-%{buildrel}			\
Version:	%{fakever}				\
Release:	%{fakerel}				\
Provides:	%kprovides1 %kprovides2			\
%{expand:%%{?kprovides_%{1}:Provides: %{kprovides_%{1}}}} \
Provides:	%{kname}-%{1}				\
Requires(pre):	%requires3 %requires4			\
Requires:	%requires5				\
Obsoletes:	%kobsoletes1 %kobsoletes2 %kobsoletes3	\
Conflicts:	%kconflicts1 %kconflicts2 %kconflicts3	\
Conflicts:	%kconflicts4 %kconflicts5		\
Provides:	should-restart = system			\
Suggests:	crda					\
Suggests:	iw					\
%ifnarch %armx						\
Suggests:	cpupower				\
Suggests:	microcode-intel				\
Suggests:	dracut >= 047				\
%endif							\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
Summary:	%{expand:%{summary_%(echo %{1} | sed -e "s/-/_/")}} \
Group:		System/Kernel and hardware		\
%description -n %{kname}-%{1}-%{buildrel}		\
%common_desc_kernel %{expand:%{info_%(echo %{1} | sed -e "s/-/_/")}} \
							\
%if %{with build_devel}					\
%package -n	%{kname}-%{1}-devel-%{buildrel}		\
Version:	%{fakever}				\
Release:	%{fakerel}				\
Requires:	glibc-devel				\
Requires:	ncurses-devel				\
Requires:	make					\
Requires:	gcc >= 7.2.1_2017.11-3			\
Requires:	perl					\
%ifarch %{x86_64}					\
Requires:	pkgconfig(libelf)			\
%endif							\
Summary:	The kernel-devel files for %{kname}-%{1}-%{buildrel} \
Group:		Development/Kernel			\
Provides:	kernel-devel = %{kverrel}		\
Provides:	%{kname}-devel = %{kverrel} 		\
Provides:	%{kname}-%{1}-devel			\
Requires:	%{kname}-%{1}-%{buildrel}		\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
%description -n %{kname}-%{1}-devel-%{buildrel}		\
This package contains the kernel files (headers and build tools) \
that should be enough to build additional drivers for   \
use with %{kname}-%{1}-%{buildrel}.                     \
							\
If you want to build your own kernel, you need to install the full \
%{kname}-source-%{buildrel} rpm.			\
							\
%endif							\
							\
%if %{with build_debug}					\
%package -n	%{kname}-%{1}-%{buildrel}-debuginfo	\
Version:	%{fakever}				\
Release:	%{fakerel}				\
Summary:	Files with debuginfo for %{kname}-%{1}-%{buildrel} \
Group:		Development/Debug			\
Provides:	kernel-debug = %{kverrel} 		\
Requires:	%{kname}-%{1}-%{buildrel}		\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
%description -n %{kname}-%{1}-%{buildrel}-debuginfo	\
This package contains the files with debuginfo to aid in debug tasks \
when using %{kname}-%{1}-%{buildrel}.			\
							\
If you need to look at debug information or use some application that \
needs debugging info from the kernel, this package may help. \
							\
%endif							\
							\
%package -n %{kname}-%{1}-latest			\
Version:	%{kversion}				\
Release:	%{rpmrel}				\
Summary:	Virtual rpm for latest %{kname}-%{1}	\
Group:		System/Kernel and hardware		\
Requires:	%{kname}-%{1}-%{buildrel}		\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
%{expand:%%{?latest_obsoletes_%{1}:Obsoletes: %{latest_obsoletes_%{1}}}} \
%{expand:%%{?latest_provides_%{1}:Provides: %{latest_provides_%{1}}}} \
%description -n %{kname}-%{1}-latest			\
This package is a virtual rpm that aims to make sure you always have the \
latest %{kname}-%{1} installed...			\
							\
%if %{with build_devel}					\
%package -n %{kname}-%{1}-devel-latest			\
Version:	%{kversion}				\
Release:	%{rpmrel}				\
Summary:	Virtual rpm for latest %{kname}-%{1}-devel \
Group:		Development/Kernel			\
Requires:	%{kname}-%{1}-devel-%{buildrel}		\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
Conflicts:	arch(znver1)				\
%endif							\
Provides:	%{kname}-devel-latest			\
%{expand:%%{?latest_obsoletes_devel_%{1}:Obsoletes: %{latest_obsoletes_devel_%{1}}}} \
%{expand:%%{?latest_provides_devel_%{1}:Provides: %{latest_provides_devel_%{1}}}} \
%description -n %{kname}-%{1}-devel-latest		\
This package is a virtual rpm that aims to make sure you always have the \
latest %{kname}-%{1}-devel installed...			\
							\
%endif							\
							\
%post -n %{kname}-%{1}-%{buildrel} -f kernel_files.%{1}-post \
%posttrans -n %{kname}-%{1}-%{buildrel} -f kernel_files.%{1}-posttrans \
%preun -n %{kname}-%{1}-%{buildrel} -f kernel_files.%{1}-preun \
%postun -n %{kname}-%{1}-%{buildrel} -f kernel_files.%{1}-postun \
							\
%if %{with build_devel}					\
%post -n %{kname}-%{1}-devel-%{buildrel} -f kernel_devel_files.%{1}-post \
%preun -n %{kname}-%{1}-devel-%{buildrel} -f kernel_devel_files.%{1}-preun \
%postun -n %{kname}-%{1}-devel-%{buildrel} -f kernel_devel_files.%{1}-postun \
%endif							\
							\
%files -n %{kname}-%{1}-%{buildrel} -f kernel_files.%{1} \
%files -n %{kname}-%{1}-latest				\
							\
%if %{with build_devel}					\
%files -n %{kname}-%{1}-devel-%{buildrel} -f kernel_devel_files.%{1} \
%files -n %{kname}-%{1}-devel-latest			\
%endif							\
							\
%if %{with build_debug}					\
%files -n %{kname}-%{1}-%{buildrel}-debuginfo -f kernel_debug_files.%{1} \
%endif

# kernel-desktop: i686, smp-alternatives, 4 GB / x86_64
#
%if %{with build_desktop}
%ifarch %{ix86}
%define summary_desktop Linux Kernel for desktop use with i686 & 4GB RAM
%define info_desktop This kernel is compiled for desktop use, single or \
multiple i686 processor(s)/core(s) and less than 4GB RAM, using HZ_1000, \
voluntary preempt, CFS cpu scheduler and BFQ i/o scheduler.
%else
%define summary_desktop Linux Kernel for desktop use with %{_arch}
%define info_desktop This kernel is compiled for desktop use, single or \
multiple %{_arch} processor(s)/core(s), using HZ_1000, \
voluntary preempt, CFS cpu scheduler and BFQ i/o scheduler, ONDEMAND governor.
%endif
%mkflavour desktop
%endif

#
%if %{with build_server}
%ifarch %{ix86}
%define summary_server Linux Kernel for server use with i686 & 64GB RAM
%define info_server This kernel is compiled for server use, single or \
multiple i686 processor(s)/core(s) and up to 64GB RAM using PAE, using \
no preempt, HZ_100, CFS cpu scheduler and BFQ i/o scheduler, PERFORMANCE governor.
%else
%define summary_server Linux Kernel for server use with %{_arch}
%define info_server This kernel is compiled for server use, single or \
CFS cpu scheduler and BFQ i/o scheduler, PERFORMANCE governor.
%endif
%mkflavour server
%endif

#
# kernel-source
#
%if %{with build_source}
%package -n %{kname}-source-%{buildrel}
Version:	%{fakever}
Release:	%{fakerel}
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
Buildarch:	noarch

%description -n %{kname}-source-%{buildrel}
The %{kname}-source package contains the source code files for the Mandriva and
ROSA kernel. Theese source files are only needed if you want to build your own
custom kernel that is better tuned to your particular hardware.

If you only want the files needed to build 3rdparty (nVidia, Ati, dkms-*,...)
drivers against, install the *-devel-* rpm that is matching your kernel.

#
# kernel-source-latest: virtual rpm
#
%package -n %{kname}-source-latest
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Virtual rpm for latest %{kname}-source
Group:		Development/Kernel
Requires:	%{kname}-source-%{buildrel}
Buildarch:	noarch

%description -n %{kname}-source-latest
This package is a virtual rpm that aims to make sure you always have the
latest %{kname}-source installed...
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
%if %{with build_perf}
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

%package -n bootsplash-packer
Summary:	Tool for packing bootsplash images
Group:		System/Kernel and hardware
Version:	%{kversion}
Release:	%{rpmrel}

%description -n bootsplash-packer
Tool for packing bootsplash images.

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

%package headers
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Linux kernel header files mostly used by your C library
Group:		System/Kernel and hardware
Epoch:		1
# (tpg) fix bug https://issues.openmandriva.org/show_bug.cgi?id=1580
Provides:	kernel-headers = 1:%{kverrel}
Obsoletes:	kernel-headers < 1:%{kverrel}
# we don't need the kernel binary in chroot
#Requires:	%{kname} = %{kverrel}
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
%setup -q -n linux-%{tar_ver} -a 140
cp %{S:6} %{S:7} %{S:8} %{S:9} %{S:10} %{S:11} %{S:12} %{S:13} kernel/configs/

%if 0%{sublevel}
[ -e .git ] || git init
xzcat %{SOURCE90} |git apply - || git apply %{SOURCE90}
rm -rf .git
%endif
%apply_patches
git apply %{SOURCE112}

# merge SAA716x DVB driver from extra tarball
sed -i -e '/saa7164/isource "drivers/media/pci/saa716x/Kconfig"' drivers/media/pci/Kconfig
sed -i -e '/saa7164/iobj-$(CONFIG_SAA716X_CORE) += saa716x/' drivers/media/pci/Makefile
find drivers/media/tuners drivers/media/dvb-frontends -name "*.c" -o -name "*.h" |xargs sed -i -e 's,"dvb_frontend.h",<media/dvb_frontend.h>,g'

%if %{with build_debug}
%define debug --debug
%else
%define debug --no-debug
%endif

# make sure the kernel has the sublevel we know it has...
LC_ALL=C sed -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{sublevel}/" Makefile

# Pull in some externally maintained modules
%if %mdvver >= 3000000
%ifarch %{ix86} %{x86_64}
# === VirtualBox guest additions ===
# VBoxVideo is upstreamed -- let's fix it instead of copying the dkms driver
# 800x600 is too small to be useful -- even calamares doesn't
# fit into that anymore
sed -i -e 's|800, 600|1024, 768|g' drivers/staging/vboxvideo/vbox_mode.c
# VBoxGuest is upstreamed -- no need to do anything for it
# VirtualBox shared folders now come in through patch 300

# === VirtualBox host modules ===
# VirtualBox
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxdrv drivers/virt/
sed -i -e 's,\$(KBUILD_EXTMOD),drivers/virt/vboxdrv,g' drivers/virt/vboxdrv/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/virt/vboxdrv/Makefile*
echo 'obj-m += vboxdrv/' >>drivers/virt/Makefile
# VirtualBox network adapter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetadp drivers/net/
sed -i -e 's,\$(KBUILD_EXTMOD),drivers/net/vboxnetadp,g' drivers/net/vboxnetadp/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetadp/Makefile*
echo 'obj-m += vboxnetadp/' >>drivers/net/Makefile
# VirtualBox network filter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetflt drivers/net/
sed -i -e 's,\$(KBUILD_EXTMOD),drivers/net/vboxnetflt,g' drivers/net/vboxnetflt/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetflt/Makefile*
echo 'obj-m += vboxnetflt/' >>drivers/net/Makefile
# VirtualBox PCI
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxpci drivers/pci/
sed -i -e 's,\$(KBUILD_EXTMOD),drivers/pci/vboxpci,g' drivers/pci/vboxpci/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/pci/vboxpci/Makefile*
echo 'obj-m += vboxpci/' >>drivers/pci/Makefile
git apply %{SOURCE115}
%endif
%endif

# get rid of unwanted files
find . -name '*~' -o -name '*.orig' -o -name '*.append' -delete
# wipe all .gitignore/.get_maintainer.ignore files
find . -name "*.g*ignore" -delete

# fix missing exec flag on file introduced in 4.14.10-rc1
chmod 755 tools/objtool/sync-check.sh

%build
%setup_compile_flags
############################################################
### Linker start2 > Check point to build for omv or rosa ###
############################################################
# Make sure we don't use gold
export LD="%{_target_platform}-ld.bfd"
export PYTHON=%{__python2}

############################################################
###  Linker end2 > Check point to build for omv or rosa ###
############################################################
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

CreateConfig() {
	arch="$1"
	type="$2"
	rm -f .config

%if %{with clang}
	CLANG_EXTRAS=clang-workarounds
%else
	CLANG_EXTRAS=""
%endif

%if %{with build_modxz}
sed -i -e "s/^# CONFIG_KERNEL_XZ is not set/CONFIG_KERNEL_XZ=y/g" kernel/configs/common.config
%endif

%if %{with build_modzstd}
sed -i -e "s/^# CONFIG_KERNEL_ZSTD is not set/CONFIG_KERNEL_ZSTD=y/g" kernel/configs/common.config
sed -i -e "s/^# CONFIG_RD_ZSTD is not set/CONFIG_RD_ZSTD=y/g" kernel/configs/common.config
%endif

	case ${arch} in
	i?86)
		CONFIGS="i386_defconfig"
		;;
	x86_64|znver1)
		CONFIGS="x86_64_defconfig"
		;;
	*)
		CONFIGS="defconfig"
		;;
	esac
	for i in common common-${type} ${arch}-common ${arch}-${type} $CLANG_EXTRAS; do
		[ -e kernel/configs/$i.config ] && CONFIGS="$CONFIGS $i.config"
	done
	if [ "$arch" = "znver1" ]; then
		# We need to build with ARCH=x86_64 rather than ARCH=znver1
		# and pull in both x86_64 and znver1 configs, with the latter
		# coming last so it can override the former
		CONFIGS="${CONFIGS/znver1.config/x86_64.config znver1.config}"
		arch=x86
	fi
	make ARCH="${arch}" $CONFIGS
	scripts/config --set-val BUILD_SALT \"$(echo "$arch-$type-%{EVRD}"|sha1sum|awk '{ print $1; }')\"
}

PrepareKernel() {
    name=$1
    extension=$2
    config_dir=%{_sourcedir}
    printf '%s\n' "Make config for kernel $extension"
    %{smake} -s mrproper
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
# (tpg) build with gcc, as kernel is not yet ready for LLVM/clang
%ifarch %{x86_64}
%if %{with clang}
    %kmake all CC=clang CXX=clang++ CFLAGS="$CFLAGS -flto"
%else
    %kmake all CC=gcc CXX=g++ CFLAGS="$CFLAGS -flto"
%endif
%else
%if %{with clang}
    %kmake all CC=clang CXX=clang++ CFLAGS="$CFLAGS"
%else
    %kmake all CC=gcc CXX=g++ CFLAGS="$CFLAGS"
%endif
%endif

# Start installing stuff
    install -d %{temp_boot}
    install -m 644 System.map %{temp_boot}/System.map-$KernelVer
    install -m 644 .config %{temp_boot}/config-$KernelVer

%if %{with build_modxz}
%ifarch %{ix86} %{armx}
    xz -5 -T0 -c Module.symvers > %{temp_boot}/symvers-$KernelVer.xz
%else
    xz -7 -T0 -c Module.symvers > %{temp_boot}/symvers-$KernelVer.xz
%endif
%endif

%if %{with build_modzstd}
%ifarch %{ix86} %{armx}
    zstd -15 -q -T0 -c Module.symvers > %{temp_boot}/symvers-$KernelVer.zst
%else
    zstd -10 -q -T0 -c Module.symvers > %{temp_boot}/symvers-$KernelVer.zst
%endif
%endif

%ifarch %{arm}
    if [ -f arch/arm/boot/uImage ]; then
	cp -f arch/arm/boot/uImage %{temp_boot}/uImage-$KernelVer
    else
	cp -f arch/arm/boot/zImage %{temp_boot}/vmlinuz-$KernelVer
    fi
%else
%ifarch aarch64
    cp -f arch/arm64/boot/Image.gz %{temp_boot}/vmlinuz-$KernelVer
%else
    cp -f arch/%{target_arch}/boot/bzImage %{temp_boot}/vmlinuz-$KernelVer
%endif
%endif

# modules
    install -d %{temp_modules}/$KernelVer
    %{smake} INSTALL_MOD_PATH=%{temp_root} KERNELRELEASE=$KernelVer INSTALL_MOD_STRIP=1 modules_install

# headers
    %{make} INSTALL_HDR_PATH=%{temp_root}%{_prefix} KERNELRELEASE=$KernelVer headers_install

%ifarch %{armx}
    %{smake} ARCH=%{target_arch} V=1 dtbs INSTALL_DTBS_PATH=%{temp_boot}/dtb-$KernelVer dtbs_install
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
#     ln -s ../generated/uapi/linux/version.h $TempDevelRoot/include/linux/version.h
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

# add acpica header files, needed for fglrx build
    cp -fR drivers/acpi/acpica/*.h $TempDevelRoot/drivers/acpi/acpica/

# orc unwinder needs theese
    cp -fR tools/build/Build{,.include} $TempDevelRoot/tools/build
    cp -fR tools/build/fixdep.c $TempDevelRoot/tools/build
    cp -fR tools/lib/{str_error_r.c,string.c} $TempDevelRoot/tools/lib
    cp -fR tools/lib/subcmd/* $TempDevelRoot/tools/lib/subcmd
    cp -fR tools/objtool/* $TempDevelRoot/tools/objtool
    cp -fR tools/scripts/utilities.mak $TempDevelRoot/tools/scripts

    for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
		 mips mn10300 nds32 nios2 openrisc parisc powerpc s390 score sh sparc tile unicore32 xtensa; do
	rm -rf $TempDevelRoot/arch/$i
    done

# Clean the scripts tree, and make sure everything is ok (sanity check)
# running prepare+scripts (tree was already "prepared" in build)
    cd $TempDevelRoot >/dev/null
    %{smake} ARCH=%{target_arch} clean
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
$DevelRoot/arch/riscv
$DevelRoot/arch/um
$DevelRoot/arch/x86
$DevelRoot/block
$DevelRoot/crypto
# here
$DevelRoot/certs
$DevelRoot/drivers
$DevelRoot/firmware
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
%doc README.kernel-sources
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
    find %{temp_modules}/%{kversion}-$debug_flavour-%{buildrpmrel}/kernel -name "*.ko" | %kxargs -I '{}' sh -c 'cd `dirname {}`; objcopy --add-gnu-debuglink=`basename {}`.debug --strip-debug `basename {}`'

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
%{_bootdir}/symvers-%{kversion}-$kernel_flavour-%{buildrpmrel}.[gxz]*
%{_bootdir}/config-%{kversion}-$kernel_flavour-%{buildrpmrel}
%{_bootdir}/$ker-%{kversion}-$kernel_flavour-%{buildrpmrel}
%dir %{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/
%{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/kernel
%{_modulesdir}/%{kversion}-$kernel_flavour-%{buildrpmrel}/modules.*
%doc README.kernel-sources
EOF

%if %{with build_debug}
cat kernel_exclude_debug_files.$kernel_flavour >> $kernel_files
%endif

### Create kernel Post script
cat > $kernel_files-post <<EOF
/usr/bin/kernel-install add %{kversion}-$kernel_flavour-%{buildrpmrel} /boot/vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel}
cd /boot > /dev/null
if [ -L vmlinuz-$kernel_flavour ]; then
    rm -f vmlinuz-$kernel_flavour
fi
ln -sf vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel} vmlinuz-$kernel_flavour
if [ -L initrd-$kernel_flavour.img ]; then
    rm -f initrd-$kernel_flavour.img
fi
ln -sf initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img initrd-$kernel_flavour.img
if [ -e initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img ]; then
    ln -sf vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel} vmlinuz
    ln -sf initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img initrd.img
fi

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
if [ -x /usr/sbin/dkms_autoinstaller -a -d /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
    /usr/sbin/dkms_autoinstaller start %{kversion}-$kernel_flavour-%{buildrpmrel}
fi

if [ -x %{_sbindir}/dkms -a -e %{_unitdir}/dkms.service -a -d /usr/src/linux-%{kversion}-$kernel_flavour-%{buildrpmrel} ]; then
    /bin/systemctl --quiet restart dkms.service
    /bin/systemctl --quiet try-restart fedora-loadmodules.service
    %{_sbindir}/dkms autoinstall --verbose --kernelver %{kversion}-$kernel_flavour-%{buildrpmrel}
fi

EOF

### Create kernel Preun script on the fly
cat > $kernel_files-preun <<EOF
/usr/bin/kernel-install remove %{kversion}-$kernel_flavour-%{buildrpmrel}
cd /boot > /dev/null
if [ -L vmlinuz-$kernel_flavour ]; then
    if [ "$(readlink vmlinuz-$kernel_flavour)" = "vmlinuz-%{kversion}-$kernel_flavour-%{buildrpmrel}" ]; then
	rm -f vmlinuz-$kernel_flavour
    fi
fi
if [ -L initrd-$kernel_flavour.img ]; then
    if [ "$(readlink initrd-$kernel_flavour.img)" = "initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img" ]; then
	rm -f initrd-$kernel_flavour.img
    fi
fi
cd - > /dev/null
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

### Create kernel Postun script on the fly
cat > $kernel_files-postun <<EOF
rm -f /boot/initrd-%{kversion}-$kernel_flavour-%{buildrpmrel}.img
rm -rf /lib/modules/%{kversion}-$kernel_flavour-%{buildrpmrel} >/dev/null
if [ -d /var/lib/dkms ]; then
    rm -f /var/lib/dkms/*/kernel-%{kversion}-$devel_flavour-%{buildrpmrel}-%{_target_cpu} >/dev/null
    rm -rf /var/lib/dkms/*/*/%{kversion}-$devel_flavour-%{buildrpmrel} >/dev/null
    rm -f /var/lib/dkms-binary/*/kernel-%{kversion}-$devel_flavour-%{buildrpmrel}-%{_target_cpu} >/dev/null
    rm -rf /var/lib/dkms-binary/*/*/%{kversion}-$devel_flavour-%{buildrpmrel} >/dev/null
fi
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
for a in arm arm64 i386 x86_64 znver1; do
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
				*)
					[ "$a" != "$TripletArch" ] && continue
					;;
				esac
				%{smake} ARCH=${a} SRCARCH=${SARCH} INSTALL_HDR_PATH=%{temp_root}%{_prefix}/${i} headers_install
			done
		fi
%endif
	done
done
make mrproper

%if %{with build_desktop}
CreateKernel desktop
%endif

%if %{with build_server}
CreateKernel server
%endif

# how to build own flavour
# if %build_nrjQL_desktop
# CreateKernel nrjQL-desktop
# endif

# set extraversion to match srpm to get nice version reported by the tools
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{rpmrel}|" Makefile

############################################################
### Linker start3 > Check point to build for omv or rosa ###
############################################################
%if %{with build_perf}
%{smake} -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} PYTHON=%{__python2} WERROR=0 prefix=%{_prefix} all
%{smake} -C tools/perf -s CC=%{__cc} prefix=%{_prefix} PYTHON=%{__python2} man
%endif

%if %{with build_cpupower}
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%kmake -C tools/power/cpupower CPUFREQ_BENCH=false LDFLAGS="%{optflags}"
%endif

%kmake -C tools/bootsplash LDFLAGS="%{optflags}"

%ifarch %{ix86} %{x86_64}
%if %{with build_x86_energy_perf_policy}
%kmake -C tools/power/x86/x86_energy_perf_policy CC=clang LDFLAGS="%{optflags} -Wl,--build-id=none"
%endif

%if %{with build_turbostat}
%kmake -C tools/power/x86/turbostat CC=clang
%endif
%endif

############################################################
###  Linker end3 > Check point to build for omv or rosa  ###
############################################################

# We don't make to repeat the depend code at the install phase
%if %{with build_source}
PrepareKernel "" %{buildrpmrel}custom
%{smake} -s mrproper
%endif

###
### install
###
%install
install -m 644 %{SOURCE4} .

# Directories definition needed for installing
%define target_source %{buildroot}%{_kerneldir}
%define target_boot %{buildroot}%{_bootdir}
%define target_modules %{buildroot}%{_modulesdir}

# We want to be able to test several times the install part
rm -rf %{buildroot}
cp -a %{temp_root} %{buildroot}

# compressing modules
%if %{with build_modxz}
%ifarch %{ix86} %{armx}
find %{target_modules} -name "*.ko" | %kxargs xz -5 -T0
%else
find %{target_modules} -name "*.ko" | %kxargs xz -7 -T0
%endif
%else
find %{target_modules} -name "*.ko" | %kxargs gzip -9
%endif

#if %{with build_modzstd}
#ifarch %{ix86} %{armx}
#find %{target_modules} -name "*.ko" | %kxargs zstd -10 -q -T0 --rm
#else
#find %{target_modules} -name "*.ko" | %kxargs zstd -15 -q -T0 --rm
#endif
#endif

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
%if %{with build_perf}

# perf tool binary and supporting scripts/binaries
make -C tools/perf -s CC=%{__cc} V=1 DESTDIR=%{buildroot} WERROR=0 PYTHON=%{__python2} HAVE_CPLUS_DEMANGLE=1 prefix=%{_prefix} install

# perf man pages (note: implicit rpm magic compresses them later)
make -C tools/perf  -s CC=%{__cc} V=1 DESTDIR=%{buildroot} WERROR=0 PYTHON=%{__python2} HAVE_CPLUS_DEMANGLE=1 prefix=%{_prefix} install-man
%endif

############################################################
### Linker start4 > Check point to build for omv or rosa ###
############################################################
%if %{with build_cpupower}
%{make} -C tools/power/cpupower DESTDIR=%{buildroot} libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false CC=%{__cc} LDFLAGS="%{optflags}" install

rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{SOURCE50} %{buildroot}%{_unitdir}/cpupower.service
install -m644 %{SOURCE51} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
%endif

mkdir -p %{buildroot}%{_bindir}
install -m755 tools/bootsplash/bootsplash-packer %{buildroot}%{_bindir}/

%ifarch %{ix86} %{x86_64}
%if %{with build_x86_energy_perf_policy}
mkdir -p %{buildroot}%{_bindir} %{buildroot}%{_mandir}/man8
%kmake -C tools/power/x86/x86_energy_perf_policy install DESTDIR="%{buildroot}"
%endif
%if %{with build_turbostat}
mkdir -p %{buildroot}%{_bindir} %{buildroot}%{_mandir}/man8
%kmake -C tools/power/x86/turbostat install DESTDIR="%{buildroot}"
%endif
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
    mips nds32 nios2 openrisc parisc powerpc s390 score sh sh64 sparc tile unicore32 v850 xtensa mn10300; do
    rm -rf %{target_source}/arch/$i
done

# other misc files
rm -f %{target_source}/{.config.old,.config.cmd,.gitignore,.lst,.mailmap,.gitattributes}
rm -f %{target_source}/{.missing-syscalls.d,arch/.gitignore,firmware/.gitignore}
rm -rf %{target_source}/.tmp_depmod/

# more cleaning
cd %{target_source}
# lots of gitignore files
find -iname ".gitignore" -delete
# clean tools tree
%smake -C tools clean
%smake -C tools/build clean
%smake -C tools/build/feature clean
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
### Linker start4 > Check point to build for omv or rosa ###
############################################################

%if %{with build_source}
%files -n %{kname}-source-%{buildrel}
%doc README.kernel-sources
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
%{_kerneldir}/arch/riscv
%{_kerneldir}/arch/um
%{_kerneldir}/arch/x86
%{_kerneldir}/block
%{_kerneldir}/crypto
%{_kerneldir}/drivers
%{_kerneldir}/firmware
%{_kerneldir}/fs
%{_kerneldir}/certs/*
%{_kerneldir}/include/acpi
%{_kerneldir}/include/asm-generic
%{_kerneldir}/include/clocksource
%{_kerneldir}/include/crypto
%{_kerneldir}/include/drm
%{_kerneldir}/include/dt-bindings
%{_kerneldir}/include/keys
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

%files -n %{kname}-source-latest
%endif

%if %{with build_doc}
%files -n %{kname}-doc
%doc Documentation/*
%endif

%if %{with build_perf}
%files -n perf
%{_bindir}/perf
%ifarch %{x86_64}
%{_bindir}/perf-read-vdso32
%endif
%{_bindir}/trace
%{_libdir}/libperf-gtk.so
%dir %{_libdir}/traceevent
%dir %{_libdir}/traceevent/plugins
%{_libdir}/traceevent/plugins/plugin_*
%dir %{_prefix}/libexec/perf-core
%{_prefix}/libexec/perf-core/*
%{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
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

%files -n bootsplash-packer
%{_bindir}/bootsplash-packer

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
