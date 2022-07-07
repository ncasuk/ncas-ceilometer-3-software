import datetime as dt
import numpy as np
from netCDF4 import Dataset
import csv

import read_ceilometer
from ncas_amof_netcdf_template import create_netcdf, util, remove_empty_variables



def get_data(csv_file):
    all_the_info_df = read_ceilometer.read_file(csv_file).replace('/////',np.NaN)
    time_len = len(all_the_info_df['Timestamp'])
    alt_len = len(all_the_info_df['ranges'][0])
    
    dt_times = [dt.datetime.strptime(i, "%Y-%m-%dT%H:%M:%S.%f") for i in all_the_info_df['Timestamp']]
    
    backscatter_array = np.stack(all_the_info_df['backscatter_profile'].to_numpy())
    laser_temp = np.stack(all_the_info_df['laser_temp'].to_numpy())
    laser_temp = np.array([float(i) for i in laser_temp])
    laser_energy = np.stack(all_the_info_df['energy'].to_numpy())
    laser_energy = np.array([float(i) for i in laser_energy])
    window_transmittance = np.stack(all_the_info_df['window_transmission'].to_numpy())
    window_transmittance = np.array([float(i) for i in window_transmittance])
    backscatter_sum = np.stack(all_the_info_df['backscatter_sum'].to_numpy())
    backscatter_sum = np.array([float(i) for i in backscatter_sum])
    background_light = np.stack(all_the_info_df['bl'].to_numpy())
    background_light = np.array([float(i) for i in background_light])
    resolution = np.stack(all_the_info_df['resolution'].to_numpy())
    resolution = np.array([float(i) for i in resolution])
    ranges = np.stack(all_the_info_df['ranges'].to_numpy())
    pulses = np.stack(all_the_info_df['pulse'].to_numpy())
    pulses = np.array([int(i)*1000 for i in pulses])
    scale = np.stack(all_the_info_df['attenuated_scale'].to_numpy())
    scale = np.array([int(i) for i in scale])
    #ranges = np.array([float(i) for i in ranges])
    total_tilt = np.stack(all_the_info_df['total_tilt'].to_numpy())
    total_tilt = np.array([float(i) for i in total_tilt])
    altitude = ranges[0,:] * np.sin(np.deg2rad(90-total_tilt[0]))  # tilt angle corrected altitude
    
    cba = np.empty((len(dt_times),4))
    for i in range(len(dt_times)):
        cba[i,0] = all_the_info_df['h1'][i]
        cba[i,1] = all_the_info_df['h2'][i]
        cba[i,2] = all_the_info_df['h3'][i]
        cba[i,3] = all_the_info_df['h4'][i]
        
    return time_len, alt_len, dt_times, backscatter_array, laser_temp, laser_energy, window_transmittance, backscatter_sum, background_light, resolution, ranges, pulses, scale, total_tilt, altitude, cba
    
    
    
