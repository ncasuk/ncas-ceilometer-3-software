#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

gws_path=/gws/pw/j07/ncas_obs_vol1

netcdf_path=${gws_path}/iao/processing/ncas-ceilometer-3/netcdf_files
datapath=${gws_path}/iao/raw_data/ncas-ceilometer-3/incoming
logfilepath=${gws_path}/iao/logs/ncas-ceilometer-3

metadata_file=${SCRIPT_DIR}/../metadata.csv


datadate=$1  # YYYYmmdd
conda_env=${2:-netcdf}

conda activate ${conda_env}

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
