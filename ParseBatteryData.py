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


#setting up file tree

input_path = 'data/input'
output_path = 'data/output'
csv_path = 'data/output/csv'
capVplot_path = 'data/output/capVplots'
dqdvplot_path = 'data/output/dqdvPlots'


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


def splitcycledata(filename, df, cell_aam_wt, cell_type, cell_number, start_cycle, end_cycle,
                   cell_data, output_path, csv_path, capVplot_path, dqdvplot_path):
    cyclelist = df['cycle'].unique().tolist()
    cyclerange = list(range(start_cycle, end_cycle+2))
    for i in cyclelist:
        cycleDF = df.loc[df['cycle'].isin([i])]
        steps = cycleDF['step'].unique().tolist()
        if cyclelist[0] == cyclerange[0]:
            cycle = i
        else:
            cycle = cyclerange[i - 1]
        step_types = cycleDF['status'].tolist()
        charge_steps = cycleDF.loc[cycleDF['status'] == 'charge', 'step'].unique().tolist()
        discharge_steps = cycleDF.loc[cycleDF['status'] == 'discharge', 'step'].unique().tolist()
        step_sequence = []
        prev = object()
        for item in step_types:
            if item != prev:
                step_sequence.append(item)
            prev = item
        try:
            index = step_sequence.index('charge')
        except ValueError:
            print('Incomplete Cycle:' + cell_number + '_' + 'Cycle' + str(cycle))
            continue
        else:
            pass
        try:
            index = step_sequence.index('discharge')
        except ValueError:
            print('Incomplete Cycle:' + cell_number + '_' + 'Cycle' + str(cycle))
            continue
        else:
            pass
        try:
            final_step = step_sequence[-1]
            if final_step != 'rest':
                print('Incomplete Cycle:' + cell_number + '_' + 'Cycle' + str(cycle))
                continue
            else:
                pass
        finally:
            current = float(abs(cycleDF.loc[cycleDF['status'] == 'charge', 'current(mA)'].values[1]))
            if len(charge_steps) == 1:
                charge_capacity = float(cycleDF.loc[cycleDF['status'] == 'charge', 'charge_capacity(mAh)'].iloc[-1])
            elif len(charge_steps) == 2:
                cc_charge = float(cycleDF.loc[cycleDF['step'] == charge_steps[0], 'charge_capacity(mAh)'].iloc[-1])
                cv_charge = float(cycleDF.loc[cycleDF['step'] == charge_steps[1], 'charge_capacity(mAh)'].iloc[-1])
                if cycleDF.loc[cycleDF['step'] == charge_steps[1], 'charge_capacity(mAh)'].iloc[0] == 0:
                    cycleDF.loc[cycleDF['step'] == charge_steps[1], 'charge_capacity(mAh)'] \
                        += float(cycleDF.loc[cycleDF['step'] == charge_steps[0], 'charge_capacity(mAh)'].iloc[-1])
                    charge_capacity = float(cycleDF.loc[cycleDF['step'] == charge_steps[1], 'charge_capacity(mAh)'].iloc[-1])
                else:
                    charge_capacity = float(
                        cycleDF.loc[cycleDF['step'] == charge_steps[1], 'charge_capacity(mAh)'].iloc[-1])
            discharge_capacity = float(cycleDF.loc[cycleDF['status'] == 'discharge', 'discharge_capacity(mAh)'].iloc[-1])
            cycle_data = {'cell_name': cell_number,
                                        'cycle#': cycle,
                                        'current_mA': current,
                                        'discharge_capacity(mAh)': discharge_capacity,
                                        'charge_capacity(mAh)': charge_capacity}
            dqdv_data = pd.DataFrame({
                'step': cycleDF['step'], 'status': cycleDF['status'], 'current(mA)': cycleDF['current(mA)'],
                'voltage(V)': cycleDF['voltage(V)'], 'DV': cycleDF['voltage(V)'].diff(dqdv_step),
                'charge_capacity(mAh)': cycleDF['charge_capacity(mAh)'], 'dq_charge': cycleDF['charge_capacity(mAh)'].diff(dqdv_step),
                'discharge_capacity(mAh)': cycleDF['discharge_capacity(mAh)'], 'dq_discharge': cycleDF['discharge_capacity(mAh)'].diff(10)})
            dqdv_data = dqdv_data[abs(dqdv_data['DV']) > 0.001]
            dqdv_data['dqdv_charge'] = dqdv_data['dq_charge'] / dqdv_data['DV']
            dqdv_data['smoothed_charge'] = dqdv_data['dqdv_charge'].rolling(window=dqdv_smooth).mean()
            dqdv_data['dqdv_discharge'] = dqdv_data['dq_discharge'] / dqdv_data['DV']
            dqdv_data['smoothed_discharge'] = dqdv_data['dqdv_discharge'].rolling(window=dqdv_smooth).mean()
        cell_data.append(cycle_data)
        name = filename.split('_')
        if name[0][0] == 'P':
            name[2] = str(cycle).zfill(4)
        elif name[0][0] == 'C':
            name[1] = str(cycle).zfill(4)
        filename = '_'.join(name)
        cycleDF.to_csv(csv_path + '/' + filename + '.csv')
        dqdv_data.to_csv(csv_path + '/' + filename + '_dqdv.csv')
        plotCapV(filename, cycleDF, cell_number, cell_aam_wt, cell_type, capVplot_path)
        plotdqdv(filename, dqdv_data, dqdvplot_path, cell_number, cycle)
    return cell_data

