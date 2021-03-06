from cmath import nan
import pyspedas
from pytplot import get_data, store_data, tplot_names, tplot, options, tplot_options
from pyspedas import time_clip, time_double, time_string, tinterpol
import numpy as np
from load import mca, orb

start_year_day = '1990-06-04'
day = 30
unit_time_hour = 2

freq_channel_index = 2
channels = ["3.16 Hz", "5.62 Hz", "10 Hz", "17.6 Hz",
            "31.6 Hz", "56.2 Hz", "100 Hz", "176 Hz",
            "316 Hz", "562 Hz", "1 kHz", '1.76 kHz']

field = 'B' #Electric field, E or Magnetic field, B
spec_type = 'amp' #amplitude, amp or power, pwr


seconds_per_day = 86400
unit_time_width = 3600 * unit_time_hour
unit_per_day = seconds_per_day/(unit_time_width)
lat_array = np.arange(55, 90)

hemispheres = ['north','south']
north_matrix = []
south_matrix = []

start_time_string = start_year_day + ' 00:00:00'
start_time = time_double(start_time_string)
end_time = start_time+day*seconds_per_day

days = np.arange(start_time, end_time + seconds_per_day, seconds_per_day, float)
days_string = time_string(days, fmt= '%Y-%m-%d %H:%M:%S')

for i in range(len(days_string)-1):
    trange = [days_string[i], days_string[i+1]]
    mca(trange)
    orb(trange)
    tplot_name = ['Emax', 'Eave', 'Bmax', 'Bave']
    for k in range(4):
            tplot_variable = get_data(tplot_name[k])
            tplot_variable_float = (tplot_variable.y).astype(float)
            np.place(tplot_variable_float, tplot_variable_float == 254, np.nan)
            tplot_variable_0dB = 1e-6 #mV or pT
            bandwidth = tplot_variable.v * 0.3
            tplot_variable_amplitude = (10**(tplot_variable_float/20)) * (tplot_variable_0dB)  / np.sqrt(bandwidth)
            tplot_variable_power = (10**(tplot_variable_float/10)) * ((tplot_variable_0dB)**2)  / bandwidth
            store_data(tplot_name[k] +'_amp', data={'x': tplot_variable.times, 'y': tplot_variable_amplitude, 'v': tplot_variable.v})
            store_data(tplot_name[k] +'_pwr', data={'x': tplot_variable.times, 'y': tplot_variable_power, 'v': tplot_variable.v})
            
    tinterpol('akb_ILAT', interp_to='Emax', newname = 'ILAT', )
    tinterpol('akb_MLAT', interp_to='Emax', newname = 'MLAT')
    tinterpol('akb_MLT', interp_to='Emax', newname = 'MLT', method = 'nearest')

    start_time_hour = time_double(days_string[i])
    hours = np.arange(start_time_hour, start_time_hour + (unit_per_day + 1)*unit_time_width, unit_time_width)
    
    field_var = get_data(field+'max_'+spec_type)
    ILAT = get_data('ILAT')
    MLAT = get_data('MLAT')
    MLT = get_data('MLT')
    
    times = np.arange(start_time, end_time, unit_time_width, dtype=float)

    for hemisphere in hemispheres:
        for j in range(hours.size-1):
            pwr_list_per_hour = []        
            for lat in lat_array:            
                if hemisphere == 'north':
                    index_tuple = np.where((hours[j] <= field_var.times) & (field_var.times < hours[j+1]) 
                                        & (ILAT.y > lat) & (ILAT.y < lat+1) 
                                        & (10 <= MLT.y) & (MLT.y <= 14)
                                        & (MLAT.y>0))
                                        
                if hemisphere == 'south':
                    index_tuple = np.where((hours[j] <= field_var.times) & (field_var.times < hours[j+1]) 
                                        & (ILAT.y > lat) & (ILAT.y < lat+1) 
                                        & (10 <= MLT.y) & (MLT.y <= 14)
                                        & (MLAT.y<0))
                index = index_tuple[0] 
                if len(index) == 0:
                    pwr_list_per_hour.append(np.nan)
                else:
                    field_var_1deg = field_var.y.T[freq_channel_index][index]
                    pwr_list_per_hour.append(np.nanmax(field_var_1deg))
           
            if hemisphere == 'north':
                north_matrix.append(pwr_list_per_hour)
            if hemisphere == 'south':
                south_matrix.append(pwr_list_per_hour)


store_data(field +spec_type+'_N_monthly', data={'x':times, 'y':north_matrix, 'v':lat_array})
store_data(field +spec_type+'_S_monthly', data={'x':times, 'y':south_matrix, 'v':lat_array})

pyspedas.omni.data([start_time, end_time], datatype='1min', level='hro', no_update=True)
options([field +spec_type+'_N_monthly',field +spec_type+'_S_monthly'] , 'spec', 1)
options([field +spec_type+'_N_monthly',field +spec_type+'_S_monthly'], 'zlog', 1)
if spec_type == 'amp':
    options([field +spec_type+'_N_monthly',field +spec_type+'_S_monthly'], 'ztitle', 'SD \n [mV/m/Hz^1/2]')
if spec_type == 'pwr':
    options([field +spec_type+'_N_monthly',field +spec_type+'_S_monthly'], 'ztitle', 'PSD \n [(mV/m)^2/Hz]')
options(field +spec_type+'_N_monthly', 'ytitle', 'North Cusp \n ILAT [deg]')
options(field +spec_type+'_S_monthly', 'ytitle', 'South Cusp \n ILAT [deg]')

omni_var_name = ['BZ_GSM', 'flow_speed', 'proton_density', 'Pressure', 'SYM_H']
options(omni_var_name, 'panel_size', 0.5)

tplot_options('title','AKEBONO/MCA' + field + spec_type + '@' + channels[freq_channel_index]
              + '\n' + start_time_string)
tplot(['SYM_H', field +spec_type+'_N_monthly',field +spec_type+'_S_monthly'], save_png='mca_monthly_2h_omni_' + field + spec_type +start_year_day)
#tplot(['SYM_H', field +spec_type+'_N_monthly'], save_png='mca_monthly_2h_omni_' + field + spec_type +start_year_day)


