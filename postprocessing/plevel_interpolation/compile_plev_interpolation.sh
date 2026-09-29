#!/usr/bin/env bash
#Script that compiles the plev.x executable

cd ./exec

source $GFDL_BASE/src/extra/env/$GFDL_ENV

../bin/mkmf -p plev.x -t ../bin/mkmf.template.${GFDL_MKMF_TEMPLATE:-ubuntu_conda} -c "-Duse_netCDF" -a ../src ../src/path_names ../src/shared/mpp/include ../src/shared/include

make -f Makefile
