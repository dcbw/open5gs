Name:           open5gs
Version:        2.7.5
Release:        2.dcbw%{?dist}
Summary:        Implementation for 5G Core and EPC
License:        AGPL v3.0

URL:            https://open5gs.org

BuildRequires:  git gcc-c++ meson cmake mongo-c-driver-devel python3 ninja-build glibc-headers
BuildRequires:  pkgconf-pkg-config gnutls-devel libtalloc-devel libcurl-devel libyaml-devel openssl-devel
BuildRequires:  lksctp-tools-devel libnghttp2-devel libmicrohttpd-devel libtins-devel
BuildRequires:  nodejs-npm nodejs-devel flex bison libgcrypt-devel libidn-devel lksctp-tools-devel
BuildRequires:  systemd-devel
%{?sysusers_requires_compat}


Requires:       mongodb-org

Source0: %{name}-%{version}.tar.bz2
Source1: open5gs.conf
Source2: open5gs-nolock.conf
Source3: open5gs-subprojects.tar.gz
Source4: open5gs-webui.service
Source5: node_modules.bz2
Source6: package-lock.json
Source7: package.json
Source8: freeDiameter-libs-rename.patch

%description
Open5GS is a C-language Open Source implementation for
5G Core and EPC, i.e. the core network of LTE/NR network.

%package        webui
Summary:        Web UI for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       nodejs mongodb-org

%description    webui
Web UI for %{name}.


%prep
%autosetup -p1
tar xzf %{SOURCE3} -C subprojects/
tar xjf %{SOURCE5} -C webui/
cp %{SOURCE6} %{SOURCE7} webui/
patch -p1 < %{SOURCE8}

%build
%global optflags %(echo %optflags | sed 's|-Wp,-D_GLIBCXX_ASSERTIONS||g')

# no rpath
find . -name 'meson.build' -exec sed -i '/install_rpath/d' {} +

