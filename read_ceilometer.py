import numpy as np
import pandas as pd


def read_file(infile):
    all_the_info = {}
    with open(infile, 'rb') as fid:
        for line in fid:
            if b'\x01' in line:
                all_the_info = read_record(line, fid, all_the_info)
            else:
                msg = "reading of text file with control characters stripped is not yet implemented, please use csv file"
                raise NotImplementedError(msg)
    all_the_info_df = pd.DataFrame(all_the_info).transpose().reset_index()
    return all_the_info_df.rename(columns={"index":"Timestamp"})


def read_record(line, fid, all_the_info):
    try:
        timestamp, ident = line.decode('ascii').split(',')
        all_the_info[timestamp] = {}
        message_number = get_message_number(ident)
        all_the_info[timestamp]['message_number'] = message_number
        if message_number not in ['001','002','003','004']:
            msg = f'Unexpected message_number - {message_number}'
            raise ValueError(msg)
        line2 = next(fid)
        status, warning_alarm, window_transmission, h1, h2, h3, h4, flags = read_line2(line2.strip())
        all_the_info[timestamp]['status'] = status
        all_the_info[timestamp]['warning_alarm'] = warning_alarm
        all_the_info[timestamp]['window_transmission'] = window_transmission
        all_the_info[timestamp]['h1'] = h1
        all_the_info[timestamp]['h2'] = h2
        all_the_info[timestamp]['h3'] = h3
        all_the_info[timestamp]['h4'] = h4
        all_the_info[timestamp]['flags'] = flags
        if message_number in ['003','004']:
            cloud_coverage_line = next(fid)
            # process cloud_coverage_line
            # add processed cloud_coverage_line to all_the_info
        if message_number in ['002','004']:
            backscatter_info_line = next(fid)
            attenuated_scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum = read_bs_info(backscatter_info_line.strip())
            ranges = int(resolution.strip('0')) * np.arange(0, int(length))
            backscatter_profile = next(fid).strip()  # removes \r\n
            backscatter_profile = decode_backscatter(backscatter_profile.strip(), attenuated_scale = int(attenuated_scale))
            all_the_info[timestamp]['attenuated_scale'] = attenuated_scale
            all_the_info[timestamp]['resolution'] = resolution
            all_the_info[timestamp]['length'] = length
            all_the_info[timestamp]['energy'] = energy
            all_the_info[timestamp]['laser_temp'] = laser_temp
            all_the_info[timestamp]['total_tilt'] = total_tilt
            all_the_info[timestamp]['bl'] = bl
            all_the_info[timestamp]['pulse'] = pulse
            all_the_info[timestamp]['sample_rate'] = sample_rate
            all_the_info[timestamp]['backscatter_sum'] = backscatter_sum
            all_the_info[timestamp]['ranges'] = ranges
            all_the_info[timestamp]['backscatter_profile'] = backscatter_profile
        checksum = next(fid)
        if len(checksum) != 6 and len(checksum) != 5:
            nextrecord = checksum[5:]
            all_the_info = read_record(nextrecord, fid, all_the_info)
        return all_the_info
    except StopIteration:
        pass


def read_line2(line2):
    status_warning, window_transmission, h1, h2, h3, h4, flags = line2.decode('ascii').split(" ")
    status = status_warning[0]
    warning_alarm = status_warning[1]
    return status, warning_alarm, window_transmission, h1, h2, h3, h4, flags


def read_bs_info(bs_info):
    attenuated_scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum = bs_info.decode('ascii').split(" ")
    return attenuated_scale, resolution, length, energy, laser_temp, total_tilt, bl, pulse, sample_rate, backscatter_sum


def decode_backscatter(backscatter_profile, attenuated_scale = 100):
    hex_string_array = np.array([backscatter_profile[i:i+5] for i in range(0, len(backscatter_profile), 5)])
    int_array = np.apply_along_axis(lambda y: [int(i,16) for i in y],0, hex_string_array)
    return((np.where(int_array > (2**19-1), int_array - 2**20, int_array)) * (attenuated_scale/100.0) * 10**-8)


def get_message_number(ident):
    return ident[7:10]


if __name__ == "__main__":
    import sys
    csvinfile = sys.argv[1]
    all_the_info_df = read_file(csvinfile)
    backscatter_array = np.stack(all_the_info_df['backscatter_profile'].to_numpy())
    print(backscatter_array)
    print(all_the_info_df)
