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
# (tpg) use LLVM/polly for polyhedra optimization and automatic vector code generation
# based on https://lore.kernel.org/lkml/20210120174146.12287-1-lazerl0rd@thezest.dev/
%define pollyflags %{nil}
#-mllvm -polly -mllvm -polly-run-dce -mllvm -polly-run-inliner -mllvm -polly-reschedule=1 -mllvm -polly-loopfusion-greedy=1 -mllvm -polly-postopts=1 -mllvm -polly-ast-use-context -mllvm -polly-detect-keep-going -mllvm -polly-vectorizer=stripmine -mllvm -polly-invariant-load-hoisting
%else
%define pollyflags %{nil}
%endif

## STOP: Adding weird and unsupported upstream kernel C/LD flags of any sort
## yes , including ftlo . O3 and whatever else

# Disable useless debug rpms as we generate our own debug package
%define _enable_debug_packages %{nil}
%define debug_package %{nil}
%global __debug_package %{nil}
%global __debug_install_post %{nil}
%global _build_id_links none

# Work around incomplete debug packages
%global _empty_manifest_terminate_build 0

%global cross_header_archs aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv32-linuxmusl riscv64-linuxmusl aarch64-android armv7l-android armv8l-android x86_64-android aarch64-linuxuclibc armv7hnl-linuxuclibc i686-linuxuclibc x86_64-linuxuclibc x32-linuxuclibc riscv32-linuxuclibc riscv64-linuxuclibc ppc64le-linux ppc64-linux ppc64le-linuxmusl ppc64-linuxmusl ppc64le-linuxuclibc ppc64-linuxuclibc loongarch64-linux loongarch64-linuxmusl loongarch64-linuxuclibc
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

%define target_arch %(echo %{_arch} | sed -e 's/mips.*/mips/' -e 's/arm.*/arm/' -e 's/aarch64/arm64/' -e 's/x86_64/x86/' -e 's/i.86/x86/' -e 's/znver1/x86/' -e 's/riscv.*/riscv/' -e 's/ppc.*/powerpc/' -e 's/loongarch64/loongarch/')

# Kernel flavours as bconds. rpm does not accept hyphens in bcond names,
# so the gcc flavours are desktop_gcc / server_gcc (--without desktop_gcc).
# Flavour strings in the build remain desktop-gcc / server-gcc.
# Defaults match the previous per-arch list (LoongArch has no gcc yet).
%bcond_without desktop
%bcond_without server
%ifarch %{loongarch64}
%bcond_with desktop_gcc
%bcond_with server_gcc
%else
%bcond_without desktop_gcc
%bcond_without server_gcc
%endif
%if %{with desktop}
%global kf_desktop desktop
%endif
%if %{with server}
%global kf_server server
%endif
%if %{with desktop_gcc}
%global kf_desktop_gcc desktop-gcc
%endif
%if %{with server_gcc}
%global kf_server_gcc server-gcc
%endif
%define kernel_flavours %{?kf_desktop} %{?kf_server} %{?kf_desktop_gcc} %{?kf_server_gcc}

# Rarely used modules → separate kernel-*-modules-* subpackages (see install loop).
# Token forms:
#   name           directory basename under .../kernel/ (e.g. jfs, firewire)
#   path/to/dir    path suffix, so sound/soc/qcom does not steal drm/qcom
#   foo.ko         exact module basename
#   src=pkg        map any of the above onto package kernel-*-modules-pkg
#
# Keep everyday hardware in the main package (USB, common Wi‑Fi, webcams/V4L,
# NVMe/AHCI, HDA/SOF laptop audio, etc.). Split only niche protocols, legacy
# buses, DVB/TV, staging, embedded-SoC audio, and odd firmware-bound drivers.

# Rare / legacy filesystems
# 7.3 removed appletalk, efs and freevxfs
%global modules_subpackages can adfs affs afs befs bfs coda cramfs gfs2 hfs hfsplus hpfs jffs2 jfs minix nilfs2 ocfs2 omfs orangefs qnx4 qnx6 romfs ubifs ufs zonefs zd1211rw

# Rare networking (ATM kept available for legacy PPPoA/ADSL; not needed for PPPoE)
%global modules_subpackages %{modules_subpackages} atm sctp rds tipc hsr batman-adv x25 phonet caif nfc 6lowpan ieee802154 mac802154 openvswitch fddi arcnet isdn

# Legacy / industrial / hobbyist hardware classes
%global modules_subpackages %{modules_subpackages} firewire pcmcia parport comedi infiniband fpga greybus rapidio gnss w1 uio most siox auxdisplay accessibility staging

# DVB / digital TV / FM radio only — leave media core + UVC webcams in main
%global modules_subpackages %{modules_subpackages} dvb-core dvb-frontends dvb-usb tuners radio
# Pre-UVC gspca webcams (not common anymore). Package: kernel-*-modules-gspca
%global modules_subpackages %{modules_subpackages} gspca

# Specialized accelerators (not everyday laptop NPUs)
%global modules_subpackages %{modules_subpackages} habanalabs

# ASoC platform drivers for embedded SoCs (SBCs, phones, FPGA). Path tokens
# match only sound/soc/<vendor>. Package: kernel-*-modules-snd-soc-<vendor>.
# Left in the main image: amd / intel / sof (x86 laptops), qcom (Snapdragon X
# Elite), apple (Macs), loongson (everyday on loongarch), plus codecs/generic/
# sdca/sdw_utils (shared laptop codecs and simple-card).
%global modules_subpackages %{modules_subpackages} sound/soc/adi sound/soc/atmel sound/soc/au1x sound/soc/bcm sound/soc/cirrus sound/soc/dwc sound/soc/fsl sound/soc/google sound/soc/hisilicon sound/soc/img sound/soc/jz4740 sound/soc/kirkwood sound/soc/mediatek sound/soc/meson sound/soc/mxs sound/soc/pxa sound/soc/renesas sound/soc/rockchip sound/soc/samsung sound/soc/sophgo sound/soc/spacemit sound/soc/spear sound/soc/sprd sound/soc/starfive sound/soc/sti sound/soc/stm sound/soc/sunxi sound/soc/tegra sound/soc/ti sound/soc/uniphier sound/soc/ux500 sound/soc/xilinx sound/soc/xtensa

# Codecs that only exist on those SoCs (they live in sound/soc/codecs/)
%global modules_subpackages %{modules_subpackages} snd-soc-mt6351.ko=snd-soc-mediatek snd-soc-mt6357.ko=snd-soc-mediatek snd-soc-mt6358.ko=snd-soc-mediatek snd-soc-mt6359.ko=snd-soc-mediatek snd-soc-mt6660.ko=snd-soc-mediatek snd-soc-chv3-codec.ko=snd-soc-google snd-soc-sti-sas.ko=snd-soc-sti

%ifarch %{aarch64} %{x86_64}
%global modules_subpackages %{modules_subpackages} nvidia
%endif

# Nouveau is split so NVIDIA-proprietary users can uninstall it. The main
# flavour package Requires it for now so existing nouveau setups keep working.
%global modules_subpackages %{modules_subpackages} nouveau

# Industrial / eval-board IIO (ADC/DAC/chemical/…). Laptop bits stay in main:
# industrialio core, hid-sensor-*, Cros EC, ACPI ALS, ST LSM6DSx, BMI160/270/323,
# BMC150, KXCJK-1013.
%global modules_subpackages %{modules_subpackages} iio/adc=iio iio/dac=iio iio/addac=iio iio/afe=iio iio/amplifiers=iio iio/cdc=iio iio/chemical=iio iio/filter=iio iio/frequency=iio iio/health=iio iio/potentiometer=iio iio/potentiostat=iio iio/resolver=iio iio/multiplexer=iio

