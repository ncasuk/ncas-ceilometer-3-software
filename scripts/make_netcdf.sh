#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

#netcdf_path="/gws/nopw/j04/ncas_obs/iao/processing/ncas-ceilometer-3/netcdf_files"
netcdf_path="/home/users/earjham"
datapath="/gws/nopw/j04/ncas_obs/iao/raw_data/ncas-ceilometer-3/incoming"
logfilepath="/home/users/earjham/logs/nc3logs"
metadata_file=${SCRIPT_DIR}/../metadata.csv


datadate=$1  # YYYYmmdd

python ${SCRIPT_DIR}/../process_ceilometer.py ${datapath}/${datadate}_ceilometer.csv -m ${metadata_file} -o ${netcdf_path} -v


if [ -f ${netcdf_path}/ncas-ceilometer-3_iao_${datadate}_aerosol-backscatter_*.nc ]
then 
  ab_file_exists=True
else
  ab_file_exists=False
fi

if [ -f ${netcdf_path}/ncas-ceilometer-3_iao_${datadate}_cloud-base_*.nc ]
then 
  cb_file_exists=True
else
  cb_file_exists=False
fi


cat << EOF | sed -e 's/#.*//; s/  *$//' > ${logfilepath}/${datadate}.txt
Date: $(date -u)
aerosol-backscatter file created: ${ab_file_exists}
cloud-base file created: ${cb_file_exists}
EOF
