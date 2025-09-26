#!/bin/sh

# As lgr-django is a complex installation process. A shell script is more easy
# to read and modify

# Critically exit script if one command in error
set -e

# INSTALLATION & CONFIGURATION
printf "\tInstall the various lgr-django dependencies\t"
dnf -qy install \
  gettext \
  git \
  libicu \
  libxml2 \
  procps-ng \
  tcl
printf "OK\n"

printf "\tFix xlocale.h library\t"
# Link the locale.h library to the xlocale.h
ln -sf /usr/include/locale.h /usr/include/xlocale.h
printf "OK\n"

printf "\tInstall compilation tools\t"
dnf -qy install \
  gcc-c++ \
  expat-devel \
  libffi-devel \
  zlib-devel
printf "OK\n"

printf "\tInstall lgr-django unicodes dependencies\n"
## buildDir will contain all files needed to compile application
buildDir=$(mktemp -d)

## unicodeURL set the repository git use for cloning
unicodeURL='https://github.com/unicode-org/icu.git'

# Clone unicode repository
git clone -q $unicodeURL $buildDir/icu

# unicodeVersions define all unicode version use in LGR
unicodeVersion="15.1.0"

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
    12.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=64
      unicodeRelease='release-64-1'
      ;;
    14.0.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=71
      unicodeRelease='release-71-1'
      ;;
    15.1.0)
      icu4cBuildPath="$buildDir/icu/icu4c/build"
      unicodeTag=74
      unicodeRelease='release-74-2'
      ;;
    *)
      # Should never happen as no external input is used
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

  # Return to the home directory
  cd ~
  printf "OK\n"
done

printf "\tAdd Unicode shared library path\t"
# So that LGR can use the icu4c library
echo '/usr/local/lib' > /etc/ld.so.conf.d/lgr.conf
printf "OK\n"

printf "\nPhase2: Cleanup files and unused production application\n"
# Clean up unused file and application to lower the docker size
printf "\tRemove Build Directory\t"
rm -fr $buildDir
printf "OK\n"

printf "\tRemove compilation tools\t"
dnf -qy remove \
  gcc-c++ \
  expat-devel \
  libffi-devel \
  zlib-devel
printf "OK\n"

printf "\tClean up dnf cache files\t"
dnf -qy clean all || true
rm -fr /var/cache/dnf || true
printf "OK\n"