def plotCapV(filename, df, cell_number, cell_aam_wt, cell_type, output_path):
    cellCap_plot = os.path.splitext(os.path.split(filename)[1])[0] + "_CellCapV.png" #add CapV to filename and change extension to .png
    specificCap_plot = os.path.splitext(os.path.split(filename)[1])[0] + "_SpecificCapV.png"
    charge = df.loc[df['status'].isin(['charge'])]
    specific_charge = charge['charge_capacity(mAh)']/cell_aam_wt
    discharge = df.loc[df['status'].isin(['discharge'])]
    specific_discharge = discharge['discharge_capacity(mAh)'] / cell_aam_wt
    plt.plot(discharge['discharge_capacity(mAh)'], discharge['voltage(V)'], label='Discharge', color='blue')
    plt.plot(charge['charge_capacity(mAh)'], charge['voltage(V)'], label='Charge', color='red')
    plt.title(os.path.splitext(os.path.split(filename)[1])[0])
    plt.legend()
    plt.xlabel('Cell Capacity(mAh)')
    plt.ylabel('Voltage(V)')
    plt.savefig(output_path + '/' + cellCap_plot)
    plt.clf()
    plt.plot(specific_discharge, discharge['voltage(V)'], label='Discharge', color='blue')
    plt.plot(specific_charge, charge['voltage(V)'], label='Charge', color='red')
    plt.title(os.path.splitext(os.path.split(filename)[1])[0])
    plt.legend()
    plt.xlabel('Specific Capacity(mAh/g)')
    plt.ylabel('Voltage(V)')
    plt.savefig(output_path + '/' + specificCap_plot)
    plt.clf()


def plotdqdv(filename, dqdv_data, output_path, cell_number, cycle):
    plot_name = os.path.splitext(os.path.split(filename)[1])[0] + '_dqdv.png'
    charge = dqdv_data[dqdv_data['status'] == 'charge']
    discharge = dqdv_data[dqdv_data['status'] == 'discharge']
    charge_max = str(charge['smoothed_charge'].max())
    discharge_min = str(discharge['smoothed_discharge'].min())
    if charge_max == 'nan':
        if discharge_min == 'nan':
            print('No Data:' + cell_number + '_' + 'Cycle' + str(cycle))
        else:
            charge_peak = discharge_peak = abs(math.floor((discharge['smoothed_discharge'].min())*10)/10)
    elif discharge_min == 'nan':
        charge_peak = discharge_peak = abs(math.ceil((charge['smoothed_charge'].max())*10)/10)
    else:
        charge_peak = abs(math.ceil((charge['smoothed_charge'].max())*10)/10)
        discharge_peak = abs(math.floor((discharge['smoothed_discharge'].min())*10)/10)
    plt.plot(charge['voltage(V)'], charge['smoothed_charge'], label='Charge', color='red')
    plt.plot(discharge['voltage(V)'], discharge['smoothed_discharge'], label='Discharge', color='blue')
    plt.title(plot_name)
    plt.legend()
    if charge_peak >= discharge_peak:
        plt.ylim(-charge_peak, charge_peak)
    elif charge_peak < discharge_peak:
        plt.ylim(-discharge_peak, discharge_peak)
    plt.xlabel('Voltage(V)')
    plt.ylabel('DQ/DV')
    plt.savefig(output_path + '/' + plot_name)
    plt.clf()


#setting up dataframes
cycle_data = []
updated_cells = []

'''
main function-takes files from input folder and produces:
        1) A csv for each individual cycle
        2) a csv summarizing the charge and discharge capacity for each cycle for each cell
        3) a Capacity vs Voltage Plot for each cycle for each cell
        4) a dqdv plot for each cycle for each cell
'''
files = os.listdir(input_path)
for file in files:
    file_path = os.path.join(input_path, file)
    filename, extension = os.path.splitext(file)
    #parse filename
    if filename[0] =='P': #old naming convention
        cell_number = file.split('_')[1]
        cycle_number = file.split('_')[2].replace('Cycle',"")
        if "-" in cycle_number:
            if cycle_number[3] == '-':
                start_cycle = int(cycle_number[1:3])
                end_cycle = int(cycle_number[4:])
            elif cycle_number[4] == '-':
                starting_cycle = int(cycle_number[1:4])
                end_cycle = int(cycle_number[5:])
        else:
            start_cycle = end_cycle = int(cycle_number)
        cell_type = file.split('_')[3]
        cell_tester = file.split('_')[4]
    elif filename[0] == 'C': #new naming convention
        cell_number = file.split('_')[0]
        cycle_number = file.split('_')[1]
        if "-" in cycle_number:
            cycle_range = cycle_number.split('-')
            start_cycle = int(cycle_range[0])
            end_cycle = int(cycle_range[1])
        else:
            start_cycle = end_cycle = int(cycle_number)
        cell_type = file.split('_')[2]
        cell_tester = file.split('_')[3]

    #identify filetype
    if extension == '.res':
        cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
        df = echem.parseArbin(file_path)
        df = convertdf(df, extension, filename)
    elif extension == '.ndax':
        cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
        df = NewareNDA.read(file_path, cycle_mode='auto')
        df = convertdf(df, extension, filename)
    elif extension == '.csv':
        df = pd.read_csv(file_path)
        cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
    elif extension == '.xlsx':
        df = pd.read_excel(file_path)
        cell_aam_wt = airtable.get_AAM_Wt({'Name': cell_number})
    elif filename == '.gitkeep':
        continue
    else:
        print("unknown format" + filename)


    cycle_data = splitcycledata(filename, df, cell_aam_wt, cell_type, cell_number, start_cycle, end_cycle,
                                cycle_data, output_path, csv_path, capVplot_path, dqdvplot_path)
    print(filename)
cycle_data = pd.DataFrame(cycle_data)
cycle_data.to_csv(output_path + '/' + 'New_Cycle_Data' + '.csv', index=False)
airtable.data_upload(cycle_data)