# Mixed IIO class drivers that are not laptop HID/Cros-EC/common IMUs
%global modules_subpackages %{modules_subpackages} abp060mg.ko=iio abp2030pa.ko=iio abp2030pa_i2c.ko=iio abp2030pa_spi.ko=iio adis16080.ko=iio adis16130.ko=iio adis16136.ko=iio adis16201.ko=iio adis16209.ko=iio adis16260.ko=iio
%global modules_subpackages %{modules_subpackages} adis16400.ko=iio adis16460.ko=iio adis16475.ko=iio adis16480.ko=iio adis16550.ko=iio adis_lib.ko=iio adjd_s311.ko=iio adp810.ko=iio adux1020.ko=iio adxl313_core.ko=iio adxl313_i2c.ko=iio adxl313_spi.ko=iio
%global modules_subpackages %{modules_subpackages} adxl345_core.ko=iio adxl345_i2c.ko=iio adxl345_spi.ko=iio adxl355_core.ko=iio adxl355_i2c.ko=iio adxl355_spi.ko=iio adxl367.ko=iio adxl367_i2c.ko=iio adxl367_spi.ko=iio adxl372.ko=iio adxl372_i2c.ko=iio adxl372_spi.ko=iio
%global modules_subpackages %{modules_subpackages} adxl380.ko=iio adxl380_i2c.ko=iio adxl380_spi.ko=iio adxrs290.ko=iio adxrs450.ko=iio af8133j.ko=iio ak8974.ko=iio ak8975.ko=iio al3000a.ko=iio al3010.ko=iio al3320a.ko=iio als31300.ko=iio
%global modules_subpackages %{modules_subpackages} am2315.ko=iio apds9160.ko=iio apds9300.ko=iio apds9306.ko=iio apds9960.ko=iio apds9999.ko=iio as3935.ko=iio as73211.ko=iio aw96103.ko=iio bh1745.ko=iio bh1750.ko=iio bh1780.ko=iio
%global modules_subpackages %{modules_subpackages} bma180.ko=iio bma220_core.ko=iio bma220_i2c.ko=iio bma220_spi.ko=iio bma400_core.ko=iio bma400_i2c.ko=iio bma400_spi.ko=iio bmc150_magn.ko=iio bmc150_magn_i2c.ko=iio bmc150_magn_spi.ko=iio bmg160_core.ko=iio bmg160_i2c.ko=iio
%global modules_subpackages %{modules_subpackages} bmg160_spi.ko=iio bmi088-accel-core.ko=iio bmi088-accel-i2c.ko=iio bmi088-accel-spi.ko=iio bmi160_core.ko=iio bmi270_core.ko=iio bmi323_core.ko=iio bmp280.ko=iio bmp280-i2c.ko=iio bmp280-spi.ko=iio bno055.ko=iio bno055_i2c.ko=iio
%global modules_subpackages %{modules_subpackages} bno055_ser.ko=iio cm32181.ko=iio cm3232.ko=iio cm3323.ko=iio cm3605.ko=iio cm36651.ko=iio d3323aa.ko=iio da280.ko=iio da311.ko=iio dht11.ko=iio dlhl60d.ko=iio dmard06.ko=iio
%global modules_subpackages %{modules_subpackages} dmard09.ko=iio dmard10.ko=iio dps310.ko=iio ens210.ko=iio fxas21002c_core.ko=iio fxas21002c_i2c.ko=iio fxas21002c_spi.ko=iio fxls8962af-core.ko=iio fxls8962af-i2c.ko=iio fxls8962af-spi.ko=iio fxos8700_core.ko=iio fxos8700_i2c.ko=iio
%global modules_subpackages %{modules_subpackages} fxos8700_spi.ko=iio gp2ap002.ko=iio gp2ap020a00f.ko=iio hdc100x.ko=iio hdc2010.ko=iio hdc3020.ko=iio hmc5843_core.ko=iio hmc5843_i2c.ko=iio hmc5843_spi.ko=iio hp03.ko=iio hp206c.ko=iio hsc030pa.ko=iio
%global modules_subpackages %{modules_subpackages} hsc030pa_i2c.ko=iio hsc030pa_spi.ko=iio hts221.ko=iio hts221_i2c.ko=iio hts221_spi.ko=iio htu21.ko=iio hx9023s.ko=iio icp10100.ko=iio inv-icm42600.ko=iio inv-icm42600-i2c.ko=iio inv-icm42600-spi.ko=iio inv-icm45600.ko=iio
%global modules_subpackages %{modules_subpackages} inv-icm45600-i2c.ko=iio inv-icm45600-i3c.ko=iio inv-icm45600-spi.ko=iio inv-mpu6050.ko=iio inv-mpu6050-i2c.ko=iio inv-mpu6050-spi.ko=iio inv_sensors_timestamp.ko=iio iqs620at-temp.ko=iio iqs621-als.ko=iio iqs624-pos.ko=iio irsd200.ko=iio isl29018.ko=iio
%global modules_subpackages %{modules_subpackages} isl29028.ko=iio isl29125.ko=iio isl29501.ko=iio isl76682.ko=iio itg3200.ko=iio jsa1212.ko=iio kionix-kx022a.ko=iio kionix-kx022a-i2c.ko=iio kionix-kx022a-spi.ko=iio kmx61.ko=iio kxsd9.ko=iio kxsd9-i2c.ko=iio
%global modules_subpackages %{modules_subpackages} kxsd9-spi.ko=iio lm3533-als.ko=iio ltc2983.ko=iio ltr390.ko=iio ltr501.ko=iio ltrf216a.ko=iio lv0104cs.ko=iio mag3110.ko=iio max30208.ko=iio max31856.ko=iio max31865.ko=iio max44000.ko=iio
%global modules_subpackages %{modules_subpackages} max44009.ko=iio maxim_thermocouple.ko=iio mb1232.ko=iio mc3230.ko=iio mcp9600.ko=iio mlx90614.ko=iio mlx90632.ko=iio mlx90635.ko=iio mma7455_core.ko=iio mma7455_i2c.ko=iio mma7455_spi.ko=iio mma7660.ko=iio
%global modules_subpackages %{modules_subpackages} mma8452.ko=iio mma9551.ko=iio mma9551_core.ko=iio mma9553.ko=iio mmc35240.ko=iio mmc5633.ko=iio mmc5983.ko=iio mpl115.ko=iio mpl115_i2c.ko=iio mpl115_spi.ko=iio mpl3115.ko=iio mprls0025pa.ko=iio
%global modules_subpackages %{modules_subpackages} mprls0025pa_i2c.ko=iio mprls0025pa_spi.ko=iio mpu3050.ko=iio ms5611_core.ko=iio ms5611_i2c.ko=iio ms5611_spi.ko=iio ms5637.ko=iio ms_sensors_i2c.ko=iio msa311.ko=iio mxc4005.ko=iio mxc6255.ko=iio noa1305.ko=iio
%global modules_subpackages %{modules_subpackages} opt3001.ko=iio opt4001.ko=iio opt4060.ko=iio pa12203001.ko=iio ping.ko=iio pulsedlight-lidar-lite-v2.ko=iio rfd77402.ko=iio rm3100-core.ko=iio rm3100-i2c.ko=iio rm3100-spi.ko=iio rohm-bm1390.ko=iio rohm-bu27034.ko=iio
%global modules_subpackages %{modules_subpackages} rpr0521.ko=iio sca3000.ko=iio sca3300.ko=iio scmi_iio.ko=iio sdp500.ko=iio sensorhub.ko=iio si1133.ko=iio si1145.ko=iio si7005.ko=iio si7020.ko=iio si7210.ko=iio smi240.ko=iio
%global modules_subpackages %{modules_subpackages} smi330_core.ko=iio smi330_i2c.ko=iio smi330_spi.ko=iio srf04.ko=iio srf08.ko=iio ssp_accel_sensor.ko=iio ssp_gyro_sensor.ko=iio ssp_iio.ko=iio st_accel.ko=iio st_accel_i2c.ko=iio st_accel_spi.ko=iio st_gyro.ko=iio
%global modules_subpackages %{modules_subpackages} st_gyro_i2c.ko=iio st_gyro_spi.ko=iio st_lsm9ds0.ko=iio st_lsm9ds0_i2c.ko=iio st_lsm9ds0_spi.ko=iio st_magn.ko=iio st_magn_i2c.ko=iio st_magn_spi.ko=iio st_pressure.ko=iio st_pressure_i2c.ko=iio st_pressure_spi.ko=iio st_uvis25_core.ko=iio
%global modules_subpackages %{modules_subpackages} st_uvis25_i2c.ko=iio st_uvis25_spi.ko=iio stk3310.ko=iio stk8312.ko=iio stk8ba50.ko=iio sx9310.ko=iio sx9324.ko=iio sx9360.ko=iio sx9500.ko=iio sx_common.ko=iio t5403.ko=iio tcs3414.ko=iio
%global modules_subpackages %{modules_subpackages} tcs3472.ko=iio tlv493d.ko=iio tmag5273.ko=iio tmp006.ko=iio tmp007.ko=iio tmp117.ko=iio tsl2563.ko=iio tsl2583.ko=iio tsl2591.ko=iio tsl2772.ko=iio tsl4531.ko=iio tsys01.ko=iio
%global modules_subpackages %{modules_subpackages} tsys02d.ko=iio us5182d.ko=iio vcnl3020.ko=iio vcnl4000.ko=iio vcnl4035.ko=iio veml3235.ko=iio veml3328.ko=iio veml6030.ko=iio veml6040.ko=iio veml6046x00.ko=iio veml6070.ko=iio veml6075.ko=iio
%global modules_subpackages %{modules_subpackages} vl53l0x-i2c.ko=iio vl53l1x-i2c.ko=iio vl6180.ko=iio yamaha-yas530.ko=iio zopt2201.ko=iio zpa2326.ko=iio zpa2326_i2c.ko=iio zpa2326_spi.ko=iio
%global modules_subpackages %{modules_subpackages} inv-icm42607-i2c.ko=iio inv-icm42607-spi.ko=iio qmc5883l.ko=iio qmc6308.ko=iio ltc2378.ko=iio adf41513.ko=iio mcp47a1.ko=iio ti-ads112c14.ko=iio slf3s.ko=iio

# Industrial / PMBus / eval-board hwmon. Desktop Super-I/O, CPU, vendor
# (ASUS/Gigabyte/Corsair/NZXT), Mac, Chromebook and common I2C temps stay in main.
%global modules_subpackages %{modules_subpackages} acbel-fsg032.ko=hwmon-extra ad7314.ko=hwmon-extra ad7414.ko=hwmon-extra ad7418.ko=hwmon-extra adc128d818.ko=hwmon-extra adcxx.ko=hwmon-extra adm1025.ko=hwmon-extra adm1026.ko=hwmon-extra adm1029.ko=hwmon-extra adm1031.ko=hwmon-extra adm1177.ko=hwmon-extra adm1266.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} adm1275.ko=hwmon-extra adm9240.ko=hwmon-extra adp1050.ko=hwmon-extra ads7828.ko=hwmon-extra ads7871.ko=hwmon-extra adt7310.ko=hwmon-extra adt7410.ko=hwmon-extra adt7411.ko=hwmon-extra adt7462.ko=hwmon-extra adt7470.ko=hwmon-extra adt7475.ko=hwmon-extra adt7x10.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} aht10.ko=hwmon-extra amc6821.ko=hwmon-extra aps-379.ko=hwmon-extra arctic_fan_controller.ko=hwmon-extra as370-hwmon.ko=hwmon-extra asb100.ko=hwmon-extra asc7621.ko=hwmon-extra aspeed-g6-pwm-tach.ko=hwmon-extra aspeed-pwm-tacho.ko=hwmon-extra atxp1.ko=hwmon-extra axi-fan-control.ko=hwmon-extra bel-pfe.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} bpa-rs600.ko=hwmon-extra cgbc-hwmon.ko=hwmon-extra chipcap2.ko=hwmon-extra crps.ko=hwmon-extra d1u74t.ko=hwmon-extra da9052-hwmon.ko=hwmon-extra da9055-hwmon.ko=hwmon-extra delta-ahe50dc-fan.ko=hwmon-extra dps920ab.ko=hwmon-extra ds1621.ko=hwmon-extra ds620.ko=hwmon-extra e50sn12051.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} emc1403.ko=hwmon-extra emc1812.ko=hwmon-extra emc2103.ko=hwmon-extra emc2305.ko=hwmon-extra emc6w201.ko=hwmon-extra fsp-3y.ko=hwmon-extra ftsteutates.ko=hwmon-extra g760a.ko=hwmon-extra g762.ko=hwmon-extra gl518sm.ko=hwmon-extra gl520sm.ko=hwmon-extra gsc-hwmon.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} gxp-fan-ctrl.ko=hwmon-extra hac300s.ko=hwmon-extra hih6130.ko=hwmon-extra hs3001.ko=hwmon-extra htu31.ko=hwmon-extra ibm-cffps.ko=hwmon-extra ibmaem.ko=hwmon-extra ibmpex.ko=hwmon-extra ibmpowernv.ko=hwmon-extra iio_hwmon.ko=hwmon-extra ina209.ko=hwmon-extra ina233.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} ina238.ko=hwmon-extra ina2xx.ko=hwmon-extra ina3221.ko=hwmon-extra inspur-ipsps.ko=hwmon-extra intel-m10-bmc-hwmon.ko=hwmon-extra ir35221.ko=hwmon-extra ir36021.ko=hwmon-extra ir38064.ko=hwmon-extra irps5401.ko=hwmon-extra isl28022.ko=hwmon-extra isl68137.ko=hwmon-extra kbatt.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} kfan.ko=hwmon-extra lan966x-hwmon.ko=hwmon-extra lattepanda-sigma-ec.ko=hwmon-extra lineage-pem.ko=hwmon-extra lm25066.ko=hwmon-extra lm70.ko=hwmon-extra lm73.ko=hwmon-extra lm77.ko=hwmon-extra lm78.ko=hwmon-extra lm80.ko=hwmon-extra lm83.ko=hwmon-extra lm93.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} lm95234.ko=hwmon-extra lm95241.ko=hwmon-extra lm95245.ko=hwmon-extra lochnagar-hwmon.ko=hwmon-extra lt3074.ko=hwmon-extra lt7182s.ko=hwmon-extra ltc2945.ko=hwmon-extra ltc2947-core.ko=hwmon-extra ltc2947-i2c.ko=hwmon-extra ltc2947-spi.ko=hwmon-extra ltc2978.ko=hwmon-extra ltc2990.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} ltc2991.ko=hwmon-extra ltc2992.ko=hwmon-extra ltc3815.ko=hwmon-extra ltc4151.ko=hwmon-extra ltc4215.ko=hwmon-extra ltc4222.ko=hwmon-extra ltc4245.ko=hwmon-extra ltc4260.ko=hwmon-extra ltc4261.ko=hwmon-extra ltc4282.ko=hwmon-extra ltc4283.ko=hwmon-extra ltc4286.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} ltq-cputemp.ko=hwmon-extra lx1308.ko=hwmon-extra max1111.ko=hwmon-extra max127.ko=hwmon-extra max15301.ko=hwmon-extra max16064.ko=hwmon-extra max16065.ko=hwmon-extra max1619.ko=hwmon-extra max16601.ko=hwmon-extra max1668.ko=hwmon-extra max17616.ko=hwmon-extra max197.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} max20730.ko=hwmon-extra max20751.ko=hwmon-extra max20830.ko=hwmon-extra max20860a.ko=hwmon-extra max31722.ko=hwmon-extra max31730.ko=hwmon-extra max31760.ko=hwmon-extra max31785.ko=hwmon-extra max31790.ko=hwmon-extra max31827.ko=hwmon-extra max34440.ko=hwmon-extra max6620.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} max6621.ko=hwmon-extra max6639.ko=hwmon-extra max6650.ko=hwmon-extra max6697.ko=hwmon-extra max77705-hwmon.ko=hwmon-extra max8688.ko=hwmon-extra mc13783-adc.ko=hwmon-extra mc33xs2410_hwmon.ko=hwmon-extra mc34vr500.ko=hwmon-extra mcp3021.ko=hwmon-extra mcp9982.ko=hwmon-extra menf21bmc_hwmon.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} mlxreg-fan.ko=hwmon-extra mp2856.ko=hwmon-extra mp2869.ko=hwmon-extra mp2888.ko=hwmon-extra mp2891.ko=hwmon-extra mp2925.ko=hwmon-extra mp29502.ko=hwmon-extra mp2975.ko=hwmon-extra mp2985.ko=hwmon-extra mp2993.ko=hwmon-extra mp5023.ko=hwmon-extra mp5920.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} mp5926.ko=hwmon-extra mp5990.ko=hwmon-extra mp9941.ko=hwmon-extra mp9945.ko=hwmon-extra mpq7932.ko=hwmon-extra mpq8785.ko=hwmon-extra mr75203.ko=hwmon-extra npcm750-pwm-fan.ko=hwmon-extra nsa320-hwmon.ko=hwmon-extra occ-hwmon-common.ko=hwmon-extra occ-p8-hwmon.ko=hwmon-extra occ-p9-hwmon.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} pcf8591.ko=hwmon-extra peci-cputemp.ko=hwmon-extra peci-dimmtemp.ko=hwmon-extra pim4328.ko=hwmon-extra pli1209bc.ko=hwmon-extra pm6764tr.ko=hwmon-extra pmbus.ko=hwmon-extra powerz.ko=hwmon-extra powr1220.ko=hwmon-extra prom21-xhci.ko=hwmon-extra pt5161l.ko=hwmon-extra pxe1610.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} q54sj108a2.ko=hwmon-extra qnap-mcu-hwmon.ko=hwmon-extra raspberrypi-hwmon.ko=hwmon-extra sbtsi_temp.ko=hwmon-extra scmi-hwmon.ko=hwmon-extra scpi-hwmon.ko=hwmon-extra sfctemp.ko=hwmon-extra sg2042-mcu.ko=hwmon-extra sht15.ko=hwmon-extra sht21.ko=hwmon-extra sht3x.ko=hwmon-extra sht4x.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} shtc1.ko=hwmon-extra sl28cpld-hwmon.ko=hwmon-extra smpro-hwmon.ko=hwmon-extra sparx5-temp.ko=hwmon-extra stef48h28.ko=hwmon-extra stpddc60.ko=hwmon-extra sy7636a-hwmon.ko=hwmon-extra tc654.ko=hwmon-extra tc74.ko=hwmon-extra tda38640.ko=hwmon-extra thmc50.ko=hwmon-extra tmp513.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} tps23861.ko=hwmon-extra tps25990.ko=hwmon-extra tps40422.ko=hwmon-extra tps53679.ko=hwmon-extra tps546d24.ko=hwmon-extra tsc1641.ko=hwmon-extra ucd9000.ko=hwmon-extra ucd9200.ko=hwmon-extra ultra45_env.ko=hwmon-extra vexpress-hwmon.ko=hwmon-extra wm831x-hwmon.ko=hwmon-extra wm8350-hwmon.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} xdp710.ko=hwmon-extra xdp720.ko=hwmon-extra xdpe12284.ko=hwmon-extra xdpe152c4.ko=hwmon-extra xdpe1a2g7b.ko=hwmon-extra xgene-hwmon.ko=hwmon-extra yogafan.ko=hwmon-extra zl6100.ko=hwmon-extra
%global modules_subpackages %{modules_subpackages} kb9002.ko=hwmon-extra mpq82d00.ko=hwmon-extra mpq8646.ko=hwmon-extra sq24860.ko=hwmon-extra vt7505.ko=hwmon-extra altera-socfpga-hwmon.ko=hwmon-extra eic7700-pvt.ko=hwmon-extra polarfire-soc-tvs.ko=hwmon-extra versal-sysmon.ko=hwmon-extra versal-sysmon-i2c.ko=hwmon-extra

