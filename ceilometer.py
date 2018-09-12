#!/usr/bin/env python
# vim: set fileencoding=utf-8 expandtab ts=4:
# -*- coding: utf-8 -*-
'''
Class to decode Campbell Scientific CS135 ceilometer data
'''

import csv
import struct

import numpy as np

from CRC_CS135 import CRC_CS135

class Ceilometer:
    '''
    Takes logged output from a ceilometer then converts it to netCDF

    '''

    def __init__(self, input_file, metadatafile = None, outfile = None):
        for infile in input_file:
            with open(infile, 'rb') as fid:
                for line in fid:
                    if b'\x01' in line:
                        self.import_record(line, fid)

    def import_record(self, line, fid):
        timestamp, ident = line.decode('ascii').split(',')
        line2 = next(fid)
        status_warning, window_transmission, h1, h2, h3, h4, flags = line2.decode('ascii').split(" ")
        status = status_warning[0]
        warning_alarm = status_warning[1]
        line3 = next(fid)
        scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum = line3.decode('ascii').split(" ")
        backscatter_profile = next(fid)
        checksum = next(fid)
        #ident include SOH character which is not included in
        #CS135's CRC
        nextrecord = None
        if len(checksum) != 6: #6 includes TX and LF
            #probably merged with next record, e.g. ^C86de2018-09-10T11:40:58.503741.....
            nextrecord = checksum[5:]
            checksum = checksum[0:5]

                        
        if self.checkmessage(bytes(ident[1:],'ascii')+line2+line3+backscatter_profile+b'\x03', int(checksum[1:],16)):
            print(timestamp, 'Passed checksum')

            #print(scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum, checksum)
            backscatter = (self.backscatter_to_array(backscatter_profile.strip()))
        if(nextrecord):
            #if the checksum was demerged from a merged record
            self.import_record(nextrecord, fid)
            print('corrected merged records')

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
                return False
        else:
            #no checksum supplied, return calculated value
            return crcval


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