# modern glibc
sed -i '/sys\/sysctl.h/d' lib/ipfw/*.c
sed -i '1 i #include <cstdint>' src/upf/arp-nd.cpp
export CFLAGS='%{optflags} -I/usr/include/uClibc/'

# external freeDiameter
#sed -i 's|^freeDiameter|#freeDiameter|' lib/diameter/common/meson.build
#sed -i 's|^libfdcore_dep = |#libfdcore_dep|' lib/diameter/common/meson.build
#sed -i "/^#libfdcore_dep/i libfdcore_dep = [cc.find_library(['libfdcore'], dirs : ['%{_libdir}'])]" lib/diameter/common/meson.build
#sed -i "/^#libfdcore_dep/a libfdcore_dep += cc.find_library(['libfdproto'], dirs : ['%{_libdir}'])" lib/diameter/common/meson.build
#sed -i "/^#libfdcore_dep/a libfdcore_dep += cc.find_library(['libgnutls'], dirs : ['%{_libdir}'])" lib/diameter/common/meson.build

%meson
%meson_build

# NOTE: webui only creates admin account when running the upstream
# custom install script, or building from sources. Since we don't do
# that users have to create the admin account manually.
#
# cat << EOF > ./account.js
# db = db.getSiblingDB('open5gs')
# cursor = db.accounts.find()
# if ( cursor.count() == 0 ) {
#     // admin/1423
#     db.accounts.insert({ salt: 'f5c15fa72622d62b6b790aa8569b9339729801ab8bda5d13997b5db6bfc1d997', hash: '402223057db5194899d2e082aeb0802f6794622e1cbc47529c419e5a603f2cc592074b4f3323b239ffa594c8b756d5c70a4e1f6ecd3f9f0d2d7328c4cf8b1b766514effff0350a90b89e21eac54cd4497a169c0c7554a0e2cd9b672e5414c323f76b8559bc768cba11cad2ea3ae704fb36abc8abc2619231ff84ded60063c6e1554a9777a4a464ef9cfdfa90ecfdacc9844e0e3b2f91b59d9ff024aec4ea1f51b703a31cda9afb1cc2c719a09cee4f9852ba3cf9f07159b1ccf8133924f74df770b1a391c19e8d67ffdcbbef4084a3277e93f55ac60d80338172b2a7b3f29cfe8a36738681794f7ccbe9bc98f8cdeded02f8a4cd0d4b54e1d6ba3d11792ee0ae8801213691848e9c5338e39485816bb0f734b775ac89f454ef90992003511aa8cceed58a3ac2c3814f14afaaed39cbaf4e2719d7213f81665564eec02f60ede838212555873ef742f6666cc66883dcb8281715d5c762fb236d72b770257e7e8d86c122bb69028a34cf1ed93bb973b440fa89a23604cd3fefe85fbd7f55c9b71acf6ad167228c79513f5cfe899a2e2cc498feb6d2d2f07354a17ba74cecfbda3e87d57b147e17dcc7f4c52b802a8e77f28d255a6712dcdc1519e6ac9ec593270bfcf4c395e2531a271a841b1adefb8516a07136b0de47c7fd534601b16f0f7a98f1dbd31795feb97da59e1d23c08461cf37d6f2877d0f2e437f07e25015960f63', username: 'admin', roles: [ 'admin' ], "__v" : 0})
# }
# EOF
# $ mongosh ./account.js
#
pushd webui/
  npm install
  cat /builddir/.npm/_logs/* || true
  npm run build
popd


%install
%meson_install

%if 0%{?fedora} >= 42
install -p -D -m 0644 %{SOURCE1} %{buildroot}%{_sysusersdir}/%{name}.conf
%else
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/%{name}.conf
%endif

# These need to be readable/writable by open5gs:open5gs
install -d %{buildroot}/%{_sysconfdir}/freeDiameter
install -d %{buildroot}%{_localstatedir}/log/open5gs

install -d %{buildroot}/%{_sysconfdir}/open5gs
install -d %{buildroot}/%{_unitdir}
install -d %{buildroot}/%{_sysconfdir}/logrotate.d
install -m 0644 redhat-linux-build/configs/logrotate/open5gs %{buildroot}%{_sysconfdir}/logrotate.d/
#
install -m 0644 redhat-linux-build/configs/open5gs/hss.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/freeDiameter/hss.conf %{buildroot}/%{_sysconfdir}/freeDiameter/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-hssd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/mme.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/freeDiameter/mme.conf %{buildroot}/%{_sysconfdir}/freeDiameter/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-mmed.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/sgwc.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-sgwcd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/sgwu.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-sgwud.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/amf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-amfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/upf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-upfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/nrf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-nrfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/ausf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-ausfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/udm.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-udmd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/udr.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-udrd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/udr.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-udrd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/bsf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-bsfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/pcrf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/freeDiameter/pcrf.conf %{buildroot}/%{_sysconfdir}/freeDiameter/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-pcrfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/smf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/freeDiameter/smf.conf %{buildroot}/%{_sysconfdir}/freeDiameter/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-smfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/nssf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-nssfd.service %{buildroot}/%{_unitdir}/
#
install -m 0644 redhat-linux-build/configs/open5gs/pcf.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-pcfd.service %{buildroot}/%{_unitdir}/

#
install -m 0644 redhat-linux-build/configs/open5gs/scp.yaml %{buildroot}/%{_sysconfdir}/open5gs/
install -m 0644 redhat-linux-build/configs/systemd/open5gs-scpd.service %{buildroot}/%{_unitdir}/

# webui
mkdir -p %{buildroot}/usr/lib/node_modules
mv webui %{buildroot}/usr/lib/node_modules/%{name}
install -m 0644 %{SOURCE4} %{buildroot}/%{_unitdir}/

ls -al %{buildroot}/%{_libdir}/freeDiameter/

%ldconfig_scriptlets

%pre
%sysusers_create_compat %{SOURCE1}

%post
%systemd_post open5gs-hssd.service
%systemd_post open5gs-mmed.service
%systemd_post open5gs-sgwcd.service
%systemd_post open5gs-sgwud.service
%systemd_post open5gs-amfd.service
%systemd_post open5gs-upfd.service
%systemd_post open5gs-nrfd.service
%systemd_post open5gs-ausfd.service
%systemd_post open5gs-udmd.service
%systemd_post open5gs-udrd.service
%systemd_post open5gs-bsfd.service
%systemd_post open5gs-pcrfd.service
%systemd_post open5gs-smfd.service
%systemd_post open5gs-nssfd.service
%systemd_post open5gs-pcfd.service
%systemd_post open5gs-scpd.service

%post webui
%systemd_post open5gs-webui.service

%preun
%systemd_preun open5gs-hssd.service
%systemd_preun open5gs-mmed.service
%systemd_preun open5gs-sgwcd.service
%systemd_preun open5gs-sgwud.service
%systemd_preun open5gs-amfd.service
%systemd_preun open5gs-upfd.service
%systemd_preun open5gs-nrfd.service
%systemd_preun open5gs-ausfd.service
%systemd_preun open5gs-udmd.service
%systemd_preun open5gs-udrd.service
%systemd_preun open5gs-bsfd.service
%systemd_preun open5gs-pcrfd.service
%systemd_preun open5gs-smfd.service
%systemd_preun open5gs-nssfd.service
%systemd_preun open5gs-pcfd.service
%systemd_preun open5gs-scpd.service

%preun webui
%systemd_preun open5gs-webui.service

%postun
%systemd_postun open5gs-hssd.service
%systemd_postun open5gs-mmed.service
%systemd_postun open5gs-sgwcd.service
%systemd_postun open5gs-sgwud.service
%systemd_postun open5gs-amfd.service
%systemd_postun open5gs-upfd.service
%systemd_postun open5gs-nrfd.service
%systemd_postun open5gs-ausfd.service
%systemd_postun open5gs-udmd.service
%systemd_postun open5gs-udrd.service
%systemd_postun open5gs-bsfd.service
%systemd_postun open5gs-pcrfd.service
%systemd_postun open5gs-smfd.service
%systemd_postun open5gs-nssfd.service
%systemd_postun open5gs-pcfd.service
%systemd_postun open5gs-scpd.service

%postun webui
%systemd_postun open5gs-webui.service

%files
%doc README.md
%license LICENSE
%{_bindir}/*
%{_libdir}/*.so*
%dir %{_libdir}/freeDiameter
%{_libdir}/freeDiameter/*.fdx
%dir %{_sysconfdir}/open5gs
%dir %{_sysconfdir}/freeDiameter
%config(noreplace) %{_sysconfdir}/freeDiameter/*.conf
%config(noreplace) %{_sysconfdir}/open5gs/*.yaml
%{_unitdir}/open5gs-hssd.service
%{_unitdir}/open5gs-mmed.service
%{_unitdir}/open5gs-sgwcd.service
%{_unitdir}/open5gs-sgwud.service
%{_unitdir}/open5gs-amfd.service
%{_unitdir}/open5gs-upfd.service
%{_unitdir}/open5gs-nrfd.service
%{_unitdir}/open5gs-ausfd.service
%{_unitdir}/open5gs-udmd.service
%{_unitdir}/open5gs-udrd.service
%{_unitdir}/open5gs-bsfd.service
%{_unitdir}/open5gs-pcrfd.service
%{_unitdir}/open5gs-smfd.service
%{_unitdir}/open5gs-nssfd.service
%{_unitdir}/open5gs-pcfd.service
%{_unitdir}/open5gs-scpd.service
%{_sysusersdir}/%{name}.conf
%attr(755,open5gs,open5gs) %dir %{?_localstatedir}/log/open5gs
%config(noreplace) %{_sysconfdir}/logrotate.d/open5gs
%ghost %dir %{_rundir}/open5gs-mmed
%ghost %dir %{_rundir}/open5gs-sgwcd
%ghost %dir %{_rundir}/open5gs-smfd
%ghost %dir %{_rundir}/open5gs-amfd
%ghost %dir %{_rundir}/open5gs-sgwud
%ghost %dir %{_rundir}/open5gs-upfd
%ghost %dir %{_rundir}/open5gs-hssd
%ghost %dir %{_rundir}/open5gs-pcrfd
%ghost %dir %{_rundir}/open5gs-nrfd
%ghost %dir %{_rundir}/open5gs-ausfd
%ghost %dir %{_rundir}/open5gs-udmd
%ghost %dir %{_rundir}/open5gs-udrd

%files webui
/usr/lib/node_modules/%{name}
%{_unitdir}/open5gs-webui.service

%changelog
* Sun Jun  8 2025 Dan Williams <dan@ioncontrol.co> - 2.7.5
- Update to 2.7.5

* Fri Oct 02 2020 Cristian Balint <cristian.balint@gmail.com>
- git update releases
