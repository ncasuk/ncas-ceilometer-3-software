#!/usr/bin/env python
# vim: set fileencoding=utf-8 expandtab ts=4:
# -*- coding: utf-8 -*-
'''
Class to decode Campbell Scientific CS135 ceilometer data
'''

import csv
import struct

import numpy as np

class Ceilometer:
    '''
    Takes logged output from a ceilometer then converts it to netCDF

    '''

    def __init__(self, input_file, metadatafile = None, outfile = None):
        for infile in input_file:
            with open(infile, 'rt') as fid:
                for line in fid:
                    if chr(1) in line:
                        timestamp, ident = line.split(',')
                        line2 = fid.next()
                        status_warning, window_transmission, h1, h2, h3, h4, flags = line2.split(" ")
                        status = status_warning[0]
                        warning_alarm = status_warning[1]
                        scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum = fid.next().split(" ")
                        backscatter_profile = fid.next()
                        checksum = fid.next().strip()
                        #print(scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum, checksum)
                        backscatter = (self.backscatter_to_array(backscatter_profile.strip()))
                        print(np.where(backscatter < 0))

    def backscatter_to_array(self, backscatter_profile):
        """
        Converts a string/bytes of 2048×5 hex (20-bit) characters to a 
        numpy array of signed integers.
        (See section 2.4.1 in the CS135 manual)

        Args:
            backscatter_profile (string/bytes): String as read from ceilometer
            output.

        """
        hex_string_array = np.array([backscatter_profile[i:i+5] for i in range(0, len(backscatter_profile), 5)])
        int_array = np.apply_along_axis(lambda y: [int(i,16) for i in y],0, hex_string_array)
        #is two's complement 2-bit integer
        return(np.where(int_array > (2**19-1), int_array - 2**20, int_array))
                        


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
     Ceilometer(args.infiles, args.metadata, args.output_file)