def make_netcdf_aerosol_backscatter(csv_file, metadata_file = None, ncfile_location = '.', verbose = False):
    time_len, alt_len, dt_times, backscatter_array, laser_temp, laser_energy, window_transmittance, backscatter_sum, background_light, resolution, ranges, pulses, scale, total_tilt, altitude, cba = get_data(csv_file)
    unix_times, doy, years, months, days, hours, minutes, seconds, time_coverage_start_dt, time_coverage_end_dt, file_date = util.get_times(dt_times)
    
    create_netcdf.main('ncas-ceilometer-3', date = file_date, dimension_lengths = {'time':time_len, 'altitude':alt_len}, loc = 'land', products = ['aerosol-backscatter'], file_location=ncfile_location)
    ncfile = Dataset(f'{ncfile_location}/ncas-ceilometer-3_iao_{file_date}_aerosol-backscatter_v1.0.nc', 'a')
    
    util.update_variable(ncfile, 'altitude', altitude)
    util.update_variable(ncfile, 'attenuated_aerosol_backscatter_coefficient', backscatter_array)
    util.update_variable(ncfile, 'laser_temperature', laser_temp)
    util.update_variable(ncfile, 'laser_pulse_energy', laser_energy)
    util.update_variable(ncfile, 'window_transmittance', window_transmittance)
    util.update_variable(ncfile, 'backscatter_sum', backscatter_sum)
    util.update_variable(ncfile, 'background_light', background_light)
    util.update_variable(ncfile, 'profile_pulses', pulses)
    util.update_variable(ncfile, 'profile_scaling', scale)
    
    util.update_variable(ncfile, 'time', unix_times)
    util.update_variable(ncfile, 'year', years)
    util.update_variable(ncfile, 'month', months)
    util.update_variable(ncfile, 'day', days)
    util.update_variable(ncfile, 'hour', hours)
    util.update_variable(ncfile, 'minute', minutes)
    util.update_variable(ncfile, 'second', seconds)
    util.update_variable(ncfile, 'day_of_year', doy)
    util.update_variable(ncfile, 'sensor_zenith_angle', total_tilt)
    
    ncfile.setncattr('time_coverage_start', dt.datetime.fromtimestamp(time_coverage_start_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('time_coverage_end', dt.datetime.fromtimestamp(time_coverage_end_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
                
    # if lat and lon given, no need to also give geospatial_bounds
    # this works great for point deployment (e.g. ceilometer)
    lat_masked = ncfile.variables['latitude'][0].mask
    lon_masked = ncfile.variables['longitude'][0].mask
    geospatial_attr_changed = "CHANGE" in ncfile.getncattr('geospatial_bounds')
    if geospatial_attr_changed and not lat_masked and not lon_masked:
        geobounds = f"{ncfile.variables['latitude'][0]}N, {ncfile.variables['longitude'][0]}E"
        ncfile.setncattr('geospatial_bounds', geobounds)
    
    ncfile.close()
    
    remove_empty_variables.main(f'{ncfile_location}/ncas-ceilometer-3_iao_{file_date}_aerosol-backscatter_v1.0.nc', verbose = verbose)







#def make_netcdf_cloud_coverage






def make_netcdf_cloud_base(csv_file, metadata_file = None, ncfile_location = '.', verbose = False):
    time_len, alt_len, dt_times, backscatter_array, laser_temp, laser_energy, window_transmittance, backscatter_sum, background_light, resolution, ranges, pulses, scale, total_tilt, altitude, cba = get_data(csv_file)
    unix_times, doy, years, months, days, hours, minutes, seconds, time_coverage_start_dt, time_coverage_end_dt, file_date = util.get_times(dt_times)
    
    create_netcdf.main('ncas-ceilometer-3', date = file_date, dimension_lengths = {'time':time_len, 'layer_index': 4}, loc = 'land', products = ['cloud-base'], file_location=ncfile_location)
    ncfile = Dataset(f'{ncfile_location}/ncas-ceilometer-3_iao_{file_date}_cloud-base_v1.0.nc', 'a')
    
    util.update_variable(ncfile, 'cloud_base_altitude', cba)
    util.update_variable(ncfile, 'laser_temperature', laser_temp)
    util.update_variable(ncfile, 'laser_pulse_energy', laser_energy)
    # yes, there is a spelling mistake in the netCDF file
    util.update_variable(ncfile, 'window_transmttance', window_transmittance)  
    util.update_variable(ncfile, 'backscatter_sum', backscatter_sum)
    util.update_variable(ncfile, 'background_light', background_light)
    util.update_variable(ncfile, 'profile_pulses', pulses)
    util.update_variable(ncfile, 'profile_scaling', scale)
    
    util.update_variable(ncfile, 'time', unix_times)
    util.update_variable(ncfile, 'year', years)
    util.update_variable(ncfile, 'month', months)
    util.update_variable(ncfile, 'day', days)
    util.update_variable(ncfile, 'hour', hours)
    util.update_variable(ncfile, 'minute', minutes)
    util.update_variable(ncfile, 'second', seconds)
    util.update_variable(ncfile, 'day_of_year', doy)
    util.update_variable(ncfile, 'sensor_zenith_angle', total_tilt)
    
    ncfile.setncattr('time_coverage_start', dt.datetime.fromtimestamp(time_coverage_start_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    ncfile.setncattr('time_coverage_end', dt.datetime.fromtimestamp(time_coverage_end_dt, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S %Z"))
    
    util.add_metadata_to_netcdf(ncfile, metadata_file)
                
    # if lat and lon given, no need to also give geospatial_bounds
    # this works great for point deployment (e.g. ceilometer)
    lat_masked = ncfile.variables['latitude'][0].mask
    lon_masked = ncfile.variables['longitude'][0].mask
    geospatial_attr_changed = "CHANGE" in ncfile.getncattr('geospatial_bounds')
    if geospatial_attr_changed and not lat_masked and not lon_masked:
        geobounds = f"{ncfile.variables['latitude'][0]}N, {ncfile.variables['longitude'][0]}E"
        ncfile.setncattr('geospatial_bounds', geobounds)
        
    ncfile.close()
    
    remove_empty_variables.main(f'{ncfile_location}/ncas-ceilometer-3_iao_{file_date}_cloud-base_v1.0.nc', verbose = verbose)
 
    
    
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description = 'Create AMOF-compliant netCDF file for ncas-ceilometer-3 instrument.')
    parser.add_argument('input_csv', type=str, help = 'Raw csv data from instrument.')
    parser.add_argument('-v','--verbose', action='store_true', help = 'Print out additional information.', dest = 'verbose')
    parser.add_argument('-m','--metadata', type = str, help = 'csv file with global attributes and additional metadata. Default is None', dest='metadata')
    parser.add_argument('-o','--ncfile-location', type=str, help = 'Path for where to save netCDF file. Default is .', default = '.', dest="ncfile_location")
    parser.add_argument('-p','--products', nargs = '*', help = 'Products of ncas-ceilometer-3 to make netCDF files for. Options are aerosol_backscatter, cloud_base, cloud_coverage (not yet implemented). One or many can be given (space separated), default is "aerosol_backscatter cloud_base".', default = ['aerosol_backscatter', 'cloud_base'])
    args = parser.parse_args()
    
    for prod in args.products:
        if prod == 'aerosol_backscatter':
            make_netcdf_aerosol_backscatter(args.input_csv, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        elif prod == 'cloud_base':
            make_netcdf_cloud_base(args.input_csv, metadata_file = args.metadata, ncfile_location = args.ncfile_location, verbose = args.verbose)
        elif prod == 'cloud_coverage':
            #make_netcdf_cloud_coverage(args.input_csv, metadata_file = args.metadata, ncfile_location = args.ncfile_location)
            print('WARNING: cloud_coverage is not yet implemented, continuing with other prodcuts...')
        else:
            print(f'WARNING: {prod} is not recognised for this instrument, continuing with other prodcuts...')
    
                        
