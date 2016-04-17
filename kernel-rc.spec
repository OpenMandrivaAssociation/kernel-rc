# utils/cpuidle-info.c:193: error: undefined reference to 'cpufreq_cpu_exists'
%define _disable_ld_no_undefined 1

# IMPORTNAT
# This is the place where you set kernel version i.e 4.5.0
# compose tar.xz name and release
%define kernelversion	4
%define patchlevel	6
%define sublevel	0
%define relc		3

%define tar_ver   	%{kernelversion}.%(expr %{patchlevel} - 1)
%define buildrel	%{kversion}-%{buildrpmrel}
%define rpmtag	%{disttag}

# IMPORTANT
# This is the place where you set release version %{version}-1omv2015
%define rpmrel		0.rc%{relc}.2
%define buildrpmrel	%{rpmrel}%{rpmtag}

# kernel Makefile extraversion is substituted by
# kpatch wich are either 0 (empty), rc (kpatch)
%define kpatch		%{nil}

# kernel base name (also name of srpm)
%define kname		kernel-rc

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

%define	cross_header_archs	arm arm64 mips

%ifarch x86_64
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
%bcond_without build_cpupower

# compress modules with xz
%bcond_without build_modxz

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
%define kmake ARCH=%{target_arch} %{make} LD="$LD" LDFLAGS="$LDFLAGS"
# there are places where parallel make don't work
# usually we use this
%define smake make LD="$LD" LDFLAGS="$LDFLAGS"

