%define debug_package %{nil}

# Defining the package namespace
%global ns_name ea
%global ns_dir /opt/cpanel
%global pkg ruby24
%global gem_name nokogiri

# Force Software Collections on
%global _scl_prefix %{ns_dir}
%global scl %{ns_name}-%{pkg}
# HACK: OBS Doesn't support macros in BuildRequires statements, so we have
#       to hard-code it here.
# https://en.opensuse.org/openSUSE:Specfile_guidelines#BuildRequires
%global scl_prefix %{scl}-
%{?scl:%scl_package rubygem-%{gem_name}}

# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4590 for more details
%define release_prefix 2

%define mainver     1.10.9

%global gem_name     nokogiri
%global gemdir      %{gem_dir}
%global geminstdir  %{gem_instdir}
%global gemsodir    %{gem_extdir_mri}/lib

# Note for packager:
# Nokogiri 1.4.3.1 gem says that Nokogiri upstream will
# no longer support ruby 1.8.6 after 2010-08-01, so
# it seems that 1.4.3.1 is the last version for F-13 and below.

Summary:    An HTML, XML, SAX, and Reader parser
Name:       %{?scl:%scl_prefix}rubygem-%{gem_name}
Version:    %{mainver}
Release:    %{release_prefix}%{?dist}.cpanel
Group:      Development/Languages
License:    MIT
URL:        http://nokogiri.rubyforge.org/nokogiri/
Source0:    https://rubygems.org/gems/%{gem_name}-%{mainver}.gem

# Shut down libxml2 version unmatching warning
Patch0:    rubygem-nokogiri-1.6.6.4-shutdown-libxml2-warning.patch

Requires:       %{?scl_prefix}ruby(rubygems)
Requires:       %{?scl_prefix}ruby(release)
%{?scl:Requires:%scl_runtime}

BuildRequires:  libxml2-devel
BuildRequires:  libxslt-devel
BuildRequires:  %{?scl_prefix}ruby
BuildRequires:  %{?scl_prefix}ruby(rubygems)
BuildRequires:  %{?scl_prefix}rubygems-devel
BuildRequires:  %{?scl_prefix}ruby-devel
BuildRequires:  scl-utils
BuildRequires:  scl-utils-build
%{?scl:BuildRequires: %{scl}-runtime}
Provides:       %{?scl_prefix}rubygem(%{gem_name}) = %{version}

# Filter out nokogiri.so
%{?filter_provides_in: %filter_provides_in %{gemsodir}/%{gem_name}/.*\.so$}
%{?filter_setup}

%description
Nokogiri parses and searches XML/HTML very quickly, and also has
correctly implemented CSS3 selector support as well as XPath support.

Nokogiri also features an Hpricot compatibility layer to help ease the change
to using correct CSS and XPath.

%package    doc
Summary:    Documentation for %{name}
Group:      Documentation
Requires:   %{name} = %{version}-%{release}

%description    doc
This package contains documentation for %{name}.

%package    -n %{?scl:%scl_prefix}ruby-%{gem_name}
Summary:    Non-Gem support package for %{gem_name}
Group:      Development/Languages
Requires:   %{name} = %{version}-%{release}

%description    -n %{?scl:%scl_prefix}ruby-%{gem_name}
This package provides non-Gem support for %{gem_name}.

%prep
%setup -q -T -c
%{?scl:scl enable %{scl} - << \EOF}

# Gem repack
TOPDIR=$(pwd)
mkdir tmpunpackdir
pushd tmpunpackdir

gem unpack %{SOURCE0}
cd %{gem_name}-%{version}

# patches
%patch0 -p1

gem specification -l --ruby %{SOURCE0} > %{gem_name}.gemspec

# remove bundled external libraries
sed -i \
    -e 's|, "ports/archives/[^"][^"]*"||g' \
    -e 's|, "ports/patches/[^"][^"]*"||g' \
    %{gem_name}.gemspec
# Actually not needed when using system libraries
sed -i -e '\@mini_portile@d' %{gem_name}.gemspec

# Ummm...
env LANG=ja_JP.UTF-8 gem build %{gem_name}.gemspec
mv %{gem_name}-%{version}.gem $TOPDIR

popd
rm -rf tmpunpackdir
%{?scl:EOF}

%build
%{?scl:scl enable %{scl} - << \EOF}

# 1.6.0 needs this
export NOKOGIRI_USE_SYSTEM_LIBRARIES=yes

%gem_install

# Remove precompiled Java .jar file
rm -f ./%{geminstdir}/lib/*.jar
# For now remove JRuby support
rm -rf ./%{geminstdir}/ext/java
%{?scl:EOF}

%install
mkdir -p %{buildroot}%{gemdir}
cp -a ./%{gemdir}/* %{buildroot}%{gemdir}

# Remove backup file
find %{buildroot} -name \*.orig_\* | xargs rm -vf

# move arch dependent files to %%gem_extdir
mkdir -p %{buildroot}%{gem_extdir_mri}
cp -a ./%{gem_extdir_mri}/* %{buildroot}%{gem_extdir_mri}/

pushd %{buildroot}
rm -f .%{gem_extdir_mri}/{gem_make.out,mkmf.log}
popd

# move bin/ files
mkdir -p %{buildroot}%{_bindir}
cp -pa .%{_bindir}/* \
        %{buildroot}%{_bindir}/

# remove all shebang
for f in $(find %{buildroot}%{geminstdir} -name \*.rb)
do
    sed -i -e '/^#!/d' $f
    chmod 0644 $f
done

# cleanups
rm -rf %{buildroot}%{geminstdir}/ext/%{gem_name}/
rm -rf %{buildroot}%{geminstdir}/tmp/
rm -f %{buildroot}%{geminstdir}/{.autotest,.require_paths,.gemtest,.travis.yml}
rm -f %{buildroot}%{geminstdir}/appveyor.yml
rm -f %{buildroot}%{geminstdir}/.cross_rubies
rm -f %{buildroot}%{geminstdir}/{build_all,dependencies.yml,test_all}
rm -f %{buildroot}%{geminstdir}/.editorconfig
rm -rf %{buildroot}%{geminstdir}/suppressions/
rm -rf %{buildroot}%{geminstdir}/patches/

%files
%defattr(-,root, root,-)
%{_bindir}/%{gem_name}
%{gem_extdir_mri}/
%dir    %{geminstdir}/
%doc    %{geminstdir}/[A-Z]*
# %exclude %{geminstdir}/Rakefile
# %exclude %{geminstdir}/Gemfile
%{geminstdir}/bin/
%{geminstdir}/lib/
%{gemdir}/specifications/%{gem_name}-%{mainver}.gemspec
%exclude %{gem_cache}

%files  doc
%defattr(-,root,root,-)
# %{geminstdir}/Rakefile
# %{geminstdir}/tasks/
# %{geminstdir}/test/
%{gemdir}/doc/%{gem_name}-%{mainver}

%changelog
* Tue Dec 28 2021 Dan Muey <dan@cpanel.net> - 1.10.9-2
- ZC-9589: Update DISABLE_BUILD to match OBS

* Fri Mar 06 2020 Tim Mullin <tim@cpanel.net> 1.10.9-1
- EA-8901: Update to 1.10.9 from upstream

* Mon Apr 17 2017 Rishwanth Yeddula <rish@cpanel.net> 1.7.1-1
- initial packaging