# Modules with obscure firmware dependencies (not covered by the kernel-firmware packages)
%global modules_subpackages %{modules_subpackages} p54spi.ko snd-asihpi.ko snd-usb-6fire.ko bcm203x.ko adf7242.ko ast ath10k_pci.ko ath6kl_sdio.ko at76c50x-usb.ko smsmdtv.ko b43 b43legacy bfusb.ko hci_bcm4377.ko moxa.ko

# IMPORTANT
# This is the place where you set kernel version i.e 4.5.0
# compose tar.xz name and release
%define kernelversion 7
%define patchlevel 3
%define sublevel 0
%define relc 2

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

%bcond_without build_source
%bcond_without build_devel
%bcond_without cross_headers

%bcond_with build_debug
%bcond_without evdi
%bcond_without vbox_orig_mods
%bcond_without clr
%bcond_without saa716x
# build perf and cpupower tools
%if %{cross_compiling}
%bcond_with bpftool
%bcond_with perf
%else
%bcond_without bpftool
%bcond_with perf
%endif
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
%bcond_without nvidia

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
License:	GPL-2.0
Group:		System/Kernel and hardware
ExclusiveArch:	%{ix86} %{x86_64} %{armx} %{riscv} %{loongarch64}
ExclusiveOS:	Linux
URL:		https://www.kernel.org

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
Source2:	https://github.com/Kimplul/hid-tmff2/archive/refs/heads/master.tar.gz#/hid-tmff2-20260825.tar.gz
### This is for stripped SRC RPM
%if %{with build_nosrc}
NoSource:	0
%endif
Source3:	README.kernel-sources
Source4:	%{name}.rpmlintrc
Source5:	https://github.com/linux-thinkpad/tp_smapi/releases/download/tp-smapi%2F0.45/tp_smapi-0.45.tgz
## all in one configs for each kernel
Source10:	x86-omv-defconfig
Source11:	i386-omv-defconfig
Source12:	arm-omv-defconfig
Source13:	arm64-omv-defconfig
Source14:	riscv-omv-defconfig
Source15:	powerpc-omv-defconfig
Source16:	loongarch-omv-defconfig
Source17:	generic-omv-defconfig
# Fragments to be used with all/multiple kernel types
Source20:	filesystems.fragment
Source21:	framer.fragment
Source22:	debug.fragment
Source23:	networking.fragment
Source24:	bluetooth.fragment
Source25:	sensors.fragment
Source26:	hid.fragment
Source27:	nvme.fragment
Source28:	modules.fragment
Source29:	gcc-plugins.fragment
Source30:	pps.fragment
Source31:	cgroups.fragment
Source32:	firmware.fragment
Source33:	security.fragment
Source34:	trace.fragment
# Extracted shared subsystem fragments (see CONFIGS.md / manage-kernel-configs.py)
Source35:	usb.fragment
Source36:	sound.fragment
Source37:	media.fragment
Source38:	crypto.fragment
Source39:	drm.fragment
Source40:	scsi.fragment
Source41:	input.fragment
Source42:	wireless.fragment
Source43:	mtd.fragment
Source44:	net-phy.fragment
Source45:	gpio.fragment
Source46:	infiniband.fragment
Source47:	virt.fragment
Source48:	misc-drivers.fragment
# Overrides (highest priority) for configs
Source200:	znver1.overrides
Source201:	temporary-workarounds.overrides
Source202:	arm64.overrides
# config and systemd service file from fedora
Source300:	cpupower.service
Source301:	cpupower.config

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
# booting SynQuacer from USB flash drives on old firmware
# 9d55bebd9816903b821a403a69a94190442ac043 builds on
# 7a8b64d17e35810dc3176fe61208b45c15d25402.
Source1001:	revert-7a8b64d17e35810dc3176fe61208b45c15d25402.patch
Source1002:	revert-9d55bebd9816903b821a403a69a94190442ac043.patch

# FIXME bring this back when it's ported to 6.15
#Patch30:	https://gitweb.gentoo.org/proj/linux-patches.git/plain/5010_enable-cpu-optimizations-universal.patch?h=6.7#/cpu-optimizations.patch
Patch31:	die-floppy-die.patch
Patch32:	0001-Add-support-for-Acer-Predator-macro-keys.patch
Patch34:	kernel-5.6-kvm-gcc10.patch
Patch35:	linux-6.7-BTF-deps.patch
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
#Patch41:	tp_smapi-clang.patch
# 7.2 dropped strncpy() and no longer pulls string.h in transitively
Patch41:	tp_smapi-string.h.patch
# (tpg) https://github.com/ClangBuiltLinux/linux/issues/1341
Patch42:	linux-5.11-disable-ICF-for-CONFIG_UNWINDER_ORC.patch
# Disabling rdseed breaks starting Qt applications
# https://github.com/qt/qtbase/blob/dev/src/corelib/global/qsimd.cpp#L662-L672
# Users don't appreaciate not being able to boot to a desktop
# from which they can download the required BIOS update!
Patch43:	dont-disable-rdseed.patch

# (crazy) see: https://forum.openmandriva.org/t/nvme-ssd-m2-not-seen-by-omlx-4-0/2407
Patch45:	Unknow-SSD-HFM128GDHTNG-8310B-QUIRK_NO_APST.patch
# Restore ACPI loglevels to sane values
Patch46:	https://gitweb.frugalware.org/wip_kernel/raw/86234abea5e625043153f6b8295642fd9f42bff0/source/base/kernel/acpi-use-kern_warning_even_when_error.patch
Patch47:	https://gitweb.frugalware.org/wip_kernel/raw/23f5e50042768b823e18613151cc81b4c0cf6e22/source/base/kernel/fix-acpi_dbg_level.patch
Patch51:	linux-5.5-corsair-strafe-quirks.patch
Patch52:	http://crazy.dev.frugalware.org/smpboot-no-stack-protector-for-gcc10.patch
Patch55:	linux-5.16-clang-no-attribute-symver.patch
Patch60:	linux-6.18-clang.patch
Patch61:	linux-6.19-acpi-clang.patch
# Landed in 7.2 (arch/x86/boot/compressed/Makefile already has -fno-jump-tables).
#Patch62:	linux-7.1-x86-boot-compressed-no-jump-tables.patch
# 7.3 dropped RTW89_FW_CMD_OFLD_SRC_OTHER (H2C src is 2 bits).
#Patch63:	rtw89-ofld-src-other-fits-h2c.patch
# 7.3-rc2 kmalloc_obj() conversion: void * + memcpy trips Clang ThinLTO FORTIFY
Patch64:	gud-kmalloc_obj-typed-ptr.patch

### Additional hardware support
### TV tuners:
# SAA716x DVB driver (Soeren Moch tree, already ported to 7.2)
# git clone --depth=1 -b saa716x-7.2 https://github.com/s-moch/linux-saa716x.git
# tar cJf saa716x-driver-YYYYMMDD.tar.xz -C linux-saa716x drivers/media/pci/saa716x
# Uses only in-tree frontends (stv090x/stv6110x/si2168/si2157/tda1004x/tda827x/isl6423).
# OSD_RAW_* / AUDIO_GET_PTS ioctls used by saa716x_ff (Technotrend S2-6400).
Source1003:	saa716x-driver-20260817.tar.xz
Patch210:	saa716x-uapi.patch

# VirtualBox patches -- added as Source: rather than Patch:
# because they need to be applied after stuff from the
# virtualbox-kernel-module-sources package is copied around
# Based on https://github.com/rpmfusion/VirtualBox-kmod/raw/refs/heads/master/kernel-6.19.patch
Source1005:	vbox-kernel-7.0.patch
Source1007:	vboxnet-clang.patch
Source1008:	vbox-modules-7.1.6-compile.patch
Source1009:	vbox-modules-6.15.patch

# EVDI Extensible Virtual Display Interface
# Needed by DisplayLink cruft
%define evdi_version 1.15.0
Source1010:	https://github.com/DisplayLink/evdi/archive/refs/tags/v%{evdi_version}.tar.gz

# Nexus -- BeOS like IPC, named semaphores, SHM, thread messaging, filesystem event notifications
# https://github.com/Numerio/Nexus
# https://v-os.dev/
Source1020:	https://github.com/Numerio/Nexus/archive/refs/heads/main.tar.gz#/nexus-20260831.tar.gz
Patch1021:	nexus-compile.patch

# Nvidia GPU driver
%define nvidia_version 610.57.04
Source1030:	https://github.com/NVIDIA/open-gpu-kernel-modules/archive/refs/tags/%{nvidia_version}.tar.gz
# Script to internalize nvidia modules
Source1031:	install-to-kernel-tree.sh
# Documentation of the above
Source1032:	CHANGES.md
Source1033:	nvidia-symvers-location.patch
# 610.57.04 of_gpio compat: gpio_device_get_chip() is not const
Source1034:	nvidia-gpio-const.patch

# Assorted fixes

# https://github.com/Kicksecure/tirdad
Patch100:	security_tirdad.patch

# Bring back ashmem -- anbox and waydroid still need it
Patch211:	revert-721412ed3d819e767cac2b06646bf03aa158aaec.patch
# Modular binder and ashmem -- let's try to make anbox happy
Patch212:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/android-enable-building-ashmem-and-binder-as-modules.patch
Patch213:	https://salsa.debian.org/kernel-team/linux/raw/master/debian/patches/debian/export-symbols-needed-by-android-drivers.patch
Patch216:	restore-exporting-symbols-needed-by-binder.patch

