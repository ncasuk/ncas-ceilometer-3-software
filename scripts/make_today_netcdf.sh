#!/bin/bash
# 
# optional command line argument - conda env

conda_env=${1:-netcdf}

# today date

year=$(date +"%Y")
month=$(date +"%m")
day=$(date +"%d")

# call make_netcdf script

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

${SCRIPT_DIR}/make_netcdf.sh ${year}${month}${day} ${conda_env}
