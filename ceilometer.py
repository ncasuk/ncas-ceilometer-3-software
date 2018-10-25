#!/usr/bin/env python
# vim: set fileencoding=utf-8 expandtab ts=4:
# -*- coding: utf-8 -*-
'''
Class to decode Campbell Scientific CS135 ceilometer data
'''

import csv
import subprocess

import numpy as np
import pandas as pd

from netCDF4 import Dataset
from datetime import datetime, timedelta

from CRC_CS135 import CRC_CS135

class Ceilometer:
    '''
    Takes logged output from a ceilometer then converts it to netCDF

    test plot:

    `cis plot attenuated_aerosol_backscatter_coefficient:test-ceil.nc:itemstyle="o",itemwidth="1",product=NetCDF_Gridded --type scatter2d --xaxis time --yaxis altitude --logv --cmap Greens --ymin 0 --ymax 4000`
    '''
    time_series = []
    backscatter_profile = []
    distance_from_instrument = []

    def __init__(self, input_file, metadatafile = None, outfile = None):
        for infile in input_file:
            with open(infile, 'rb') as fid:
                for line in fid:
                    if b'\x01' in line:
                        self.import_record(line, fid)
                    elif line.decode('ascii').split(' ')[1][0:2] == 'CS':
                        self.import_record(line, fid, text=True)

        self.df = pd.DataFrame(self.backscatter_profile, index=pd.to_datetime(self.time_series, infer_datetime_format=True), columns=self.distance_from_instrument)
        self.netcdf(outfile)

    def netcdf(self, output_file):
        '''
        Takes DataFrame with ceilometer backscatter data and outputs a well-formed NetCDF
        well-formed NetCDF
        '''

        #instantiate NetCDF output
        dataset = Dataset(output_file, "w", format="NETCDF4_CLASSIC")

        # Create the time dimension - with unlimited length
        time_dim = dataset.createDimension("time", None)

        # Create the time variable
        base_time = np.datetime64('1970-01-01T00:00:00')
        self.timeoffsets = (self.df.index - base_time).total_seconds().get_values()

        time_units = "seconds since " + base_time.astype(datetime).strftime('%Y-%m-%d %H:%M:%S')
        time_var = dataset.createVariable("time", np.float64, ("time",))
        time_var.units = time_units
        time_var.fill_value = np.nan
        time_var.standard_name = "time"
        time_var.calendar = "standard"
        time_var[:] = self.timeoffsets[:]
        

        #Create the altitude dimension
        altitude_dim = dataset.createDimension("altitude", len(self.df.columns))

        altitude_var = dataset.createVariable("altitude", np.float32, ("altitude",))
        altitude_var.units = 'm'
        altitude_var.standard_name = 'altitude'
        altitude_var.long_name = 'Geometric height above geoid (WGS84)'
        altitude_var.axis = 'Z'
        altitude_var[:] = self.df.columns.get_values().astype(float)

        dataset.processing_software_url = subprocess.check_output(["git", "remote", "-v"]).split()[1] # get the git repository URL
        dataset.processing_software_version = subprocess.check_output(['git','rev-parse', '--short', 'HEAD']).strip() #record the Git revision
        dataset.time_coverage_start = self.df.index[0].strftime('%Y-%m-%dT%H:%M:%S')
        dataset.time_coverage_end = self.df.index[-1].strftime('%Y-%m-%dT%H:%M:%S')

        backscatter = dataset.createVariable('attenuated_aerosol_backscatter_coefficient', 'float32', ('time','altitude'))
        backscatter.units = 'm-1 sr-1'
        backscatter.standard_name = 'attenuated_aerosol_backscatter_coefficient'
        backscatter.long_name = 'Attenuated Aerosol Backscatter Coefficient'
        backscatter.fill_value = -1.00e20
        backscatter[:] = self.df

        dataset.setncattr('Conventions',"CF-1.6, NCAS-AMF-1.0")

        dataset.close()

    def plot(self):
        import matplotlib.pyplot as plt
        import matplotlib.dates as md
        import seaborn as sns

        '''Does a quick-and-dirty plot for testing purposes'''
        plt.xticks(rotation=45)
        ax = sns.heatmap(np.log10(self.df.loc[:,0:4000].T), cmap='Greens', vmin=-6.5, vmax=-3)

        ax.invert_yaxis()

        plt.autoscale()
        plt.show()


    def import_record(self, line, fid, text=False):
        '''
        Processes a single record from the ceilometer. if two records are merged
        together (i.e. checksum of one runs straight into the timestamp for the
        next, demerge them and recurse
        '''
        try: #need to manually check for StopIteration in case 
             #of truncated records
            if(text):
                #".txt" file, control characters stripped
                timestamp, ident = line.decode('ascii').split(' ')
                line2 = next(fid)[27:] #strip timestamp
                line3 = next(fid)[27:]
                backscatter_profile = next(fid)[27:]
                checksum = next(fid)[27:]
            else:
                #".csv" file, with control characters
                timestamp, ident = line.decode('ascii').split(',')
                line2 = next(fid)
                line3 = next(fid)
                backscatter_profile = next(fid)
                checksum = next(fid)
            status_warning, window_transmission, h1, h2, h3, h4, flags = line2.decode('ascii').split(" ")
            status = status_warning[0]
            warning_alarm = status_warning[1]
            attenuated_scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum = line3.decode('ascii').split(" ")
            #ident include SOH character which is not included in
            #CS135's CRC
            ident = ident.lstrip('\x01')
            nextrecord = None
            if len(checksum) != 6 and len(checksum) != 5: #6 includes TX and LF
                #probably merged with next record, e.g. ^C86de2018-09-10T11:40:58.503741.....
                nextrecord = checksum[5:]
                checksum = checksum[0:5]
    
            #strip TX and LF
            checksum = checksum.decode('ascii').lstrip('\x03').rstrip('\n')
        
            #strips and replaces control chrs, as they are missing in
            # .txt format input files
            if self.checkmessage(bytes(ident,'ascii').strip(b'\x02\r\n')+b'\x02\r\n'+line2.strip()+b'\r\n'+line3.strip()+b'\r\n'+backscatter_profile.strip()+b'\r\n'+b'\x03', int(checksum,16)):
    
                #print(scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum, checksum)
                backscatter = self.backscatter_to_array(backscatter_profile.strip(), int(attenuated_scale))
                ranges = int(resolution.strip('0')) * np.arange(0, int(length))
                self.backscatter_profile.append(backscatter)
                self.time_series.append(timestamp)
                self.distance_from_instrument = ranges
            if(nextrecord):
                #if the checksum was demerged from a merged record
                self.import_record(nextrecord, fid, text=text)
                print('corrected merged records')
        except StopIteration:
            #chuck away partial records
            pass;

    def checkmessage(self, message, checksum=None):
        """
        computes a checksum for the data, and optionally checks it against 
        the supplied value.

        Args:
            message (string): Complete string including terminal ETX
            checksum (hex string or int): checksum as supplied by instrument
        """
        crc = CRC_CS135()
        crcval = crc.crc_message(message)
        if checksum:
            if isinstance(checksum, int):
                pass
            else:
                #assume hex string, eg "ea4d"
                checksum = int(checksum,16)

            if crcval == checksum:
                return True
            else:
                print("failed checksum")
                return False
        else:
            #no checksum supplied, return calculated value
            return crcval


    def backscatter_to_array(self, backscatter_profile, attenuated_scale=100):
        """
        Converts a string/bytes of 2048×5 hex (20-bit) characters to a 
        numpy array of signed integers.
        (See section 2.4.1 in the CS135 manual)

        Args:
            backscatter_profile (string/bytes): String as read from ceilometer
            output.

        Returns:
            numpy array of backscatter values in sr¯¹m¯¹, scaled by 
            attenuated_SCALE value
        """
        hex_string_array = np.array([backscatter_profile[i:i+5] for i in range(0, len(backscatter_profile), 5)])
        int_array = np.apply_along_axis(lambda y: [int(i,16) for i in y],0, hex_string_array)
        #is two's complement 2-bit integer
        return((np.where(int_array > (2**19-1), int_array - 2**20, int_array)) * (attenuated_scale/100.0) * 10**-8)
                        


def arguments():
     """
     Processes command-line arguments, returns parser.
     """
     from argparse import ArgumentParser
     parser=ArgumentParser()
     parser.add_argument('--outfile', dest="output_file", help="NetCDF output filename", default=None)
     parser.add_argument('--metadata', dest="metadata", help="Metadata filename", default='meta-data.csv')
     parser.add_argument('infiles',nargs='+', help="Ceilometer data file")

     return parser

if __name__ == '__main__':
     args = arguments().parse_args()
     c = Ceilometer(args.infiles, args.metadata, args.output_file)
     #c.plot()
