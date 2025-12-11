#standard python package imports
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import math

#imports from other github users
import electrochem as echem
import NewareNDA

#imports from this project
import airtable

#load .env Data
load_dotenv()
dqdv_step = int(os.getenv('dqdv_diff'))
dqdv_smooth = int(os.getenv('dqdv_smooth'))
Directory = os.getenv('Directory')

PunchDiameter = 12


#setting up file tree
if os.path.exists(Directory + 'input/'):
    input_path = Directory + 'input/'
else:
    os.mkdir(Directory + 'input/')
    input_path = Directory + 'input/'
if os.path.exists(Directory + 'output/'):
    output_path = Directory + 'output/'
else:
    os.mkdir(Directory + 'output')
    output_path = Directory + 'output/'
if os.path.exists(Directory + 'output/csv/'):
    csv_path = Directory + 'output/csv/'
elif os.path.exists(Directory + 'csv/'):
    csv_path = Directory + 'csv/'
else:
    os.mkdir(Directory + 'csv/')
    csv_path = Directory + 'csv/'
if os.path.exists(Directory + 'output/capVplots/'):
    capVplot_path = Directory + 'output/capVplots/'
elif os.path.exists(Directory + 'capVplots/'):
    capVplot_path = Directory + 'capVplots/'
else:
    os.mkdir(Directory + 'capVplots/')
    capVplot_path = Directory + 'capVplots/'
if os.path.exists(Directory + 'output/dqdvPlots/'):
    dqdvplot_path = Directory + 'output/dqdvPlots/'
elif os.path.exists(Directory + 'dqdvPlots/'):
    dqdvplot_path = Directory + 'dqdvPlots/'
else:
    os.mkdir(Directory + 'dqdvPlots/')
    dqdvplot_path = Directory + 'dqdvPlots/'

def converttimestamp(x):
    return pd.to_datetime(x, unit='d', origin=pd.Timestamp('1900-1-1'))


def convertdf(df, extension, filename):
    converted_df = pd.DataFrame(columns=['step_time', 'datetime', 'cycle', 'step',
                                         'status', 'current(mA)', 'voltage(V)',
                                         'charge_capacity(mAh)', 'discharge_capacity(mAh)'])
    if extension == '.res':
        converted_df['step_time'] = df['Step_Time']
        converted_df['datetime'] = df['DateTime'].apply(converttimestamp)
        converted_df['step'] = df['Step_Index']
        converted_df['cycle'] = df['Cycle_Index']
        converted_df['current(mA)'] = df['Current'] * 1000
        converted_df['voltage(V)'] = df['Voltage']
        converted_df['charge_capacity(mAh)'] = df['Charge_Capacity'] * 1000
        converted_df['discharge_capacity(mAh)'] = df['Discharge_Capacity'] * 1000
        converted_df.loc[converted_df['current(mA)'] == 0, 'status'] = 'rest'
        converted_df.loc[converted_df['current(mA)'] < 0, 'status'] = 'discharge'
        converted_df.loc[converted_df['current(mA)'] > 0, 'status'] = 'charge'
    elif extension == '.ndax':
        converted_df['step_time'] = df['Time']
        converted_df['datetime'] = df['Timestamp']
        converted_df['step'] = df['Step']
        converted_df['cycle'] = df['Cycle']
        converted_df['current(mA)'] = df['Current(mA)']
        converted_df['voltage(V)'] = df['Voltage']
        converted_df['charge_capacity(mAh)'] = df['Charge_Capacity(mAh)']
        converted_df['discharge_capacity(mAh)'] = df['Discharge_Capacity(mAh)']
        converted_df.loc[converted_df['current(mA)'] == 0, 'status'] = 'rest'
        converted_df.loc[converted_df['current(mA)'] < 0, 'status'] = 'discharge'
        converted_df.loc[converted_df['current(mA)'] > 0, 'status'] = 'charge'
    return converted_df

