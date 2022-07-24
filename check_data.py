# osandvold
# 5 Jul 2022
# Adapted script from checkData_UPENN.m script from Heiner (Philips)
# for validating and reading log data from DMS of CT Benchtop

import numpy as np
import pandas as pd
import glob
import os.path
import matplotlib.pyplot as plt

# Script adapted from Heiner to read DMS data (.dat) which is a binary file
# Each projection contains a header 64 entries (unit16) and detector data
# of size (nrows * (ncols+8)) = 16 * (672+8)
# Example: acquiring 4000 views will mean you have 4000 headers and
# 4000x the detector data

# Function to read .dat file and return dcm (dms data)
def read_dms_dat_nrows(dat_fname):
  dcm = {}

  nCols = 672
  tailer = 8 # the tailer has 8 bytes
  header = 64
  # read and open binary .dat file
  file_id = open(dat_fname, 'rb')

  nRows = list(file_id.read(1))[0]
  print(f'Number of detected rows: {nRows}')

  # read binary file
  cirs_data = np.fromfile(dat_fname, dtype='uint16')

  bytes_per_view = ((nCols + tailer) * nRows + header)
  nViews = int(np.floor(len(cirs_data) / bytes_per_view))
  print(f'Number of detected views: {nViews}')

  headers = np.zeros((nViews, 64), dtype=float)

  # loop to collect the header information
  for counter in range(nViews):
    headers[counter, :] = cirs_data[counter*bytes_per_view + np.arange(64)]

  # TODO: use projData mainly
  projData = np.zeros((nCols, nRows, nViews))
  projDataHz = np.zeros((nCols, nRows, nViews))
  projDataRaw = np.zeros((nCols, nRows, nViews))

  # loop to collect the projection data
  for v in range(nViews):
    for c in range(nRows):
      projData_ind = header + v*bytes_per_view + (nCols+tailer)*c + np.arange(nCols)
      projData[:,c,v] = np.exp(-1 * cirs_data[projData_ind]
                                / 2048 * np.log(2))
      projDataHz_ind = header + v*bytes_per_view + (nCols+tailer)*c + np.arange(nCols)
      projDataHz[:,c,v] = 8e6 * (2 ** (-cirs_data[projDataHz_ind] / 2048))
      # projDataRaw_ind = header + v*bytes_per_view + (nCols+tailer)*c + np.arange(nCols)
      # projDataRaw[:,c,v] = cirs_data[projDataRaw_ind]

  # create output structure/dictionary
  dcm['FloatProjectionData'] = projData
  dcm['FloatProjectionDataHz'] = projDataHz
  # dcm['FloatProjectionDataRaw'] = projDataRaw

  dcm['IntegrationPeriod'] = headers[:,3]*0.125
  dcm['kV'] = headers[:, 50]
  dcm['mA'] = headers[:, 49]
  dcm['gridV1'] = headers[:, 42]
  dcm['gridV2'] = headers[:, 43]
  dcm['LeftDMSTemperature'] = headers[:,5] * 1/16
  dcm['RightDMSTemperature'] = headers[:,6] * 1/16
  dcm['RotationAngle'] = headers[:, 18] * 360/13920
  dcm['IPcounter'] = headers[:,17]

  return dcm

# Read the ; delimited csv log file and save as a table
# Header:
#     Timestamp[us]; Grid_1[V]; Grid_2[V]; Anode_Voltage[V]; Cathode_Voltage[V];
#     High_Voltage[V]; Analog_In_2[mV]; Analog_In_3[mV]; HighVoltage[0,1];
#     HighGrid[0,1]; Resend[0,1]; X_Act_S[0,1]; TH_Rising[0,1]; TH_Falling[0,1];
#     Phase[3Bit]; IP_Counter[16Bit]; Phantom_Index[0,1]; Phantom_AP0[0,1];
#     Phantom_AP90[0,1]; DMS_AP0[0,1]; DMS_AP90[0,1]; DMS_Even_Rea[0,1]
def read_log(log_fname):
  log_data = pd.read_csv(log_fname, sep=';')
  return log_data