Patch214:	ras-fix-build-without-debugfs.patch
Patch217:	acpi-chipset-workarounds-shouldnt-be-necessary-on-non-x86.patch
# Revert minimum power limit lock on amdgpu. If you bought a GPU, it means you own it at every level. That a power of Free Software,
# AMD cannot limit the right to own and prohibit people under volting/under power when they need it or when AMD cards are poorly designed to the point that they heat up, restart and cause very noisy operation.
Patch218:	amdgpu-ignore-min-pcap.patch
# Imported from Nobara. Enable full AMD GPU controls like fan speed etc (needed for corectrl and others)
Patch219:	https://raw.githubusercontent.com/Nobara-Project/rpm-sources/main/baseos/kernel/6.7.6/0001-Set-amdgpu.ppfeaturemask-0xffffffff-as-default.patch

# Fix CPU frequency governor mess caused by recent Intel patches
Patch225:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/0001-Revert-cpufreq-Avoid-configuring-old-governors-as-de.patch
Patch226:	https://gitweb.frugalware.org/frugalware-current/raw/50690405717979871bb17b8e6b553799a203c6ae/source/base/kernel/revert-parts-of-a00ec3874e7d326ab2dffbed92faddf6a77a84e9-no-Intel-NO.patch

# Fix perf — 7.2 rewrote tools/perf libunwind/JVMTI bits; needs rebasing
#Patch230:	linux-5.11-perf-compile.patch
#Patch231:	ce71038e673ee8291c64631359e56c48c8616dc7.patch

# (tpg) Armbian ARM Patches
# https://github.com/armbian/build/tree/main/patch/kernel/archive/
Patch240:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/board-rockpro64-fix-emmc.patch
Patch242:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/board-rockpro64-work-led-heartbeat.patch
Patch243:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/general-fix-mmc-signal-voltage-before-reboot.patch
Patch245:	https://github.com/armbian/build/raw/refs/heads/main/patch/kernel/archive/rockchip64-6.11/rk3399-unlock-temperature.patch
Patch246:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/general-increasing_DMA_block_memory_allocation_to_2048.patch
Patch247:	https://raw.githubusercontent.com/armbian/build/main/patch/kernel/archive/rockchip64-6.5/general-rk808-configurable-switch-voltage-steps.patch
Patch248:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/rk3399-sd-drive-level-8ma.patch
Patch250:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/rk3399-enable-dwc3-xhci-usb-trb-quirk.patch
Patch254:	https://raw.githubusercontent.com/armbian/build/master/patch/kernel/archive/rockchip64-6.0/rk3399-rp64-rng.patch

# (tpg) Manjaro ARM Patches
#Patch260:	https://gitlab.manjaro.org/manjaro-arm/packages/core/linux/-/raw/master/1005-panfrost-Silence-Panfrost-gem-shrinker-loggin.patch

# Other ARM64 patches
Patch261:	https://raw.githubusercontent.com/immortalwrt/immortalwrt/master/target/linux/rockchip/patches-5.15/992-rockchip-rk3399-overclock-to-2.2-1.8-GHz.patch

# (tpg) patches taken from https://github.com/OpenMandrivaSoftware/os-image-builder/tree/master/device/rockchip/generic/kernel-patches
Patch300:	add-board-orangepi-4.patch
Patch303:	rk3399-add-sclk-i2sout-src-clock.patch
#Patch304:	rtl8723cs-compile.patch
Patch305:	kernel-6.0-rc2-perf-x86-compile.patch
#Patch306:	linux-6.1-binutils-2.40.patch

# V4L2 loopback
# https://github.com/umlaeute/v4l2loopback
Source400:	https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback.c
Source401:	https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback.h
Source402:	https://raw.githubusercontent.com/umlaeute/v4l2loopback/main/v4l2loopback_formats.h

# Patches to external modules
# Marked SourceXXX instead of PatchXXX because the modules
# being touched aren't in the tree at the time %%autopatch -p1
# runs...

%if %{with clr}
# (tpg) some patches from ClearLinux
# https://github.com/clearlinux-pkgs/linux/
Patch900:	0101-i8042-decrease-debug-message-level-to-info.patch
Patch901:	0102-increase-the-ext4-default-commit-age.patch
Patch903:	0104-pci-pme-wakeups.patch
Patch904:	0105-ksm-wakeups.patch
Patch907:	0108-smpboot-reuse-timer-calibration.patch
Patch908:	0109-initialize-ata-before-graphics.patch
Patch910:	0111-ipv4-tcp-allow-the-memory-tuning-for-tcp-to-go-a-lit.patch
Patch913:	0117-migrate-some-systemd-defaults-to-the-kernel-defaults.patch
%endif

# Rockchip 3588 HDMI audio support
# from https://github.com/andyshrk/linux
# rk3588-hdmi-dsi-upstream-linux-6.13-rc1-2024-12-05 branch
# Patches of the series that are commented out don't apply anymore and
# need rebasing.
# 7.2 dropped arch/{arm,arm64}/configs/rockchip_defconfig and rpi_defconfig
#Patch950:	https://github.com/torvalds/linux/commit/e0c5c98b4558d336ecb6b5a3c174816b4ed41db2.patch
#Patch951:	https://github.com/torvalds/linux/commit/cd6e4f6d8babdb5e65525c6dd2d1e373558b38ab.patch
#Patch952:	https://github.com/torvalds/linux/commit/4071b7a0642a41773d61b16ae1d02218bc25345e.patch
#Patch953:	https://github.com/torvalds/linux/commit/6da0ae6e419442449ffa7778de518ca37292352b.patch
#Patch954:	https://github.com/torvalds/linux/commit/d6aa52f8a15e56737de5e73f4f2acbb2632f43c0.patch
#Patch955:	https://github.com/torvalds/linux/commit/250083364dc2764b6ae61a124dfb8afc575e565a.patch
#Patch956:	https://github.com/torvalds/linux/commit/146008b9d4241d4e14e5b173038aa78262c2bbcd.patch
#Patch957:	https://github.com/torvalds/linux/commit/dad4c5aac3a74cf3593fad9f7c7d0e83ae96bfa5.patch
#Patch958:	https://github.com/torvalds/linux/commit/6d478d25de6b7550769b77edcbf8d330238542a8.patch
#Patch959:	https://github.com/torvalds/linux/commit/cc17a3358bece56c8932b6a62da242f841feb2e2.patch
#Patch960:	https://github.com/torvalds/linux/commit/bc1d59cd423b4a327af19bcd726f108f0f5a5da5.patch
Patch961:	https://github.com/torvalds/linux/commit/00e0ee4050216dc768704c503860ac4ec82e7e41.patch
#Patch962:	https://github.com/torvalds/linux/commit/839301464ba91c64483923c9a2a344b1c28e56ed.patch
Patch963:	https://github.com/torvalds/linux/commit/0b7853f3fa5807bfcc193af0ebe4174fb7df21f3.patch
#Patch964:	https://github.com/torvalds/linux/commit/dd3ada12c3f671e92f67416ba9c267e1b12ed29d.patch
Patch965:	https://github.com/torvalds/linux/commit/725cb07d90c7949a971378635e7755ff9a54d25d.patch
Patch966:	https://github.com/torvalds/linux/commit/046fbc970839b287d29053c7a1083e78eecb5822.patch
#Patch967:	https://github.com/torvalds/linux/commit/f45ac0c8b0145582ba277f149a39ad386b0627b1.patch
# 516ae4f... has landed
Patch975:	https://github.com/torvalds/linux/commit/cef2dc6b338e1349b2e9feda9bf41e88510aaf5a.patch
Patch976:	https://github.com/torvalds/linux/commit/0f13fb4aa5e9aec8fcc30d4cd244a1c94a9ab01f.patch
Patch979:	https://github.com/torvalds/linux/commit/beba499cda3702062e7708b6b402d07b26d090e5.patch
Patch981:	https://github.com/torvalds/linux/commit/c8699f87d802bbb6e5aab8292f2e285c56976a35.patch
Patch982:	https://github.com/torvalds/linux/commit/a7a7cf522d7636dc1280adb1b1de7fe45f9b3305.patch
Patch983:	https://github.com/torvalds/linux/commit/f0118748bc1f791775c90c52791a1770f4429702.patch
# 4940862... has landed
# 1e51ce4... has landed
# aa868c1... has landed
# 9d85b74... has landed
# 2bd8528... has landed
# 92bd2d2... has landed
#Patch990:	https://github.com/torvalds/linux/commit/d3fd937a73e239efaf1ced03a5a10637e5ae9a95.patch
#Patch991:	https://github.com/torvalds/linux/commit/57c6d683477d619dab36bc39ca5b3c011f4a1dab.patch
#Patch992:	https://github.com/torvalds/linux/commit/ea0dd2c5e19d4c5e8d5109d78ac0d3ef1461fe43.patch
# bf10475... has landed
#Patch994:	https://github.com/torvalds/linux/commit/c1cffe7e472cf58c948a52de76007117e7d550ae.patch
# 0ab95ab... has landed
# bc27ea8... has landed
# 565e00d... has landed
Patch998:	https://github.com/torvalds/linux/commit/899558f6782528d5324322ae6e4c270e150c3d6f.patch
# b5fb817... has landed
#Patch1000:	https://github.com/torvalds/linux/commit/b35059eb51972524e48f13d9a6c39448bcd0874b.patch
#Patch1001:	https://github.com/torvalds/linux/commit/6f0311441ab7b53cdcdf71b10d8a8594f1a47ef1.patch
#Patch1002:	https://github.com/torvalds/linux/commit/d41ae3d5aa30f6ad8229967e9f97f9cf9d8527f9.patch
# 6ebd774... has landed
#Patch1004:	https://github.com/torvalds/linux/commit/353e6fcd1cd010ce89dd90a8cc5bcb506c362025.patch
#Patch1005:	https://github.com/torvalds/linux/commit/52a77da4f18b009c85fbfd30701b93e5fe5e715a.patch
#Patch1006:	https://github.com/torvalds/linux/commit/06fb8acf220d3bd8d1bffe098c41fbe398b36d07.patch
# 2108e09... has landed
# b76b3fe... has landed
# 7fd2c93... has landed
# de56911... has landed
# c75314e... has landed
# 8571e14... has landed
#Patch1015:	https://github.com/torvalds/linux/commit/ec744b5548e79d18670651113a5855fd31e7472e.patch
#Patch1016:	https://github.com/torvalds/linux/commit/05a7eca409973abbc3d97a726b88b07d256859ae.patch
# 406e4c9... has landed
# 7.2 dropped arch/arm64/configs/rockchip_defconfig
#Patch1019:	https://github.com/torvalds/linux/commit/dfb6b6ac7b8403a37c94e5afb0b990643409cbed.patch
Source2000:	7.0-rc1-compile.patch
Source2001:	7.0-rc1-compile-x86.patch

BuildRequires:	make
BuildRequires:	zstd
BuildRequires:	findutils
BuildRequires:	bc
BuildRequires:	flex
BuildRequires:	bison
BuildRequires:	binutils
BuildRequires:	hostname
BuildRequires:	gnutar
BuildRequires:	clang
BuildRequires:	llvm
BuildRequires:	lld
BuildRequires:	pkgconfig(libcap)
BuildRequires:	pkgconfig(libssl)
BuildRequires:	diffutils
BuildRequires:	atomic-devel
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
# As of 6.6-rc5, cpupower's FR translation uses iso-8859-1
BuildRequires:	locales-extra-charsets
BuildRequires:	pkgconfig(libpci)
%endif
# (Unconditional because it's small and may also be used by other tools)
BuildRequires:	gettext

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
BuildRequires:	%mklibname pfm
%endif

%ifarch %{arm}
BuildRequires:	uboot-mkimage
%endif


# Let's pull in some of the most commonly used DKMS modules
# so end users don't have to install compilers (and worse,
# get compiler error messages on failures)
%ifarch %{x86_64}
BuildRequires:	virtualbox-kernel-module-sources >= 7.2.6
%if %{with vbox_orig_mods}
BuildRequires:	virtualbox-guest-kernel-module-sources >= 7.2.6
%endif
%endif

