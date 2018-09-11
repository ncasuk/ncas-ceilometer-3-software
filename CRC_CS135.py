#!/usr/bin/python
# coding=utf8

class CRC_CS135:
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

test=CRC_CCITT()

teststr=b"Hello World"

crcval=0xFFFF

for c in teststr:
   crcval=test.update_crc(crcval, c)

print(crcval ^ 0xFFFF)