# Send in a directory path with the .dat and .csv file
# Output:
#     - Will display the DMS data
#     - Will display the wave form of the data
#     - Will print a PNG to the same data directory
def check_data(data_path):
  paths = check_contents(data_path)
  # Exit if the csv and dat file are not in the same directory
  if len(paths) == 0:
    print('Must have only one dat and one log file in the same directory')
    return 0

  logdata = read_log(paths[0])
  dcm = read_dms_dat_nrows(paths[1])
  row = 40 # set in the original script

  # where to grab data
  indStart = round(0.4/(1e-6)) # 400000
  indEnd = len(logdata.loc[:,'Timestamp[us]'])-100

  # compute correct time axis
  timeLog  = np.arange(1, len(logdata.loc[:,'Timestamp[us]'])) * 1.0e-6
  dd       = np.mean(np.mean(np.mean(dcm['FloatProjectionData'][300:400,:,:])))
  KV       = np.transpose(round(logdata.loc[:,'High_Voltage[V]'][indStart:indEnd]/1000))
  PD       = np.transpose(-logdata.loc[:,'Analog_In_2[mV]'][indStart:indEnd])
  time     = timeLog[indStart:indEnd] - timeLog[indStart]
  IPsignal = logdata.loc[:,'DMS_Even_Rea[0,1]'][indStart:indEnd]
  nx, ny, nz = dcm['FloatProjectionData'].shape

  print(f'Shape of projection data: ({nx}, {ny}, {nz})')

  # plot the data from the dms
  plt.figure()
  plt.imshow(np.transpose(np.mean(dcm['FloatProjectionData'], 2)), vmax=0.05)

  # plot the signals
  plt.figure(figsize=(11.5, 6))
  plt.subplot2grid((2, 4), (0, 0))
  # plt.hist(dcm['IntegrationPeriod'], 100) # bins=100
  low_ip = dcm['IntegrationPeriod'][1:-1:2]
  high_ip = dcm['IntegrationPeriod'][2:-1:2]
  bins = np.linspace(200,600,100)
  plt.hist(low_ip, bins, alpha=0.5, label='low')
  plt.hist(high_ip, bins, alpha=0.5, label='high')
  plt.xlabel('IP [us]')
  plt.ylabel('frequency')
  plt.legend()
  plt.title('IP')
  # TODO: print the mode (IP) of each peak on the graph

  # plot the projection for a single detector at row 40, col 341
  plt.subplot2grid((2, 4), (0, 1))
  ys = dcm['FloatProjectionData'][341, row, :].squeeze()
  plt.plot(ys)
  plt.xlim([150, 200]) # views ranges from 1-nViews
  plt.title('Profile of projection at (40,341)')
  plt.xlabel('view')
  plt.ylabel('DMS signal for single pixel')
  plt.ylim([np.mean(ys)-3*np.std(ys), np.mean(ys)+3*np.std(ys)])

  plt.subplot2grid((2, 4), (0, 2), colspan=2)
  plt.imshow(np.transpose(dcm['FloatProjectionData'][:, row, 1:-1:2].squeeze()),
              vmin=0, vmax= 0.5, aspect='auto', cmap='gray')
  plt.title('dms low')
  plt.xlabel('columns')
  plt.ylabel('views')
  plt.xlim([1, 672])
  plt.ylim([nz/2-99, nz/2])

  # Will see either switching or no switching
  plt.subplot2grid((2, 4), (1, 0))
  plt.plot(time, KV)
  plt.plot(time, np.transpose(IPsignal*max(KV)))
  plt.title('Genrator kVp')
  plt.xlabel('time')
  plt.ylabel('voltage [kVp]')
  plt.xlim([0.1, 0.102]) # time ranges from time[0] to time[-1]
  plt.ylim([60, 150])
  plt.grid()

  # refrence diode detector
  plt.subplot2grid((2, 4), (1, 1))
  plt.plot(time, PD)
  plt.title('photodiode signal')
  plt.xlabel('time')
  plt.ylabel('voltage [mV]')
  plt.xlim([0.1, 0.102]) # time ranges from time[0] to time[-1]
  plt.grid()

  plt.subplot2grid((2, 4), (1, 2), colspan=2)
  plt.imshow(np.transpose(dcm['FloatProjectionData'][:,row, 2:-1:2].squeeze()),
              vmin=0, vmax= 0.5, aspect='auto', cmap='gray')
  plt.title('dms high')
  plt.xlabel('columns')
  plt.ylabel('views')
  plt.xlim([1, 672])
  plt.ylim([nz/2-99, nz/2])

  plt.tight_layout()

  # Save the png figure to the same data_path
  # plt.savefig()

  # display profiles
  plt.figure(figsize=(11.5, 6))
  plt.subplot(2,2,1)
  plt.plot(dcm['FloatProjectionDataHz'][342,row,1:-1:2].squeeze())
  plt.xlim([90, 672])
  plt.title('profiles low (40, 342)')
  plt.subplot(2,2,2)
  plt.plot(dcm['FloatProjectionDataHz'][342,row,2:-1:2].squeeze())
  plt.xlim([90, 672])
  plt.title('profiles high (40, 342)')
  plt.subplot(2,2,3)
  plt.plot(dcm['FloatProjectionDataHz'][600,row,1:-1:2].squeeze())
  plt.xlim([90, 672])
  plt.title('profiles low (40,600)')
  plt.subplot(2,2,4)
  plt.plot(dcm['FloatProjectionDataHz'][600,row,2:-1:2].squeeze())
  plt.xlim([90, 672])
  plt.title('profiles high (40,600)')
  # plt.savefig()

  # show the histograms
  plt.figure()
  plt.subplot(1,2,1)
  data = dcm['FloatProjectionData'][342,row,101:-1:2]
  plt.hist(data[:],1000)
  plt.title('histogram low data')
  
  plt.subplot(1,2,2)
  data = dcm['FloatProjectionData'][342,row,102:-1:2]
  plt.hist(data[:],1000)
  plt.title('histogram high data')

  return 0