%description
The kernel package contains the Linux kernel (vmlinuz), the core of your
%{distribution} operating system. The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.

#
# (tpg) generate subpackages for kernel flavours
#
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
Requires(posttrans):	kmod >= 27-3
Recommends:	kernel-firmware
%ifarch %{ix86} %{x86_64} %{aarch64}
# TEMPORARY requirement — drop this Requires after one released upgrade
# cycle. It only exists so existing nouveau users keep the driver on
# update. After it is gone, NVIDIA-proprietary users can uninstall
# %{name}-${flavour}-modules-nouveau without removing the kernel.
Requires:	%{name}-${flavour}-modules-nouveau = %{EVRD}
%endif
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
done
)

#
# kernel-devel
#
%if %{with build_devel}
%(for flavour in %{kernel_flavours}; do
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
done
)
# end build_devel
%endif

#
# kernel-debuginfo
#
%if %{with build_debug}
%(for flavour in %{kernel_flavours}; do
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
done
)
# end build_debug
%endif

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
Tools needed to communicate with a Hyper-V host.

%files -n hyperv-tools
%{_sbindir}/hv_kvp_daemon
%{_unitdir}/hypervkvpd.service
%{_udevrulesdir}/70-hypervkvp.rules
%{_sbindir}/hv_vss_daemon
%{_unitdir}/hypervvssd.service
%{_udevrulesdir}/70-hypervvss.rules
%ifarch %{x86_64}
%{_sbindir}/hv_fcopy_uio_daemon
%endif
%{_unitdir}/hypervfcopyd.service
%{_udevrulesdir}/70-hypervfcopy.rules
%{_sbindir}/lsvmbus
%{_libexecdir}/hypervkvpd
%endif

%if %{with bpftool}
%package -n bpftool
Summary:	Inspection and simple manipulation of eBPF programs and maps
Group:		System/Kernel and hardware

%description -n bpftool
This package contains the bpftool, which allows inspection and simple
manipulation of eBPF programs and maps.
%endif

%package headers
Summary:	Linux kernel header files mostly used by your C library
Version:	%{version}
Release:	%{release}
Group:		System/Kernel and hardware
%if 0%{!?relc:1}
# (tpg) fix bug https://issues.openmandriva.org/show_bug.cgi?id=1580
Provides:	kernel-headers = 1:%{version}-%{release}
Obsoletes:	kernel-headers < 1:%{version}-%{release}
%rename linux-userspace-headers
%rename kernel-release-headers
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

%setup -q -n linux-%{kernelversion}.%{patchlevel}%{?relc:-rc%{relc}} -a 2 -a 5 -a 1003 -a 1020
TOPDIR="$(pwd)"

%if %{with evdi}
tar xf %{S:1010}
%endif
%if 0%{?sublevel:%{sublevel}}
[ -e .git ] || git init
xzcat %{SOURCE1000} |git apply - || git apply %{SOURCE1000}
rm -rf .git
%endif

%if %{with nvidia}
tar xf %{S:1030}
cd open-gpu-kernel-modules-%{nvidia_version}
patch -p1 -b -z .1033~ <%{S:1033}
patch -p1 -b -z .1034~ <%{S:1034}
cp %{S:1031} .
chmod +x install-to-kernel-tree.sh
./install-to-kernel-tree.sh ${TOPDIR}
cd ..
rm -rf open-gpu-kernel-modules-%{nvidia_version}
%endif

mv Nexus-main/nexus drivers/nexus
rm drivers/nexus/CMakeLists.txt
cat >>drivers/Makefile <<'EOF'
obj-$(CONFIG_NEXUS) += nexus/
EOF
sed -i -e '/endmenu/i config NEXUS\n	tristate "BeOS-like IPC etc."\n	help\n	  BeOS like IPC, named semaphores, SHM, thread messaging and FS event notifications' drivers/Kconfig
sed -i -e 's,obj-m,obj-$(CONFIG_NEXUS),g' drivers/nexus/Makefile
rm -rf Nexus-main

# uses --sort=name and other gnutar specific options
sed -i -e '/\${TAR}/iTAR=gtar' kernel/gen_kheaders.sh
sed -i -e 's, tar , gtar ,g' scripts/Makefile.package

