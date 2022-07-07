# ncas-ceilometer-3-software

Campbell Scientific CS135 : https://www.campbellsci.com/cs135 

Code for creating AMOF-compliant netCDF files for ncas-ceilometer-3 instrument.

Uses [ncas_amof_netcdf_template] submodule to create an empty netCDF file.


## Requirements
* python 3.7 or above
* modules:
  * numpy
  * pandas
  * datetime
  * netCDF4
  * csv


## Installation

Clone the git repo and submodule
```
git clone --recurse-submodules https://github.com/ncasuk/ncas-ceilometer-3-software.git
```

If the `--recurse-submodules` flag is not included, the `ncas_amof_netcdf_template` repo will not also be cloned. To fix this, use the following commands in the top level of this repo:
```
git submodule init
git submodule update
```

** TO DO **
Install required modules using `pip install -r requirements.txt` or `conda install --file requirements.txt`


## Usage

```
python process_ceilometer.py /path/to/datafile.csv -m metadata.csv
```
where `metadata.csv` includes additional metadata for the netCDF file.

Additional flags that can be given for each python script:
* `-o` or `--ncfile-location` - where to write the netCDF files to. If not given, default is `'.'`
* `-v` or `--verbose` - print additional information as the script runs

A description of all the available options can be obtained using the `-h` flag, for example
```
python process_ceilometer.py -h
```

** TO DO ** 
Bash scripts

## Further Information
* `read_ceilometer.py` contains the code that actually reads the raw data. This is called from within `process_ceilometer.py`
* No quality control is currently done on the raw data.
* See [ncas_amof_netcdf_template] for more information on how the netCDF file is created, and the additional useful functions it contains.



[ncas_amof_netcdf_template]: https://github.com/joshua-hampton/ncas_amof_netcdf_template