###################################################
###  Linker end1 > Check point to build for omv ###
###################################################
# Parallelize xargs invocations on smp machines
%define kxargs xargs %([ -z "$RPM_BUILD_NCPUS" ] \\\
	&& RPM_BUILD_NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"; \\\
	[ "$RPM_BUILD_NCPUS" -gt 1 ] && echo "-P $RPM_BUILD_NCPUS")

# Sparc arch wants sparc64 kernels
%define target_arch    %(echo %{_arch} | sed -e 's/mips.*/mips/' -e 's/arm.*/arm/' -e 's/aarch64/arm64/')

#
# SRC RPM description
#
Summary: 	Linux kernel built for %{distribution}
Name:		kernel-rc
Version:	%{kversion}
Release:	%{rpmrel}
License:	GPLv2
Group:		System/Kernel and hardware
ExclusiveArch:	%{ix86} x86_64 %{armx}
ExclusiveOS:	Linux
URL:		http://www.kernel.org

####################################################################
#
# Sources
#
### This is for full SRC RPM
Source0:	ftp://ftp.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{tar_ver}.tar.xz
Source1:	ftp://ftp.kernel.org/pub/linux/kernel/v%{kernelversion}.x/linux-%{tar_ver}.tar.sign
### This is for stripped SRC RPM
%if %{with build_nosrc}
NoSource:	0
%endif

Source4:	README.kernel-sources
Source5:	kernel-rc.rpmlintrc
# configs
Source6:	common.config
# x86_64
Source7:	x86_64-common.config
Source8:	x86_64-desktop.config
Source9:	x86_64-server.config
# for i586 only desktop flavour
Source10:	i386-desktop.config
# Server flavour for ARMx, todo: add desktop
Source11:	arm64-server.config
Source12:	arm-server.config

# config and systemd service file from fedora
Source50:	cpupower.service
Source51:	cpupower.config

# Patches
# Numbers 0 to 9 are reserved for upstream patches
# (-stable patch, -rc, ...)
%if 0%{relc}
Patch0:		https://cdn.kernel.org/pub/linux/kernel/v4.x/testing/patch-4.6-rc%{relc}.xz
%endif
# aarch64 PCI support (Opteron A1100 and friends)
# Backported from https://github.com/semihalf-nowicki-tomasz/linux.git
# pci-acpi-v5 branch
Patch10:	0001-PCI-ACPI-IA64-fix-IO-port-generic-range-check.patch
Patch16:	0007-irqchip-GICv3-ITS-Refator-ITS-dt-init-code-to-prepar.patch
Patch17:	0008-ARM64-ACPI-PCI-I-O-Remapping-Table-IORT-initial-supp.patch
Patch18:	0009-irqchip-gicv3-its-Probe-ITS-in-the-ACPI-way.patch
Patch19:	0010-acpi-gicv3-msi-Factor-out-code-that-might-be-reused-.patch
Patch20:	0011-acpi-gicv3-its-Use-MADT-ITS-subtable-to-do-PCI-MSI-d.patch
Patch21:	0012-ACPI-MCFG-Move-mmcfg_list-management-to-drivers-acpi.patch
Patch23:	0014-arm64-acpi-Use-MCFG-library-and-empty-PCI-config-spa.patch
Patch24:	0015-pci-acpi-ecam-Add-flag-to-indicate-whether-ECAM-regi.patch
Patch25:	0016-x86-pci-Cleanup-platform-specific-MCFG-data-by-using.patch
Patch26:	0017-pci-acpi-x86-ia64-Move-ACPI-host-bridge-device-compa.patch
Patch27:	0018-pci-acpi-Provide-generic-way-to-assign-bus-domain-nu.patch
Patch28:	0019-x86-ia64-Include-acpi_pci_-add-remove-_bus-to-the-de.patch
Patch29:	0020-acpi-mcfg-Add-default-PCI-config-accessors-implement.patch
Patch30:	0021-pci-of-Move-the-PCI-I-O-space-management-to-PCI-core.patch
Patch31:	0022-drivers-pci-add-generic-code-to-claim-bus-resources.patch
Patch32:	0023-pci-acpi-Support-for-ACPI-based-generic-PCI-host-con.patch
Patch33:	0024-pci-acpi-Match-PCI-config-space-accessors-against-pl.patch
Patch34:	0025-arm64-pci-acpi-Assign-legacy-IRQs-once-device-is-ena.patch
Patch35:	0026-arm64-pci-acpi-Start-using-ACPI-based-PCI-host-bridg.patch
Patch38:	0001-Add-support-for-Acer-Predator-macro-keys.patch

# Defines for the things that are needed for all the kernels
#
%define common_desc_kernel The kernel package contains the Linux kernel (vmlinuz), the core of your \
OpenMandriva Lx operating system. The kernel handles the basic functions \
of the operating system: memory allocation, process allocation, device \
input and output, etc. \
This version is a preview of an upcoming kernel version, and may be helpful if you are using \
very current hardware.


### Global Requires/Provides
%define requires1	microcode_ctl
#%define requires2	dracut >= 026
%define requires3	kmod >= 12
%define requires4	sysfsutils >=  2.1.0-12
%define requires5	kernel-firmware

%define kprovides1	%{kname} = %{kverrel}
%define kprovides2	kernel = %{tar_ver}
%define kprovides_server	drbd-api = 88

%define	kobsoletes1	dkms-r8192se <= 0019.1207.2010-2
%define	kobsoletes2	dkms-lzma <= 4.43-32
%define	kobsoletes3	dkms-psb <= 4.41.1-7

%define kconflicts1	dkms-broadcom-wl < 5.100.82.112-12
%define kconflicts2	dkms-fglrx < 13.200.5-1
%define kconflicts3	dkms-nvidia-current < 325.15-1
%define kconflicts4	dkms-nvidia-long-lived < 319.49-1
%define kconflicts5	dkms-nvidia304 < 304.108-1
# nvidia173 does not support this kernel

Autoreqprov:	no

BuildRequires:	bc
BuildRequires:	binutils
BuildRequires:	gcc
BuildRequires:	openssl-devel
BuildRequires:	diffutils
# For power tools
BuildRequires:	pkgconfig(ncurses)
BuildRequires:	kmod-devel

%ifarch x86_64
BuildRequires:	numa-devel
%endif

# for cpupower
%if %{with build_cpupower}
BuildRequires:	pciutils-devel
%endif

# for docs
%if %{with build_doc}
BuildRequires:	xmlto
%endif

# for perf
%if %{with build_perf}
BuildRequires:	asciidoc
BuildRequires:	audit-devel
BuildRequires:	binutils-devel
BuildRequires:	bison
# BuildRequires:	docbook-style-xsl
BuildRequires:	elfutils-devel
BuildRequires:	flex
# BuildRequires:	gettext
# BuildRequires:	gtk2-devel
BuildRequires:	libunwind-devel
BuildRequires:	newt-devel
BuildRequires:	perl-devel
# BuildRequires:	perl(ExtUtils::Embed)
BuildRequires:	pkgconfig(gtk+-2.0)
BuildRequires:	pkgconfig(python2)
BuildRequires:	zlib-devel
%endif

%ifarch %{arm}
BuildRequires:	uboot-mkimage
%endif

# might be useful too:
Suggests:	microcode_ctl


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
Provides:   %{kname}-%{1}              			 \
Requires(pre):	%requires1 %requires2 %requires3 %requires4 \
Requires:	%requires2 %requires5			\
Obsoletes:	%kobsoletes1 %kobsoletes2 %kobsoletes3	\
Conflicts:	%kconflicts1 %kconflicts2 %kconflicts3	\
Conflicts:	%kconflicts4 %kconflicts5		\
Provides:	should-restart = system			\
Suggests:	crda					\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
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
Requires:	gcc					\
Requires:	perl					\
Summary:	The kernel-devel files for %{kname}-%{1}-%{buildrel} \
Group:		Development/Kernel			\
Provides:	%{kname}-devel = %{kverrel} 		\
Provides:	%{kname}-%{1}-devel			\
Requires:	%{kname}-%{1}-%{buildrel}		\
%ifarch %{ix86}						\
Conflicts:	arch(x86_64)				\
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
Version: 	%{fakever}
Release: 	%{fakerel}
Requires: 	glibc-devel
Requires: 	ncurses-devel
Requires: 	make
Requires: 	gcc
Requires: 	perl
Requires: 	diffutils
Summary: 	The Linux source code for %{kname}-%{buildrel}
Group: 		Development/Kernel
Autoreqprov: 	no
Provides: 	kernel-source = %{kverrel}
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
Requires(post): 	rpm-helper >= 0.24.0-3
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

%package headers
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Linux kernel header files mostly used by your C library
Group:		System/Kernel and hardware
Epoch:		1
# (tpg) fix bug https://issues.openmandriva.org/show_bug.cgi?id=1580
Provides:	kernel-headers = %{kverrel}
# we don't need whole kernel in chroot
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

%package -n cross-%{name}-headers
Version:	%{kversion}
Release:	%{rpmrel}
Summary:	Linux kernel header files for cross toolchains
Group:		System/Kernel and hardware
Epoch:		1
BuildArch:	noarch

%description -n	cross-%{name}-headers
C header files from the Linux kernel. The header files define
structures and constants that are needed for building most
standard programs, notably the C library.

This package is only of interest if you're cross-compiling for one of the
following platforms:
%{cross_header_archs}

%files -n cross-%{name}-headers
%{_prefix}/*-%{_target_os}/include/*

# %endif (???)
# from 1486-1505 >https://abf.io/openmandriva/kernel/commit/b967a6b9458236d594dac87de97193f0e172c55c
# endif should be wrong, that is not an %if before...

#
# End packages - here begins build stage
#
%prep
%setup -q -n linux-%{tar_ver}
%apply_patches

%if %{with build_debug}
%define debug --debug
%else
%define debug --no-debug
%endif

# make sure the kernel has the sublevel we know it has...
LC_ALL=C perl -p -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{sublevel}/" Makefile

# get rid of unwanted files
find . -name '*~' -o -name '*.orig' -o -name '*.append' | %kxargs rm -f
# wipe all .gitignore/.get_maintainer.ignore files
find . -name "*.g*ignore" -exec rm {} \;

%build
%setup_compile_flags
############################################################
### Linker start2 > Check point to build for omv or rosa ###
############################################################
# Make sure we don't use gold
export LD="%{_target_platform}-ld.bfd"
export LDFLAGS="--hash-style=sysv --build-id=none"
export PYTHON=%{__python2}

############################################################
###  Linker end2 > Check point to build for omv or rosa ###
############################################################
# Common target directories
%define _kerneldir /usr/src/linux-%{kversion}-%{buildrpmrel}
%define _bootdir /boot
%define _modulesdir /lib/modules
%define _efidir %{_bootdir}/efi/mandriva

# Directories definition needed for building
%define temp_root %{build_dir}/temp-root
%define temp_source %{temp_root}%{_kerneldir}
%define temp_boot %{temp_root}%{_bootdir}
%define temp_modules %{temp_root}%{_modulesdir}

PrepareKernel() {
    name=$1
    extension=$2
    config_dir=%{_sourcedir}
    echo "Make config for kernel $extension"
    %{smake} -s mrproper
    cat ${config_dir}/common.config ${config_dir}/common-$flavour.config ${config_dir}/%{target_arch}-common.config ${config_dir}/%{target_arch}-$flavour.config >.config 2>/dev/null || :
    # make sure EXTRAVERSION says what we want it to say
    sed -ri "s|^(EXTRAVERSION =).*|\1 -$extension|" Makefile
    %{smake} oldconfig
}

BuildKernel() {
    KernelVer=$1
    echo "Building kernel $KernelVer"
# (tpg) build with gcc, as kernel is not yet ready for LLVM/clang
%ifarch x86_64
    %kmake all CC=gcc CXX=g++ CFLAGS="$CFLAGS -fwhole-program -flto" LDFLAGS="$LDFLAGS -flto"
%else
    %kmake all CC=gcc CXX=g++ CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS"
%endif

# Start installing stuff
    install -d %{temp_boot}
    install -m 644 System.map %{temp_boot}/System.map-$KernelVer
    install -m 644 .config %{temp_boot}/config-$KernelVer
    xz -7 -T0 -c Module.symvers > %{temp_boot}/symvers-$KernelVer.xz

%ifarch %{arm}
    if [ -f arch/arm/boot/uImage ]; then
	cp -f arch/arm/boot/uImage %{temp_boot}/uImage-$KernelVer
    else
	cp -f arch/arm/boot/zImage %{temp_boot}/vmlinuz-$KernelVer
    fi
%else
    cp -f arch/%{target_arch}/boot/bzImage %{temp_boot}/vmlinuz-$KernelVer
%endif

# modules
    install -d %{temp_modules}/$KernelVer
    %{smake} INSTALL_MOD_PATH=%{temp_root} KERNELRELEASE=$KernelVer INSTALL_MOD_STRIP=1 modules_install

# headers
    %{make} INSTALL_HDR_PATH=%{temp_root}%_prefix KERNELRELEASE=$KernelVer headers_install

# kernel headers for cross toolchains
%ifarch %{armx}
    %{smake} ARCH=%{target_arch} V=1 dtbs INSTALL_DTBS_PATH=%{temp_boot}/dtb-$KernelVer dtbs_install
%endif

    for arch in %{cross_header_archs}; do
	%{make} SRCARCH=$arch INSTALL_HDR_PATH=%{temp_root}%{_prefix}/$arch-%{_target_os} KERNELRELEASE=$KernelVer headers_install
    done

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
    cp -fR Documentation/DocBook/media/*.b64 $TempDevelRoot/Documentation/DocBook/media/
    cp -fR include $TempDevelRoot
#     ln -s ../generated/uapi/linux/version.h $TempDevelRoot/include/linux/version.h
    cp -fR scripts $TempDevelRoot
    cp -fR kernel/time/timeconst.bc $TempDevelRoot/kernel/time/
    cp -fR kernel/bounds.c $TempDevelRoot/kernel
    cp -fR tools/include $TempDevelRoot/tools/
%ifarch %{arm}
    cp -fR arch/%{target_arch}/tools $TempDevelRoot/arch/%{target_arch}/
%endif

%ifarch %{ix86} x86_64
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

# Needed for lguest
    cp -fR drivers/lguest/lg.h $TempDevelRoot/drivers/lguest/

# Needed for lirc_gpio (#39004)
    cp -fR drivers/media/pci/bt8xx/bttv{,p}.h $TempDevelRoot/drivers/media/pci/bt8xx/
    cp -fR drivers/media/pci/bt8xx/bt848.h $TempDevelRoot/drivers/media/pci/bt8xx/
    cp -fR drivers/media/common/btcx-risc.h $TempDevelRoot/drivers/media/common/

# Needed for external dvb tree (#41418)
    cp -fR drivers/media/dvb-core/*.h $TempDevelRoot/drivers/media/dvb-core/
    cp -fR drivers/media/dvb-frontends/lgdt330x.h $TempDevelRoot/drivers/media/dvb-frontends/

# add acpica header files, needed for fglrx build
    cp -fR drivers/acpi/acpica/*.h $TempDevelRoot/drivers/acpi/acpica/

    for i in alpha arc avr32 blackfin c6x cris frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
		 mips mn10300 nios2 openrisc parisc powerpc s390 score sh sparc tile unicore32 xtensa; do
		rm -rf $TempDevelRoot/arch/$i
    done

%ifnarch %{arm}
    rm -rf $TempDevelRoot/arch/arm*
    rm -rf $TempDevelRoot/include/kvm/arm*
    rm -rf $TempDevelRoot/include/soc
%endif

# Clean the scripts tree, and make sure everything is ok (sanity check)
# running prepare+scripts (tree was already "prepared" in build)
    pushd $TempDevelRoot >/dev/null
    %{smake} ARCH=%{target_arch} prepare scripts
    %{smake} ARCH=%{target_arch} clean
    popd >/dev/null

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
%ifarch %{armx}
$DevelRoot/arch/arm
$DevelRoot/arch/arm64
%endif
$DevelRoot/arch/um
$DevelRoot/arch/x86
$DevelRoot/block
$DevelRoot/crypto
# here
$DevelRoot/certs
$DevelRoot/drivers
$DevelRoot/firmware
$DevelRoot/fs
$DevelRoot/include/Kbuild
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
$DevelRoot/include/rxrpc
$DevelRoot/include/scsi
%ifarch %{arm}
$DevelRoot/include/soc
%endif
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

    pushd %{temp_modules}
    find %{kversion}-$debug_flavour-%{buildrpmrel}/kernel -name "*.ko.debug" > debug_module_list
    popd
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
%{_bootdir}/symvers-%{kversion}-$kernel_flavour-%{buildrpmrel}.xz
%{_bootdir}/config-%{kversion}-$kernel_flavour-%{buildrpmrel}
%{_bootdir}/$ker-%{kversion}-$kernel_flavour-%{buildrpmrel}
# device tree binary
%ifarch %{armx}
%{_bootdir}/dtb-%{kversion}-$kernel_flavour-%{buildrpmrel}
%endif
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
pushd /boot > /dev/null
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

popd > /dev/null
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
pushd /boot > /dev/null
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
popd > /dev/null
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


###
# DO it...
###


# Create a simulacro of buildroot
rm -rf %{temp_root}
install -d %{temp_root}

%if %{with build_desktop}
CreateKernel desktop
%endif

%if %{with build_server}
CreateKernel server
%endif

# how to build own flavour
# %if %build_nrjQL_desktop
# CreateKernel nrjQL-desktop
# %endif

# set extraversion to match srpm to get nice version reported by the tools
#LC_ALL=C perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{rpmrel}/" Makefile
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{rpmrel}|" Makefile

############################################################
### Linker start3 > Check point to build for omv or rosa ###
############################################################
%if %{with build_perf}
%{smake} -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 CC=%{__cc} PYTHON=%{__python2} WERROR=0 LDFLAGS="-Wl,--hash-style=sysv -Wl,--build-id=none" prefix=%{_prefix} all
%{smake} -C tools/perf -s CC=%{__cc} prefix=%{_prefix} PYTHON=%{__python2} man
%endif

%if %{with build_cpupower}
# make sure version-gen.sh is executable.
chmod +x tools/power/cpupower/utils/version-gen.sh
%kmake -C tools/power/cpupower CPUFREQ_BENCH=false LDFLAGS="%{optflags}"
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

# Create directories infastructure
%if %{with build_source}
install -d %{target_source}
tar cf - . | tar xf - -C %{target_source}
chmod -R a+rX %{target_source}

# File lists aren't needed
rm -f %{target_source}/*_files.* %{target_source}/README.kernel-sources

# we remove all the source files that we don't ship
# first architecture files
for i in alpha arc avr32 blackfin c6x cris frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
	 mips nios2 openrisc parisc powerpc s390 score sh sh64 sparc tile unicore32 v850 xtensa mn10300; do
	rm -rf %{target_source}/arch/$i
done
%ifnarch %{arm}
    rm -rf %{target_source}/include/kvm/arm*
%endif

# other misc files
rm -f %{target_source}/{.config.old,.config.cmd,.gitignore,.lst,.mailmap}
rm -f %{target_source}/{.missing-syscalls.d,arch/.gitignore,firmware/.gitignore}
rm -rf %{target_source}/.tmp_depmod/

#endif %{with build_source}
%endif

# compressing modules
%if %{with build_modxz}
find %{target_modules} -name "*.ko" | %kxargs xz -6e -T0
%else
find %{target_modules} -name "*.ko" | %kxargs gzip -9
%endif

# We used to have a copy of PrepareKernel here
# Now, we make sure that the thing in the linux dir is what we want it to be
for i in %{target_modules}/*; do
    rm -f $i/build $i/source
done

# sniff, if we compressed all the modules, we change the stamp :(
# we really need the depmod -ae here
pushd %{target_modules}
for i in *; do
    /sbin/depmod -ae -b %{buildroot} -F %{target_boot}/System.map-$i $i
    echo $?
done

for i in *; do
    pushd $i
    echo "Creating modules.description for $i"
    modules=`find . -name "*.ko.[gx]z"`
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
%{_kerneldir}/Documentation
%{_kerneldir}/arch/Kconfig
%{_kerneldir}/arch/arm
%{_kerneldir}/arch/arm64
%{_kerneldir}/arch/um
%{_kerneldir}/arch/x86
%{_kerneldir}/block
%{_kerneldir}/crypto
%{_kerneldir}/drivers
%{_kerneldir}/firmware
%{_kerneldir}/fs
%{_kerneldir}/certs/*
%{_kerneldir}/include/Kbuild
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
%{_kerneldir}/include/rxrpc
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
%{_kerneldir}/MAINTAINERS
%{_kerneldir}/Makefile
%{_kerneldir}/README
%{_kerneldir}/REPORTING-BUGS

%files -n %{kname}-source-latest
%endif

%if %{with build_doc}
%files -n %{kname}-doc
%doc Documentation/*
%endif

%if %{with build_perf}
%files -n perf
%{_bindir}/perf
%ifarch x86_64
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
%{_libdir}/libcpupower.so.0.0.0
%{_unitdir}/cpupower.service
%{_mandir}/man[1-8]/cpupower*
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower

%files -n cpupower-devel
%{_libdir}/libcpupower.so
%{_includedir}/cpufreq.h
%endif