mv tp_smapi-*/*.{c,h} drivers/platform/x86
cat >>drivers/platform/x86/Kconfig <<EOF
config THINKPAD_EC
	tristate "ThinkPad LPC Embedded Controller"
	depends on X86
	help
	  This is a low-level driver for accessing the ThinkPad H8S embedded
	  controller over the LPC bus (not to be confused with the ACPI Embedded
	  Controller interface).

config TP_SMAPI
	tristate "ThinkPad SMAPI Support"
	depends on X86
	select THINKPAD_EC
	default n
	help
	  This adds SMAPI support on Lenovo/IBM ThinkPads, for features such
	  as battery charging control. For more information about this driver
	  see <http://www.thinkwiki.org/wiki/tp_smapi>.

	  If you have a Lenovo/IBM ThinkPad laptop, say Y or M here.

config SENSORS_HDAPS
	tristate "Thinkpad HDAPS sensor support"
	depends on X86
	select THINKPAD_EC
	default n
	help
	  ThinkPad HDAPS sensor
EOF
cat >>drivers/platform/x86/Makefile <<EOF
obj-\$(CONFIG_THINKPAD_EC) += thinkpad_ec.o
obj-\$(CONFIG_TP_SMAPI) += tp_smapi.o
obj-\$(CONFIG_SENSORS_HDAPS) += hdaps.o
EOF
rm -rf tp_smapi-*

%autopatch -p1

# Apparently, vm_clean was added in tools/Makefile before tools/vm was added
if [ -d tools/vm ]; then
	echo "Remove the vm_clean workaround, it should work now"
	exit 1
fi
sed -i -e 's,vm_clean ,,' tools/Makefile

%if %{with saa716x}
# Wire s-moch saa716x into the in-tree media PCI build (same as upstream saa716x-7.2)
sed -i -e '/saa7164/isource "drivers/media/pci/saa716x/Kconfig"' drivers/media/pci/Kconfig
sed -i -e '/saa7164/iobj-$(CONFIG_SAA716X_SUPPORT) += saa716x/' drivers/media/pci/Makefile
%endif

%if %{with evdi}
# Merge EVDI
mv evdi-%{evdi_version}/module drivers/gpu/drm/evdi
rm -rf evdi-%{evdi_version}
sed -i -e '/imagination/isource "drivers/gpu/drm/evdi/Kconfig"' drivers/gpu/drm/Kconfig
# DKMS/out-of-tree Makefile is not usable in-tree. Keep the same objects as
# upstream 1.15, plus conftest.sh → evdi_detect.h (EVDI_HAVE_* probes).
# Do not build the kunit tests/ subtree.
cat >drivers/gpu/drm/evdi/Makefile <<'EOF'
ccflags-y += -include $(obj)/evdi_detect.h
clean-files := evdi_detect.h evdi_detect.h.tmp

evdi-y := evdi_platform_drv.o evdi_platform_dev.o evdi_sysfs.o evdi_modeset.o evdi_connector.o evdi_encoder.o evdi_drm_drv.o evdi_fb.o evdi_gem.o evdi_painter.o evdi_params.o evdi_cursor.o evdi_debug.o evdi_i2c.o
evdi-$(CONFIG_COMPAT) += evdi_ioc32.o
obj-$(CONFIG_DRM_EVDI) := evdi.o

$(addprefix $(obj)/, $(evdi-y) evdi_ioc32.o): $(obj)/evdi_detect.h

$(obj)/evdi_detect.h: $(src)/conftest.sh FORCE
	$(Q)$(CONFIG_SHELL) $(src)/conftest.sh "$(CC)" $@.tmp \
		$(NOSTDINC_FLAGS) $(LINUXINCLUDE) $(KBUILD_CPPFLAGS) $(KBUILD_CFLAGS) -DMODULE
	$(Q)cmp -s $@.tmp $@ 2>/dev/null && rm -f $@.tmp || mv $@.tmp $@
EOF
echo 'obj-$(CONFIG_DRM_EVDI) += evdi/' >>drivers/gpu/drm/Makefile
%endif

# Merge TMFF2
mv hid-tmff2-* drivers/hid/tmff-new
cat >drivers/hid/tmff-new/Kconfig <<'EOF'
config HID_TMFF_NEW
	tristate "Thrustmaster T300RS, T248, TX, TS-XV wheel support"
	help
	  A Linux kernel module for Thrustmaster T300RS, T248, and
	  (experimental support) TX, TS-PC and TS-XV wheels.

EOF
cat >drivers/hid/tmff-new/Makefile <<'EOF'
hid-tmff-new-y := src/hid-tmff2.o src/tmt248/hid-tmt248.o src/tmt300rs/hid-tmt300rs.o src/tmtspc/hid-tmtspc.o src/tmtsxw/hid-tmtsxw.o src/tmtx/hid-tmtx.o
obj-$(CONFIG_HID_TMFF_NEW) += hid-tmff-new.o
EOF
cat >>drivers/hid/Kconfig <<'EOF'
source "drivers/hid/tmff-new/Kconfig"
EOF
cat >>drivers/hid/Makefile <<'EOF'
obj-$(CONFIG_HID_TMFF_NEW) += tmff-new/
EOF

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
patch -p1 -z .1008~ -b <%{S:1008}
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
echo 'obj-$(CONFIG_VBOXGUEST) += vboxdrv/' >>drivers/virt/Makefile
# VirtualBox network adapter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetadp drivers/net/
sed -i -e 's,\$(VBOXNETADP_DIR),drivers/net/vboxnetadp/,g' drivers/net/vboxnetadp/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetadp/Makefile*
echo 'obj-$(CONFIG_VBOXGUEST) += vboxnetadp/' >>drivers/net/Makefile
# VirtualBox network filter
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxnetflt drivers/net/
sed -i -e 's,\$(VBOXNETFLT_DIR),drivers/net/vboxnetflt/,g' drivers/net/vboxnetflt/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/net/vboxnetflt/Makefile*
echo 'obj-$(CONFIG_VBOXGUEST) += vboxnetflt/' >>drivers/net/Makefile
%if 0
# VirtualBox PCI
# https://forums.gentoo.org/viewtopic-t-1105508-start-0.html -- not very
# useful (yet), but a source of many errors.
# Potentially re-enable if it ever gets fixed to support PCIE.
cp -a $(ls --sort=time -1d /usr/src/virtualbox-*|head -n1)/vboxpci drivers/pci/
sed -i -e 's,\$(VBOXPCI_DIR),drivers/pci/vboxpci/,g' drivers/pci/vboxpci/Makefile*
sed -i -e "s,^KERN_DIR.*,KERN_DIR := $(pwd)," drivers/pci/vboxpci/Makefile*
echo 'obj-$(CONFIG_VBOXGUEST) += vboxpci/' >>drivers/pci/Makefile
%endif
# VirtualBox 7.2+ hosts no longer call kvm_enable_virtualization() /
# ASMCpuIdEx_EDX(); they open a dummy /dev/kvm instead.  The 7.0-era
# SUPDrv-linux.c patch does not apply and is not needed.
#patch -p1 -z .1005~ -b <%{S:1005}
patch -p1 -z .1007~ -b <%{S:1007}
#patch -p1 -z .1009~ -b <%{S:1009}
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

# Port leftover out-of-tree copies to 6.15+ timer names
sed -i -e 's,del_timer_sync,timer_delete_sync,g' drivers/media/v4l2-core/v4l2loopback.c drivers/platform/x86/hdaps.c
[ -e drivers/virt/vboxdrv/r0drv/linux/timer-r0drv-linux.c ] && sed -i -e 's,del_timer_sync,timer_delete_sync,g' drivers/virt/vboxdrv/r0drv/linux/timer-r0drv-linux.c

# get rid of unwanted files
find . -name '*~' -o -name '*.orig' -o -name '*.append' -o -name '*.g*ignore' | %kxargs rm -f

# fix missing exec flag on file introduced in 4.14.10-rc1
chmod 755 tools/objtool/sync-check.sh

%ifarch znver1 znver2 znver3
# Workaround for https://github.com/llvm/llvm-project/issues/82431
echo 'CFLAGS_ip6_input.o += -march=x86-64-v3' >>net/ipv6/Makefile
%endif

patch -p1 -z .2000~ -b <%{S:2000}
%ifarch %{ix86} %{x86_64}
patch -p1 -z .2001~ -b <%{S:2001}
%endif

%build
%set_build_flags

%if %{cross_compiling}
# Host helpers (scripts/sign-file, kconfig, mrproper) must use native
# headers and flags. Cross rpm flags leak target CFLAGS (-mabi=...)
# and PKG_CONFIG_SYSROOT_DIR (target stdio.h) into HOSTCC/HOSTPKG_CONFIG.
unset PKG_CONFIG_SYSROOT_DIR
unset PKG_CONFIG_LIBDIR
export HOSTCFLAGS="-O2 -std=gnu11"
export HOSTCXXFLAGS="-O2"
export HOSTLDFLAGS=""
export CFLAGS=""
export CXXFLAGS=""
export LDFLAGS=""
export CC=clang
export CXX=clang++
%endif

###
### Functions definitions needed to build kernel
###

# (tpg) Please stop enabling CONFIG_RT_GROUP_SCHED - this option is not recommended with systemd systemd/systemd#553, killing the build."
# (tpg) Please do not disable CONFIG_MODULE_COMPRESS_NONE=y or set any other module compression inside .config, as this will bloat main package instead of debuginfo subpackage, killing the build."
# (tpg) Please do not set CONFIG_DEBUG_KERNEL=y as this is relase build, and we are not developing kernel or its modules."
FIXED_CONFIGS=" --disable CONFIG_RT_GROUP_SCHED \
%if %{without bpftool}
	--disable CONFIG_DEBUG_INFO_BTF \
	--disable CONFIG_DEBUG_INFO_BTF_MODULES \
%endif
%if %{with build_debug}
	--disable CONFIG_DEBUG_INFO_NONE \
	--enable CONFIG_DEBUG_INFO \
%else
	--enable CONFIG_DEBUG_INFO_NONE \
	--disable CONFIG_DEBUG_INFO \
%endif
	--disable CONFIG_MODULE_COMPRESS_NONE \
	--disable CONFIG_DEBUG_KERNEL "

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
	# FIXME: CONFIG_CFI_CLANG and friends are turned off on x86_64
	# because as of kernel 6.4.3 and VirtualBox 7.0, enabling any
	# form of CFI breaks starting a VM in VirtualBox.
	# If this ever gets fixed, CFI should be reenabled.
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
%ifarch %{x86_64}
# CONFIG_CFI_CLANG is not set
# CONFIG_CFI_CLANG_SHADOW is not set
# CONFIG_CFI_PERMISSIVE is not set
%else
CONFIG_CFI_CLANG=y
CONFIG_CFI_ICALL_NORMALIZE_INTEGERS=y
CONFIG_CFI_AUTO_DEFAULT=y
CONFIG_CFI_CLANG_SHADOW=y
CONFIG_CFI_PERMISSIVE=y
%endif
CONFIG_RELR=y
EOF
}

serverize() {
	sed -i -E \
		-e 's/^CONFIG_PREEMPT=y/# CONFIG_PREEMPT is not set/' \
		-e 's/^# CONFIG_PREEMPT_NONE is not set/CONFIG_PREEMPT_NONE=y/' \
		-e 's/CONFIG_HZ_1000=y/# CONFIG_HZ_1000 is not set/' \
		-e 's/^CONFIG_HZ_100 is not set/CONFIG_HZ_100=y/' \
		-e 's/^CONFIG_HZ=1000/CONFIG_HZ=100/' \
		-e 's/^CONFIG_MODIFY_LDT_SYSCALL=y/# CONFIG_MODIFY_LDT_SYSCALL is not set/' \
		"$1"
}

CreateConfig() {
	arch="$1"
	type="$2"
	config_dir=%{_sourcedir}
	rm -fv .config

	printf '%s\n' "<-- Creating config for kernel type ${type} for ${arch}"
	if printf '%s' ${type} | grep -q gcc; then
%if %{cross_compiling}
		CC=%{_target_platform}-gcc
		CXX=%{_target_platform}-g++
%else
		CC=gcc
		CXX=g++
%endif
		HCC=gcc
		HCXX=g++
		# force ld.bfd, Kbuild logic issues when ld is linked to something else
		BUILD_LD="%{_target_platform}-ld.bfd"
		BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_TOOLS=""
	else
		CC=clang
		CXX=clang++
		HCC=clang
		HCXX=clang++
		# Workaround for LLD 16 BTF generation problem
		#BUILD_LD=ld.bfd
		#BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_LD="ld.lld --icf=none --no-gc-sections"
		BUILD_KBUILD_LDFLAGS="-Wl,--icf=none -Wl,--no-gc-sections"
		BUILD_TOOLS='LLVM=1 LLVM_IAS=1'
	fi

# (crazy) do not use %{S:X} to copy, if someone messes up we end up with broken stuff again
	EXTRAFRAGMENTS=""
	cfgarch="${arch}"
	case "${cfgarch}" in
	x86_64|znver1)
		arch=x86
		;;
	ppc*)
		arch=powerpc
		if echo %{_target_cpu} |grep -q le; then
			EXTRAFRAGMENTS=arch/powerpc/configs/le.config
		fi
		;;
	loongarch64)
		arch=loongarch
		;;
	i?86)
		arch=i386
		;;
	esac
	BASECONFIG=${config_dir}/${arch}-omv-defconfig

	if [ ! -e ${BASECONFIG} ]; then
		echo "======= No defconfig for ${arch} found! Generating it, please edit and \"git add\" it! ======="
		sleep 10m
		make ARCH=${arch} defconfig
		cp .config ${config_dir}/${arch}-omv-defconfig
	fi
	[ -e ${config_dir}/${arch}.overrides ] && EXTRAFRAGMENTS="$EXTRAFRAGMENTS ${config_dir}/${arch}.overrides"
	[ -e ${config_dir}/${cfgarch}.overrides ] && EXTRAFRAGMENTS="$EXTRAFRAGMENTS ${config_dir}/${cfgarch}.overrides"
	[ -e ${config_dir}/temporary-workarounds.overrides ] && EXTRAFRAGMENTS="$EXTRAFRAGMENTS ${config_dir}/temporary-workarounds.overrides"
	rm -f .config
	scripts/kconfig/merge_config.sh -m ${BASECONFIG} %{_sourcedir}/generic-omv-defconfig %{_sourcedir}/*.fragment $EXTRAFRAGMENTS
	printf '%s' ${type} | grep -q gcc || clangify .config
	printf '%s' ${type} | grep -q server && serverize .config

	if [ ! -e $(pwd)/.config ]; then
		printf '%s\n' "Kernel config in $(pwd) missing, killing the build."
		exit 1
	fi

# (tpg) apply our dynamic configs
	scripts/config $FIXED_CONFIGS

	printf '%s\n' "=== Configuring ${arch} ${type} kernel ==="
	make ARCH="${arch}" CC="$CC" HOSTCC="$HCC" CXX="$CXX" HOSTCXX="$HCXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" V=0 olddefconfig

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

	if printf '%s' ${KernelVer} | grep -q gcc; then
%if %{cross_compiling}
		CC=%{_target_platform}-gcc
		CXX=%{_target_platform}-g++
%else
		CC=gcc
		CXX=g++
%endif
		HCC=gcc
		HCXX=g++
		BUILD_OPT_CFLAGS="-O3"
# force ld.bfd, Kbuild logic issues when ld is linked  to something else
		BUILD_LD="%{_target_platform}-ld.bfd"
		BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_TOOLS=""
	else
		CC=clang
		CXX=clang++
		HCC=clang
		HCXX=clang++
		BUILD_OPT_CFLAGS="-O3 -Wno-unknown-warning-option %{pollyflags}"
		# Workaround for LLD 16 BTF generation problem
		#BUILD_LD=ld.bfd
		#BUILD_KBUILD_LDFLAGS="-fuse-ld=bfd"
		BUILD_LD="ld.lld --icf=none --no-gc-sections"
		BUILD_KBUILD_LDFLAGS="-Wl,--icf=none -Wl,--no-gc-sections"
%ifarch %{aarch64}
		# Using objcopy rather than llvm-objcopy is a workaround for a BTF
		# generation problem on aarch64
		BUILD_TOOLS='LLVM=1 LLVM_IAS=1 OBJCOPY=objcopy'
%else
		BUILD_TOOLS='LLVM=1 LLVM_IAS=1'
%endif
	fi

%ifarch %{arm}
	IMAGE=zImage
%else
%ifarch %{aarch64} %{riscv}
# (tpg) when booting with UEFI then uboot-tools is looking for a vmlinuz in PE-COFF format
	IMAGE=Image
	DTBS="dtbs"
%else
%ifarch %{loongarch64}
	IMAGE=vmlinux.efi
%else
	IMAGE=bzImage
%endif
%endif
%endif

	# One invocation: a second -jN make re-runs filechk on
	# cpufeaturemasks.h (FORCE) and races on .tmp_cpufeaturemasks.h
	%make_build V=0 VERBOSE=0 ARCH=%{target_arch} CC="$CC" HOSTCC="$HCC" CXX="$CXX" HOSTCXX="$HCXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KCFLAGS="$BUILD_OPT_CFLAGS" KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" $IMAGE $DTBS modules

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
	%make_build V=0 VERBOSE=0 INSTALL_MOD_PATH=%{temp_root} ARCH=%{target_arch} SRCARCH=%{target_arch} KERNELRELEASE=$KernelVer CC="$CC" HOSTCC="$HCC" CXX="$CXX" HOSTCXX="$HCXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" DEPMOD=/bin/true INSTALL_MOD_STRIP=1 modules_install

# headers
	%make_build V=0 VERBOSE=0 INSTALL_HDR_PATH=%{temp_root}%{_prefix} KERNELRELEASE=$KernelVer ARCH=%{target_arch} SRCARCH=%{target_arch} headers_install

%ifarch %{armx} %{ppc}
	%make_build  V=0 VERBOSE=0 ARCH=%{target_arch} CC="$CC" HOSTCC="$HCC" CXX="$CXX" HOSTCXX="$HCXX" LD="$BUILD_LD" HOSTLD="$BUILD_LD" $BUILD_TOOLS KBUILD_HOSTLDFLAGS="$BUILD_KBUILD_LDFLAGS" INSTALL_DTBS_PATH=%{temp_modules}/$KernelVer/dtb dtbs_install
	ln -s %{_modulesdir}/$KernelVer/dtb %{temp_boot}/dtb-$KernelVer
%endif

# remove /lib/firmware, we use a separate kernel-firmware
	rm -rf %{temp_root}/lib/firmware

# (tpg) strip modules out of debug bits
	find %{temp_modules}/$KernelVer -name "*.ko" -type f > all_modules
%if %{with build_debug}
	cat all_modules | %kxargs -I '{}' llvm-objcopy --only-keep-debug '{}' '{}'.debug
	cat all_modules | %kxargs -I '{}' sh -c 'cd $(dirname {}); llvm-objcopy --add-gnu-debuglink=$(basename {}).debug --strip-debug $(basename {})'
%endif
	cat all_modules | %kxargs -I '{}' llvm-strip --strip-debug {}

# sign modules after stripping
	cat all_modules | %kxargs -r -n16 sh -c "
		for mod; do
		scripts/sign-file sha3-512 certs/signing_key.pem certs/signing_key.x509 \$mod
		rm -f \$mod.sig \$mod.dig
		done
	" DUMMYARG0
	rm -rf all_modules
}

SaveDevel() {
	devel_flavour=$1

	DevelRoot=/usr/src/linux-%{version}-$devel_flavour-%{release}%{disttag}
	TempDevelRoot=%{temp_root}$DevelRoot

	mkdir -p $TempDevelRoot
	cp -fR include $TempDevelRoot
	cp -fR scripts $TempDevelRoot
	cp -fRu --parents $(find . -name 'Makefile*' -o -name 'Kconfig*' -o -name 'Kbuild*') $TempDevelRoot
	cp -fRu kernel/time/timeconst.bc $TempDevelRoot/kernel/time/
	cp -fRu kernel/bounds.c $TempDevelRoot/kernel
	cp -fRu tools/include $TempDevelRoot/tools/
%ifarch %{arm}
	cp -fRu arch/%{target_arch}/tools $TempDevelRoot/arch/%{target_arch}/
%endif

%ifarch %{ix86} %{x86_64}
	cp -fRu arch/x86/kernel/asm-offsets.{c,s} $TempDevelRoot/arch/x86/kernel/
	cp -fRu arch/x86/kernel/asm-offsets_{32,64}.c $TempDevelRoot/arch/x86/kernel/
	cp -fRu arch/x86/purgatory/* $TempDevelRoot/arch/x86/purgatory/
	cp -fRu arch/x86/entry/syscalls/syscall* $TempDevelRoot/arch/x86/entry/syscalls/
	cp -fRu arch/x86/include $TempDevelRoot/arch/x86/
	cp -fRu arch/x86/tools $TempDevelRoot/arch/x86/
%else
	cp -fRu arch/%{target_arch}/kernel/asm-offsets.{c,s} $TempDevelRoot/arch/%{target_arch}/kernel/
	cp -fRu --parents $(find arch/%{target_arch} -name 'include') $TempDevelRoot;
%endif

	cp -fRu .config Module.symvers $TempDevelRoot

# Needed for truecrypt build (Danny)
	cp -fRu drivers/md/dm.h $TempDevelRoot/drivers/md/

# Needed for lirc_gpio (#39004)
	cp -fRu drivers/media/pci/bt8xx/bttv{,p}.h $TempDevelRoot/drivers/media/pci/bt8xx/
	cp -fRu drivers/media/pci/bt8xx/bt848.h $TempDevelRoot/drivers/media/pci/bt8xx/
	cp -fRu drivers/media/pci/bt8xx/btcx-risc.h $TempDevelRoot/drivers/media/common/

# Needed for external dvb tree (#41418)
	cp -fRu drivers/media/dvb-frontends/lgdt330x.h $TempDevelRoot/drivers/media/dvb-frontends/

# orc unwinder needs theese
	cp -fRu tools/build/Build.include $TempDevelRoot/tools/build
	cp -fRu tools/build/fixdep.c $TempDevelRoot/tools/build
	cp -fRu tools/lib/{str_error_r.c,string.c} $TempDevelRoot/tools/lib
	cp -fRu tools/lib/subcmd/* $TempDevelRoot/tools/lib/subcmd
	cp -fRu tools/objtool/* $TempDevelRoot/tools/objtool
	cp -fRu tools/scripts/utilities.mak $TempDevelRoot/tools/scripts

	for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
		 mips mn10300 nds32 nios2 openrisc parisc s390 score sh sparc tile unicore32 xtensa; do
		rm -rf $TempDevelRoot/arch/$i
	done

%if %{with bpftool}
# Needed by systemd build
	tools/bpf/bpftool/bootstrap/bpftool btf dump file vmlinux format c >$TempDevelRoot/include/vmlinux.h
%endif

# Clean the scripts tree, and make sure everything is ok (sanity check)
# running prepare+scripts (tree was already "prepared" in build)
	cd $TempDevelRoot >/dev/null
	%make_build V=0 VERBOSE=0 ARCH=%{target_arch} clean
	cd - >/dev/null

%if %{cross_compiling}
	# make clean keeps hostprogs so out-of-tree modules can build.
	# Those were compiled with HOSTCC and must not ship in a target
	# kernel-devel RPM. Sources stay; rebuild on the target with
	# "make scripts". find+read exits 1 at EOF; keep set -e happy.
	find $TempDevelRoot -type f -exec sh -c '
		for r do
			[ "$(od -An -N4 -tx1 "$r" 2>/dev/null | tr -d " ")" = "7f454c46" ] && rm -f "$r"
		done
		exit 0
	' sh {} +
%endif

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
$DevelRoot/arch/loongarch
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
$DevelRoot/include/Kbuild
$DevelRoot/include/acpi
$DevelRoot/include/asm-generic
$DevelRoot/include/clocksource
$DevelRoot/include/config
$DevelRoot/include/crypto
$DevelRoot/include/cxl
$DevelRoot/include/drm
$DevelRoot/include/dt-bindings
$DevelRoot/include/generated
%optional $DevelRoot/include/hyperv
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
%if %{with bpftool}
$DevelRoot/include/vmlinux.h
%endif
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
	find %{temp_modules}/%{version}-$debug_flavour-%{release}%{disttag}/kernel -name "*.ko.debug" -type f > %{temp_modules}/debug_module_list
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
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/System.map
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/config
%{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/vmlinuz
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
if [ "$1" = "0" ]; then
[ -e %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag}/modules.{alias{,.bin},builtin.bin,dep{,.bin},devname,softdep,symbols{,.bin}} ||:
[ -e /boot/vmlinuz-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/vmlinuz-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/initrd-%{version}-$kernel_flavour-%{release}%{disttag}.img ] && rm -rf /boot/initrd-%{version}-$kernel_flavour-%{release}%{disttag}.img
[ -e /boot/System.map-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/System.map-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/config-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/config-%{version}-$kernel_flavour-%{release}%{disttag}
[ -e /boot/dtb-%{version}-$kernel_flavour-%{release}%{disttag} ] && rm -rf /boot/dtb-%{version}-$kernel_flavour-%{release}%{disttag}
fi

%ifarch %{aarch64}
if [ -d /boot/efi ] && [ -x %{_bindir}/kernel-install ]; then
	%{_bindir}/kernel-install remove %{version}-$kernel_flavour-%{release}%{disttag} || :
fi
%endif

if [ "$1" = "0" ]; then
rm -rf %{_modulesdir}/%{version}-$kernel_flavour-%{release}%{disttag} >/dev/null
fi

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
for a in arm arm64 i386 x86_64 znver1 powerpc riscv loongarch64; do
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
				loongarch64)
					ARCH=loongarch
					SARCH=loongarch
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

# Build bpftool first so SaveDevel can use it
%if %{with bpftool}
%make_build -C tools/bpf/bpftool CC=%{__cc} HOSTCC=%{__cc} ARCH=%{target_arch} LLVM=1 DESTDIR="%{temp_root}" V=0 VERBOSE=0
%make_install -C tools/bpf/bpftool DESTDIR="%{temp_root}" prefix=%{_prefix} bash_compdir=%{_sysconfdir}/bash_completion.d/ mandir=%{_mandir} ARCH=%{target_arch} LLVM=1 install V=0 VERBOSE=0
%endif

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
%make_build -C tools/power/cpupower CC=%{__cc} HOSTCC=%{__cc} LDFLAGS="%{optflags}" CPUFREQ_BENCH=false V=0 VERBOSE=0
%make_install -C tools/power/cpupower CC=%{__cc} HOSTCC=%{__cc} LDFLAGS="%{optflags}" DESTDIR=%{temp_root} libdir=%{_libdir} mandir=%{_mandir} CPUFREQ_BENCH=false V=0 VERBOSE=0
%endif

%ifarch %{ix86} %{x86_64}
%if %{with build_x86_energy_perf_policy}
%make_build -C tools/power/x86/x86_energy_perf_policy CC=%{__cc} HOSTCC=%{__cc} LDFLAGS="-Wl,--build-id=none" V=0 VERBOSE=0
mkdir -p %{temp_root}%{_bindir} %{temp_root}%{_mandir}/man8
%make_install -C tools/power/x86/x86_energy_perf_policy DESTDIR="%{temp_root}" V=0 VERBOSE=0
%endif

%if %{with build_turbostat}
%make_build -C tools/power/x86/turbostat CC=%{__cc} HOSTCC=%{__cc} V=0 VERBOSE=0
mkdir -p %{temp_root}%{_bindir} %{temp_root}%{_mandir}/man8
%make_install -C tools/power/x86/turbostat DESTDIR="%{temp_root}" V=0 VERBOSE=0
%endif
%endif

%if %{with perf}
[ -e %{_sysconfdir}/profile.d/90java.sh ] && . %{_sysconfdir}/profile.d/90java.sh
%make_build -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 NO_LIBTRACEEVENT=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.lld HOSTLD=ld.lld WERROR=0 prefix=%{_prefix} V=0 VERBOSE=0 all man
# Not SMP safe
make -C tools/perf -s HAVE_CPLUS_DEMANGLE=1 NO_LIBTRACEEVENT=1 CC=%{__cc} HOSTCC=%{__cc} LD=ld.lld HOSTLD=ld.lld WERROR=0 prefix=%{_prefix} DESTDIR_SQ=%{temp_root} DESTDIR=%{temp_root} V=0 VERBOSE=0 install install-man
%endif

%if %{with hyperv}
%make_build -C tools/hv -s CC=%{__cc} HOSTCC=%{__cc} prefix=%{_prefix} sbindir=%{_sbindir} V=0 VERBOSE=0
%make_install -C tools/hv -s CC=%{__cc} HOSTCC=%{__cc} prefix=%{_prefix} sbindir=%{_sbindir} DESTDIR=%{temp_root} V=0 VERBOSE=0
mkdir -p %{temp_root}%{_unitdir}
install -c -m 644 %{S:7000} %{S:7002} %{S:7004} %{temp_root}%{_unitdir}/
mkdir -p %{temp_root}%{_udevrulesdir}
install -c -m 644 %{S:7001} %{temp_root}%{_udevrulesdir}/70-hypervkvp.rules
install -c -m 644 %{S:7003} %{temp_root}%{_udevrulesdir}/70-hypervvss.rules
install -c -m 644 %{S:7005} %{temp_root}%{_udevrulesdir}/70-hypervfcopy.rules
%endif

mkdir -p %{temp_root}%{_bindir}
%if ! %{cross_compiling}
cp tools/bpf/resolve_btfids/resolve_btfids %{temp_root}%{_bindir}/
%endif

# We don't make to repeat the depend code at the install phase
%if %{with build_source}
PrepareKernel "" %{release}custom
%make_build -s mrproper
%if ! %{cross_compiling}
cp %{temp_root}%{_bindir}/resolve_btfids tools/bpf/resolve_btfids/
%endif
%endif

###
### install
###

%install
export TOP="$(pwd)"

# We want to be able to test several times the install part
rm -rf %{buildroot}
cp -a %{temp_root} %{buildroot}

# We used to have a copy of PrepareKernel here
# Now, we make sure that the thing in the linux dir is what we want it to be
for i in %{buildroot}%{_modulesdir}/*; do
	rm -f $i/build $i/source
done

# binmerge
%if "%{_bindir}" == "%{_sbindir}"
[ -d %{buildroot}%{_prefix}/sbin ] && mv %{buildroot}%{_prefix}/sbin/* %{buildroot}%{_bindir}/
[ -d %{buildroot}%{_prefix}/sbin ] && rmdir %{buildroot}%{_prefix}/sbin
%endif

# (tpg) let's compress all modules
find %{buildroot}%{_modulesdir} -name "*.ko" -type f | %kxargs zstd --format=zstd --ultra -22 -T0 --rm -f -q

# sniff, if we compressed all the modules, we change the stamp :(
# we really need the depmod -ae here
for i in $(ls -d %{buildroot}%{_modulesdir}/* ); do
	KernelVer=$(basename "$i")
# (tpg) this is needed workaround to not get wrong depmod output
# unless somebody place vmlinuz into modulesdir and the copy it to bootdir on install
	[ -L %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz ] && rm -rf %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz && cp -a %{buildroot}%{_bootdir}/vmlinuz-$KernelVer %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz
	%{_bindir}/depmod -ae -b %{buildroot} -F %{buildroot}%{_modulesdir}/$KernelVer/System.map $KernelVer
	echo $?
# (tpg) see above workaround
	[ -f %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz ] && rm -rf %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz && ln -sr %{_bootdir}/vmlinuz-$KernelVer %{buildroot}%{_modulesdir}/$KernelVer/vmlinuz
done

# need to set extraversion to match srpm again to avoid rebuild
sed -ri "s|^(EXTRAVERSION =).*|\1 -%{release}|" Makefile

%if %{with build_cpupower}
rm -f %{buildroot}%{_libdir}/*.{a,la}
%find_lang cpupower
chmod 0755 %{buildroot}%{_libdir}/libcpupower.so*
mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
install -m644 %{S:300} %{buildroot}%{_unitdir}/cpupower.service
install -m644 %{S:301} %{buildroot}%{_sysconfdir}/sysconfig/cpupower
%endif

# Create directories infastructure
%if %{with build_source}
install -d %{buildroot}%{_kerneldir}

# Package what remains
tar cf - . | tar xf - -C %{buildroot}%{_kerneldir}
chmod -R a+rX %{buildroot}%{_kerneldir}

rm -f %{buildroot}%{_kerneldir}/*.lang

# File lists aren't needed
rm -f %{buildroot}%{_kerneldir}/*_files.* %{buildroot}%{_kerneldir}/README.kernel-sources

# we remove all the source files that we don't ship
# first architecture files
for i in alpha arc avr32 blackfin c6x cris csky frv h8300 hexagon ia64 m32r m68k m68knommu metag microblaze \
	mips nds32 nios2 openrisc parisc s390 score sh sh64 sparc tile unicore32 v850 xtensa mn10300; do
	rm -rf %{buildroot}%{_kerneldir}/arch/$i
	rm -rf %{buildroot}%{_kerneldir}/scripts/dtc/include-prefixes/$i
	rm -rf %{buildroot}%{_kerneldir}/tools/arch/$i
	rm -rf %{buildroot}%{_kerneldir}/tools/testing/selftests/$i
	sed -i -e "/source.*${i}/d" %{buildroot}%{_kerneldir}/crypto/Kconfig
done

%ifnarch %{armx}
	rm -rf %{buildroot}%{_kerneldir}/include/kvm/arm*
	rm -rf %{buildroot}%{_kerneldir}/scripts/dtc/include-prefixes/arm*
%endif

# other misc files
rm -f %{buildroot}%{_kerneldir}/{.config.old,.config.cmd,.gitignore,.lst,.mailmap,.gitattributes,.get_maintainer.ignore}
rm -f %{buildroot}%{_kerneldir}/{.missing-syscalls.d,arch/.gitignore,firmware/.gitignore,.gitattributes}
rm -rf %{buildroot}%{_kerneldir}/.tmp_depmod/

# more cleaning
rm -f %{buildroot}%{_kerneldir}/arch/x86_64/boot/bzImage
cd %{buildroot}%{_kerneldir}
# lots of gitignore files
find -iname ".gitignore" -delete
# clean tools tree
# (mkdir below is just so "make clean" can remove it again without erroring out)
mkdir -p tools/counter/include/linux
%make_build -C tools clean -j1 V=0 VERBOSE=0 || :
%make_build -C tools/build clean -j1 V=0 VERBOSE=0
%make_build -C tools/build/feature clean -j1 V=0 VERBOSE=0
# dont ship generated vdso.so*
%ifarch %{aarch64}
rm -f arch/arm64/kernel/vdso/vdso.so*
%endif
rm -f .cache.mk

# Drop script binaries that can be rebuilt
find tools scripts -executable |while read r; do
	if file $r |grep -q ELF; then
		rm -f $r
	fi
done
cd -

# build_source
%endif

# Set up module packages
cd %{buildroot}
description() {
	local D=$(modinfo -d $1)
	if [[ -z "$D" ]]; then
		local D="The $(modinfo $1 |grep ^name: |cut -d: -f2- |sed -E 's,^[[:space:]]+,,g') module"
	fi
	if [[ -z "$D" ]]; then
		local D="The $(basename $1 |sed -e 's,\.ko.*,,') module"
	fi
	echo $D
}
PERCENT='%%'
# Membership lookup — avoid grep -q in the per-module loop.
# The old nested "for d in $DONE; echo | grep" is O(modules × dirs) and
# with rpm xtrace it filled a 640MB log and timed out aarch64 ABF.
declare -A MODPKG_DIR MODPKG_KO MODPKG_PATH
for _m in %{modules_subpackages}; do
	_pkg=""
	if [[ "$_m" == *=* ]]; then
		_pkg="${_m#*=}"
		_m="${_m%%=*}"
	fi
	if [[ "$_m" == *.ko ]]; then
		MODPKG_KO["$_m"]="${_pkg:-${_m%.ko}}"
	elif [[ "$_m" == */* ]]; then
		if [[ -z "$_pkg" ]]; then
			_base="${_m##*/}"
			if [[ "$_m" == sound/soc/* ]]; then
				_pkg="snd-soc-${_base}"
			else
				_pkg="${_m//\//-}"
			fi
		fi
		MODPKG_PATH["$_m"]="$_pkg"
	else
		MODPKG_DIR["$_m"]="${_pkg:-$_m}"
	fi
done
# Recreate flavour file lists and module specparts so a re-run of
# %install does not duplicate %dir / module paths.
for flavour in %{kernel_flavours}; do
	kf=${TOP}/kernel_files.${flavour}
	[ -f "$kf" ] || continue
	grep -vE '^(%dir /lib/modules/|/lib/modules/.*/kernel)' "$kf" > "${kf}.tmp" && mv "${kf}.tmp" "$kf"
done
rm -f %{specpartsdir}/%{name}-*-modules-*.specpart
modpkg_for_dir() {
	local DN="$1" M suf
	M="${DN##*/}"
	if [[ -n "${MODPKG_DIR[$M]}" ]]; then
		printf '%s\n' "${MODPKG_DIR[$M]}"
		return
	fi
	for suf in "${!MODPKG_PATH[@]}"; do
		if [[ "$DN" == */"$suf" ]]; then
			printf '%s\n' "${MODPKG_PATH[$suf]}"
			return
		fi
	done
}
for flavour in %{kernel_flavours}; do
	unset DONE_PREFIX
	declare -A DONE_PREFIX
	while read d; do
		M="$(basename $d)"
		DN="${d#.}"
		# DTBs are already listed as a tree in CreateFiles(). Walking
		# them here re-adds %dir entries (File listed twice) and
		# basename-matches vendor dirs such as dtb/nvidia into
		# kernel-*-modules-nvidia.
		if [[ "$DN" == */dtb || "$DN" == */dtb/* ]]; then
			continue
		fi
		# Skip subdirectories of a directory already claimed by a split
		# (e.g. kernel/drivers/comedi/drivers after kernel/drivers/comedi).
		p="$DN"
		IS_DONE=false
		while [[ "$p" == */* ]]; do
			p="${p%/*}"
			[[ -n "$p" ]] || break
			if [[ -n "${DONE_PREFIX[$p]}" ]]; then
				IS_DONE=true
				break
			fi
		done
		$IS_DONE && continue
		PKG="$(modpkg_for_dir "$DN")"
		if [[ -n "$PKG" ]]; then
			# Let's see if it's a group of modules (e.g. "all ISDN drivers") or
			# an individual module that has its own directory (e.g. most filesystems,
			# with paths like fs/jfs/jfs.ko)
			if [[ $(ls -1 $d |wc -l) -eq 1 ]]; then
				D="$(description $d/*.ko*) for the ${flavour} kernel"
			else
				D="$PKG modules for the ${flavour} kernel"
			fi
			SP="%{specpartsdir}/%{name}-${flavour}-modules-${PKG}.specpart"
			if ! [ -e "$SP" ]; then
				cat >"$SP" <<EOF
${PERCENT}package -n %{name}-${flavour}-modules-${PKG}
Summary:	${D}
Group:		System/Kernel and hardware
Requires:	%{name}-${flavour} = %{EVRD}
Provides:	installonlypkg(kernel-module)
Requires(posttrans,postun):	kmod
EOF
				if [ "$M" = "hfs" -a "${flavour}" = "desktop" ]; then
					echo "Obsoletes: hfsutils < 3.2.6-42" >>$SP
				fi
				cat >>"$SP" <<EOF
${PERCENT}description -n %{name}-${flavour}-modules-${PKG}
${D}

${PERCENT}postun -n %{name}-${flavour}-modules-${PKG}
[ -x %{_bindir}/depmod ] && %{_bindir}/depmod -A %{version}-$flavour-%{release}%{disttag}

${PERCENT}files -n %{name}-${flavour}-modules-${PKG}
EOF
			fi
			echo "${DN}" >>"$SP"
			DONE_PREFIX["$DN"]=1
		else
			echo "%%dir ${DN}" >>${TOP}/kernel_files.${flavour}
		fi
	done < <(find .%{_modulesdir}/%{version}-${flavour}-%{release}%{disttag}/kernel -type d)
	while read f; do
		M="$(basename $f)"
		BN="$(echo $M |sed -e 's,\.ko.*,,')"
		FN="${f#.}"
		# O(depth) parent walk instead of grepping every DONE prefix
		p="$FN"
		IS_DONE=false
		while [[ "$p" == */* ]]; do
			p="${p%/*}"
			[[ -n "$p" ]] || break
			if [[ -n "${DONE_PREFIX[$p]}" ]]; then
				IS_DONE=true
				break
			fi
		done
		$IS_DONE && continue
		if [[ -n "${MODPKG_KO[${BN}.ko]}" ]]; then
			PKG="${MODPKG_KO[${BN}.ko]}"
			if [[ "$PKG" != "$BN" ]]; then
				D="$PKG modules for the ${flavour} kernel"
			else
				D="$(description $f) for the ${flavour} kernel"
			fi
			SP="%{specpartsdir}/%{name}-${flavour}-modules-${PKG}.specpart"
			if ! [ -e "$SP" ]; then # Deal with e.g. net/can and drivers/can going together
				cat >"$SP" <<EOF
${PERCENT}package -n %{name}-${flavour}-modules-${PKG}
Summary:	${D}
Group:		System/Kernel and hardware
Requires:	%{name}-${flavour} = %{EVRD}
Provides:	installonlypkg(kernel-module)
Requires(posttrans,postun):	kmod
EOF
				cat >>"$SP" <<EOF
${PERCENT}description -n %{name}-${flavour}-modules-${PKG}
${D}

${PERCENT}postun -n %{name}-${flavour}-modules-${PKG}
[ -x %{_bindir}/depmod ] && %{_bindir}/depmod -A %{version}-$flavour-%{release}%{disttag}

${PERCENT}files -n %{name}-${flavour}-modules-${PKG}
EOF
			fi
			echo "${FN}" >>"$SP"
		else
			echo "${FN}" >>${TOP}/kernel_files.${flavour}
		fi
	done < <(find .%{_modulesdir}/%{version}-${flavour}-%{release}%{disttag} -type f -name "*.ko*")
done

%if %{with build_source}
%files -n %{name}-source
%if ! %{cross_compiling}
%{_bindir}/resolve_btfids
%endif
%dir %{_kerneldir}
%dir %{_kerneldir}/arch
%dir %{_kerneldir}/include
%dir %{_kerneldir}/certs
%{_kerneldir}/.clang-format
%optional %{_kerneldir}/.clippy.toml
%{_kerneldir}/.cocciconfig
%{_kerneldir}/.editorconfig
%{_kerneldir}/.pylintrc
%{_kerneldir}/Documentation
%{_kerneldir}/arch/Kconfig
%{_kerneldir}/arch/arm
%{_kerneldir}/arch/arm64
%{_kerneldir}/arch/loongarch
%{_kerneldir}/arch/powerpc
%{_kerneldir}/arch/riscv
%{_kerneldir}/arch/um
%{_kerneldir}/arch/x86
%{_kerneldir}/block
%{_kerneldir}/crypto
%{_kerneldir}/drivers
%{_kerneldir}/fs
%{_kerneldir}/certs/*
%{_kerneldir}/include/Kbuild
%{_kerneldir}/include/acpi
%{_kerneldir}/include/asm-generic
%{_kerneldir}/include/clocksource
%{_kerneldir}/include/crypto
%{_kerneldir}/include/cxl
%{_kerneldir}/include/drm
%{_kerneldir}/include/dt-bindings
%optional %{_kerneldir}/include/hyperv
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
%optional %{_bindir}/perf-read-vdso32
%{_bindir}/trace
%dir %{_prefix}/libexec/perf-core
%{_prefix}/libexec/perf-core/*
%doc %{_mandir}/man[1-8]/perf*
%{_sysconfdir}/bash_completion.d/perf
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
%{_libexecdir}/cpupower
%{_libdir}/libcpupower.so.1
%{_libdir}/libcpupower.so.1.0.1
%{_unitdir}/cpupower.service
%doc %{_mandir}/man[1-8]/cpupower*
%{_datadir}/bash-completion/completions/cpupower
%config(noreplace) %{_sysconfdir}/sysconfig/cpupower
%config(noreplace) %{_sysconfdir}/cpupower-service.conf

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
%endif
