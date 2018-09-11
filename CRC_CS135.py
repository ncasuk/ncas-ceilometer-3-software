#!/usr/bin/env python
# vim: set fileencoding=utf-8 expandtab ts=4:
# -*- coding: utf-8 -*-

class CRC_CS135:
    """
    Class implementing the CRC for the Campbell Scientific CS135 ceilometer
    """

    initval=0xFFFF
    xorval=0xFFFF

    def __init__(self):
        self.tab=256*[[]]
        for i in range(256):
            crc=0
            c = i << 8

            for j in range(8):
                if (crc ^ c) & 0x8000:
                    crc = ( crc << 1) ^ 0x1021
                else:
                        crc = crc << 1

                c = c << 1

                crc = crc & 0xffff

            self.tab[i]=crc
    
    def update_crc(self, crc, c):
        short_c=0x00ff & (c % 256)

        tmp = ((crc >> 8) ^ short_c) & 0xffff
        crc = (((crc << 8) ^ self.tab[tmp])) & 0xffff

        return crc

    def crc_message(self, message):
        """
        Takes Python3 bytes buffer and CRCs it using the algorithm
        used by the CS135 ceilometer
        """

        crcval = self.initval
        for c in message:
            crcval=self.update_crc(crcval, c)

        return crcval ^ self.xorval
