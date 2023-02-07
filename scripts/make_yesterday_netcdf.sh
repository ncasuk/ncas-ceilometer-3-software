#!/bin/bash
# 
# optional command line argument - conda env

conda_env=${1:-netcdf}

# yesterday date

year=$(date --date="yesterday" +"%Y")
month=$(date --date="yesterday" +"%m")
day=$(date --date="yesterday" +"%d")

# call make_netcdf script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

${SCRIPT_DIR}/make_netcdf.sh ${year}${month}${day} ${conda_env}