# TODO: add foldername as an input path, or use a defult ./results path
def display_main_figure(paths):
  # read the data
  logdata = read_log(paths[0])
  dcm = read_dms_dat_nrows(paths[1])
  row = 40 # set in the original script

  # where to grab data
  indStart = round(0.4/(1e-6)) # 400000
  indEnd = len(logdata.loc[:,'Timestamp[us]'])-100

  # compute correct time axis
  timeLog  = np.arange(1, len(logdata.loc[:,'Timestamp[us]'])) * 1.0e-6
  dd       = np.mean(np.mean(np.mean(dcm['FloatProjectionData'][300:400,:,:])))
  KV       = np.transpose(round(logdata.loc[:,'High_Voltage[V]'][indStart:indEnd]/1000))
  PD       = np.transpose(-logdata.loc[:,'Analog_In_2[mV]'][indStart:indEnd])
  time     = timeLog[indStart:indEnd] - timeLog[indStart]
  IPsignal = logdata.loc[:,'DMS_Even_Rea[0,1]'][indStart:indEnd]
  nx, ny, nz = dcm['FloatProjectionData'].shape

  # plot the signals
  plt.figure(figsize=(11.5, 6))
  plt.subplot2grid((2, 4), (0, 0))
  # plt.hist(dcm['IntegrationPeriod'], 100) # bins=100
  low_ip = dcm['IntegrationPeriod'][1:-1:2]
  high_ip = dcm['IntegrationPeriod'][2:-1:2]
  bins = np.linspace(200,600,100)
  plt.hist(low_ip, bins, alpha=0.5, label='low')
  plt.hist(high_ip, bins, alpha=0.5, label='high')
  plt.xlabel('IP [us]')
  plt.ylabel('frequency')
  plt.legend()
  plt.title('IP')

  # plot the projection for a single detector at row 40, col 341
  plt.subplot2grid((2, 4), (0, 1))
  ys = dcm['FloatProjectionData'][341, row, :].squeeze()
  plt.plot(ys)
  plt.xlim([150, 200]) # views ranges from 1-nViews
  plt.title('Profile of projection at (40,341)')
  plt.xlabel('view')
  plt.ylabel('DMS signal for single pixel')
  plt.ylim([np.mean(ys)-3*np.std(ys), np.mean(ys)+3*np.std(ys)])

  plt.subplot2grid((2, 4), (0, 2), colspan=2)
  plt.imshow(np.transpose(dcm['FloatProjectionData'][:, row, 1:-1:2].squeeze()),
              vmin=0, vmax= 0.5, aspect='auto', cmap='gray')
  plt.title('dms low')
  plt.xlabel('columns')
  plt.ylabel('views')
  plt.xlim([1, 672])
  plt.ylim([nz/2-99, nz/2])

  # Will see either switching or no switching
  plt.subplot2grid((2, 4), (1, 0))
  plt.plot(time, KV)
  plt.plot(time, np.transpose(IPsignal*max(KV)))
  plt.title('Genrator kVp')
  plt.xlabel('time')
  plt.ylabel('voltage [kVp]')
  plt.xlim([0.1, 0.102]) # time ranges from time[0] to time[-1]
  plt.ylim([60, 150])
  plt.grid()

  # refrence diode detector
  plt.subplot2grid((2, 4), (1, 1))
  plt.plot(time, PD)
  plt.title('photodiode signal')
  plt.xlabel('time')
  plt.ylabel('voltage [mV]')
  plt.xlim([0.1, 0.102]) # time ranges from time[0] to time[-1]
  plt.grid()

  plt.subplot2grid((2, 4), (1, 2), colspan=2)
  plt.imshow(np.transpose(dcm['FloatProjectionData'][:,row, 2:-1:2].squeeze()),
              vmin=0, vmax= 0.5, aspect='auto', cmap='gray')
  plt.title('dms high')
  plt.xlabel('columns')
  plt.ylabel('views')
  plt.xlim([1, 672])
  plt.ylim([nz/2-99, nz/2])

  plt.tight_layout()
  # TODO: 
  # plt.savefig(foldername)
  plt.show()


# Checks the directory path has one .dat and one .csv file
# Returns the path to those files in an array if true
# or an empty array if false
def check_contents(data_path):
  log_files = glob.glob(os.path.join(data_path, '*.csv'))
  dat_files = glob.glob(os.path.join(data_path, '*.dat'))

  if len(log_files) == 1 and len(dat_files) == 1:
    return log_files + dat_files
  else:
    print(f'Directory {data_path} contains: ')
    print(f'- Log files: {log_files}')
    print(f'- Dat files: {dat_files}')
    return []

# check_data('E:/CT_BENCH/2022-06-24_17_34_15-Edgar-140kv_100mAs')
# check_data('E:/CT_BENCH/data/2022_07_15/smaller_col/')
# plt.show()

# data = read_log('E:/CT_BENCH/2022-07-13/2022_07_13_UPENN_140kVp_80kVp_1150V_705V_330mA_285ms_thresh_94kV_tkeep_40-test_photodiode_13 Jul 2022_14_39_17_converted_.csv')
# print(data.columns)
# print(data.loc[102900:300000, 'Analog_In_3[mV]'])
