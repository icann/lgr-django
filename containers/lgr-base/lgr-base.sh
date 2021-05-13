#!/bin/sh

# As lgr-django is a complex installation process. A shell script is more easy
# to read and modify

# Criticaly exit script if one command in error
set -e

# VARIABLE DECLARATION
## pythonMinor version set the python minor version (ex.: 3.7)
pythonMinorVersion='3.7'
## unicodeURL set the repository git use for cloning
unicodeURL='https://github.com/unicode-org/icu.git'
lgrBaseDir='/var/www/lgr'
lgrPersistantDir='storage'

## Get the last patch version for the specify python version
pythonPatchVersion=$( curl -s https://www.python.org/ftp/python/ | \
                    cut -d \" -f 2 | \
                    sed 's|/||g' | \
                    grep $pythonMinorVersion. | \
                    sort -V | \
                    tail -1 )

## pythonURL is the URL where the python source file are located
pythonURL="https://www.python.org/ftp/python/$pythonPatchVersion/Python-$pythonPatchVersion.tar.xz"

## buildDir will contain all file needed to compile application
buildDir=$(mktemp -d)


# INTALLATION & CONFIGURATION
printf "Phase1: Install required applications\n"


printf "\tInstall compilation tools\t"
# Install compilation tools for django and icu4c
dnf -qy install --enablerepo powertools \
  "@development tools" \
  bzip2-devel \
  ncurses-devel \
  sqlite-devel \
  readline-devel \
  tk-devel \
  gdbm-devel \
  libdb-devel \
  libpcap-devel \
  xz-devel \
  expat-devel \
  zlib-devel \
  openssl-devel \
  libffi-devel

printf "OK\n"


printf "\tInstall the various lgr-django dependancies\t"
# Install various dependancies for lg-django
dnf -qy install \
  libxml2 \
  libicu \
  tcl

printf "OK\n"


printf "\tInstall lgr-django python dependancy\t"
# Download latest path for the define minor version of python
wget $pythonURL -qO $buildDir/python.tar.xz

# Unpack the tar file
tar -xf $buildDir/python.tar.xz -C $buildDir

# Compile & install python
cd $buildDir/Python-$pythonPatchVersion
./configure -q --enable-optimizations
make -s altinstall &>/dev/null
cd ~

# Create genericly named link to execute python
ln -s /usr/local/bin/python$pythonMinorVersion /usr/local/bin/python

# Validate python installation
/usr/local/bin/python -V | grep -q $pythonPatchVersion

printf "OK\n"

printf "\tFix xlocale.h library\t"
# Link the locale.h library to the xlocale.h
ln -sf /usr/include/locale.h /usr/include/xlocale.h
printf "OK\n"

printf "\tInstall lgr-django unicodes dependancies\n"
# Clone unicode repository
git clone -q $unicodeURL $buildDir/icu

# unicodeVersions define all unicode version use in LGR
unicodeVersion="
  6.3.0
  6.0.0
  6.1.0
  6.2.0
  7.0.0
  8.0.0
  9.0.0
  10.0.0"

# Compile every icu4c version from the local LGR git repo
for i in $unicodeVersion
do
  #Clean previous build
  git -C $buildDir/icu clean --quiet -d -fx
  case $i in
    6.0.0)
      icu4cBuildPath="$buildDir/icu/build"
      unicodeTag=46
      unicodeRelease='icu-maint/maint-4-6'
      ;;
    6.1.0)
      icu4cBuildPath="$buildDir/icu/build"
      unicodeTag=49
      unicodeRelease='icu-maint/maint-49'
      ;;
    6.2.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=50
      unicodeRelease='release-50-1-2'
      ;;
    6.3.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=52
      unicodeRelease='release-52-1'
      ;;
    7.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=54
      unicodeRelease='release-54-1'
      ;;
    8.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=56
      unicodeRelease='release-56-1'
      ;;
    9.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=58
      unicodeRelease='release-58-2'
      ;;
    10.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=60
      unicodeRelease='release-60-2'
      ;;
    *)
      # Should never happend as no external input is used
      exit 1
      ;;
  esac
  printf "\t\tBuild icu4c-$i\t"
  # Checkout in the good branch
  git -C $buildDir/icu checkout --quiet $unicodeRelease
  # Create the build directory and ...
  mkdir $icu4cBuildPath
  cd $icu4cBuildPath
  # Build inside it
  ../source/runConfigureICU Linux &>/dev/null
  make &>/dev/null
  make install &>/dev/null
  #../source/runConfigureICU Linux
  #make
  #make install
  # Return to the home directory
  cd ~
  printf "OK\n"
done

printf "\tAdd Unicode shared library path\t"
# So that LGR can use the icu4c library
echo '/usr/local/lib' > /etc/ld.so.conf.d/lgr.conf
printf "OK\n"

printf "\nPhase2: Cleanup files and unused production application\n"
# Clean up unuse file and application to lower the docker size
printf "\tRemove Build Directory\t"
rm -fr $buildDir
printf "OK\n"
printf "\tRemove compilation tools\t"
dnf -qy remove --enablerepo powertools \
  "@development tools" \
  bzip2-devel \
  ncurses-devel \
  sqlite-devel \
  readline-devel \
  tk-devel \
  gdbm-devel \
  libdb-devel \
  libpcap-devel \
  xz-devel \
  expat-devel \
  zlib-devel \
  openssl-devel \
  libffi-devel
printf "OK\n"
printf "\tClean up dnf cache files\t"
dnf -qy clean all
rm -fr /var/cache/dnf
printf "OK\n"
