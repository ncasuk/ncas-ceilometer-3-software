#!/usr/bin/env python
# vim: set fileencoding=utf-8 expandtab ts=4:
# -*- coding: utf-8 -*-
'''
Class to decode Campbell Scientific CS135 ceilometer data
'''

import csv
import os
import subprocess

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from amfutils.instrument import AMFInstrument
from netCDF4 import Dataset

from CRC_CS135 import CRC_CS135

class Ceilometer (AMFInstrument):
    '''
    Takes logged output from a ceilometer then converts it to netCDF

    test plot:

    `cis plot attenuated_aerosol_backscatter_coefficient:test-ceil.nc:itemstyle="o",itemwidth="1",product=NetCDF_Gridded --type scatter2d --xaxis time --yaxis altitude --logv --cmap Greens --ymin 0 --ymax 4000`
    '''

    progname = __file__
    product = 'aerosol-backscatter'

    time_series = []
    backscatter_profile = []
    distance_from_instrument = []

    def get_data(self, input_files, outdir):

        self.outdir = outdir

        for infile in input_files:
            with open(infile, 'rb') as fid:
                for line in fid:
                    if b'\x01' in line:
                        self.import_record(line, fid)
                    elif line.decode('ascii').split(' ')[1][0:2] == 'CS':
                        self.import_record(line, fid, text=True)

        self.rawdata = pd.DataFrame(self.backscatter_profile, index=pd.to_datetime(self.time_series, infer_datetime_format=True), columns=self.distance_from_instrument)
        #set start and end times
        self.time_coverage_start = self.rawdata.index[0].strftime(self.timeformat)
        self.time_coverage_end = self.rawdata.index[-1].strftime(self.timeformat)
        self.netcdf(self.outdir)

    def netcdf(self, output_dir):
        '''
        Takes DataFrame with ceilometer backscatter data and outputs a 
        well-formed NetCDF file. 

        :param output_dir: string containing path to output directory
        '''

        #instantiate NetCDF output
        self.setup_dataset(self.product, 1)

        #can drop timeoffsets from rawdata
        self.rawdata.drop(columns='timeoffsets', inplace=True)

        #Create the altitude dimension
        altitude_dim = self.dataset.createDimension("altitude", len(self.rawdata.columns))

        altitude_var = self.dataset.createVariable("altitude", np.float32, ("altitude",))
        altitude_var.units = 'm'
        altitude_var.standard_name = 'altitude'
        altitude_var.long_name = 'Geometric height above geoid (WGS84)'
        altitude_var.axis = 'Z'
        altitude_var[:] = self.rawdata.columns.array.astype(float)

        backscatter = self.dataset.createVariable('attenuated_aerosol_backscatter_coefficient', 'float32', ('time','altitude'))
        backscatter.units = 'm-1 sr-1'
        backscatter.standard_name = 'attenuated_aerosol_backscatter_coefficient'
        backscatter.long_name = 'Attenuated Aerosol Backscatter Coefficient'
        backscatter.fill_value = -1.00e20
        backscatter[:] = self.rawdata

        self.dataset.setncattr('Conventions',"CF-1.6, NCAS-AMF-1.0")

        self.dataset.close()

    def plot(self):
        '''Does a quick-and-dirty plot for testing purposes'''

        import matplotlib.pyplot as plt
        import matplotlib.dates as md
        import seaborn as sns

        plt.xticks(rotation=45)
        ax = sns.heatmap(np.log10(self.rawdata.T), cmap='Greens', vmin=-6.5, vmax=-3)

        ax.invert_yaxis()

        plt.autoscale()
        plt.show()


    def import_record(self, line, fid, text=False):
        '''
        Processes a single record from the ceilometer. if two records are merged
        together (i.e. checksum of one runs straight into the timestamp for the
        next, demerge them and recurse.

        :param: line: Bytes object. A line from a raw datafile.
        :param: fid: File(-like) object such as returned by open()
        :param: text: Boolean. Set to true if the raw file has had control characters stripped.
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
                        


if __name__ == '__main__':
    args = Ceilometer.arguments().parse_args()
    c = Ceilometer(args.metadata)
    try:
        os.makedirs(args.outdir,mode=0o755)
    except OSError:
         #Dir already exists, probably
         pass
    else:
        print ("Successfully create directory %s" % args.outdir)

    c.get_data(args.infiles, args.outdir)