def parseHPPC(cell_number, df, PunchDiameter, HPPC_Data):
    fulldata = df
    oneCdischarge = fulldata.loc[fulldata['step'] == 5, 'discharge_capacity(mAh)'].iloc[-1]
    initialOCV = fulldata.loc[fulldata['step'] == 10, 'voltage(V)'].iloc[-1]
    VoltageSteps = fulldata.groupby('step')['voltage(V)'].apply(list).to_dict()
    CurrentSteps = fulldata.groupby('step')['current(mA)'].apply(list).to_dict()
    PulseCurrent = np.mean(CurrentSteps[11])
    DischargeCurrent = np.mean(CurrentSteps[15])
    PulseOCV = VoltageSteps[17]
    PulseOCV.insert(0, initialOCV)
    PulseOCV = PulseOCV[:-1]
    FiveCVoltage = VoltageSteps[11]
    NumberOfPulses = (len(FiveCVoltage)/20)
    ListOfPulses = list(range(1, int(NumberOfPulses) + 1))
    VoltageIndex = [(pulse * 20) - 1 for pulse in ListOfPulses]
    EndVoltage = [FiveCVoltage[pulse] for pulse in VoltageIndex]
    irDF = pd.DataFrame(columns=['Cell_ID', 'SOC', 'OCV', 'PulseEndV',
                                      'IR Drop', 'Pulse Current', 'Discharge Current',
                                      'Resistance(Ohms)', 'Areal Resistance(Ohms/cm^2)'])
    irDF['OCV'] = PulseOCV[:11]
    irDF['PulseEndV'] = EndVoltage[:11]
    irDF = irDF.iloc[:11]
    irDF['Cell_ID'] = cell_number
    irDF['SOC'] = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0]
    irDF['IR Drop'] = irDF['PulseEndV'] - irDF['OCV']
    irDF['Pulse Current'] = PulseCurrent/1000
    irDF['Discharge Current'] = DischargeCurrent/1000
    irDF['Resistance(Ohms)'] = irDF['IR Drop']/irDF['Pulse Current']
    irDF['Areal Resistance(Ohms/cm^2)'] = irDF['Resistance(Ohms)'] / np.pi*np.square(((PunchDiameter/2)/10))
    HPPC_Data.append(irDF)
    return HPPC_Data

def HPPC(input_path, PunchDiameter):
    HPPC_Data = []
    if os.path.isdir(input_path):
        files = os.listdir(input_path)
        for file in files:
            file_path = os.path.join(input_path, file)
            filename, extension = os.path.splitext(file)
            #parse filename
            if filename[0] =='P': #old naming convention
                cell_number = file.split('_')[1]
                cell_type = file.split('_')[3]
                cell_tester = file.split('_')[4]
            elif filename[0] == 'C': #new naming convention
                cell_number = file.split('_')[0]
                cell_type = file.split('_')[2]
                cell_tester = file.split('_')[3]

        #identify filetype
            if extension == '.res':
                cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
                df = echem.parseArbin(file_path)
                df = convertdf(df, extension, filename)
                df.to_csv(output_path + '/' + filename + '.csv')
            elif extension == '.ndax':
                cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
                df = NewareNDA.read(file_path, cycle_mode='auto')
                df = convertdf(df, extension, filename)
                df.to_csv(output_path + '/' + filename + '.csv')
            elif extension == '.csv':
                df = pd.read_csv(file_path)
                #cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
                HPPC_Data = parseHPPC(cell_number, df, PunchDiameter, HPPC_Data)
            elif extension == '.xlsx':
                df = pd.read_excel(file_path)
                cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
                HPPC_Data = parseHPPC(cell_number, df, PunchDiameter, HPPC_Data)
            elif filename == '.gitkeep':
                continue
            else:
                print("unknown format" + filename)
            print(filename)
        HPPC_DF = pd.concat(HPPC_Data, ignore_index=True)
        HPPC_DF.to_csv(output_path + '/' + 'HPPC_Summary' + '.csv')




HPPC(input_path, PunchDiameter)
