#standard python package imports
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#imports from other github users
import electrochem as echem
import NewareNDA

#setting up file tree
input_path = 'data/input'
output_path = 'data/output'
csv_path = 'data/output/csv'
capVplot_path = 'data/output/capVplots'
dqdvplot_path = 'data/output/dqdvPlots'


def convertdf(df, cell_tester):
    converted_df = pd.DataFrame(columns=['step_time', 'datetime', 'cycle', 'step',
                                         'status', 'current(mA)', 'voltage(V)',
                                         'charge_capacity(mAh)', 'discharge_capacity(mAh)'])
    if cell_tester == 'Arbin':
        converted_df['step_time'] = df['Step_Time']
        converted_df['datetime'] = pd.to_datetime(df['DateTime'][0], unit='d', origin=pd.Timestamp('1899-12-30'))
        converted_df['step'] = df['Step_Index']
        converted_df['cycle'] = df['Cycle_Index']
        converted_df['current(mA)'] = df['Current'] * 1000
        converted_df['voltage(V)'] = df['Voltage']
        converted_df['charge_capacity(mAh)'] = df['Charge_Capacity'] * 1000
        converted_df['discharge_capacity(mAh)'] = df['Discharge_Capacity'] * 1000
        converted_df.loc[converted_df['current(mA)'] == 0, 'status'] = 'rest'
        converted_df.loc[converted_df['Current(mA)'] < 0, 'status'] = 'discharge'
        converted_df.loc[converted_df['Current(mA)'] > 0, 'status'] = 'charge'
    elif cell_tester == 'Neware':
        converted_df['step_time'] = df['Time']
        converted_df['datetime'] = df['Timestamp']
        converted_df['step'] = df['Step']
        converted_df['cycle'] = df['Cycle']
        converted_df['status'] = df['Status']
        converted_df['current(mA)urrent(mA)'] = df['Current(mA)']
        converted_df['voltage(V)'] = df['Voltage']
        converted_df['charge_capacity(mAh)'] = df['Charge_Capacity(mAh)']
        converted_df['discharge_capacity(mAh)'] = df['Discharge_Capacity(mAh)']
    return converted_df

def splitcycledata(filename, df, cell_type, cell_number, start_cycle, end_cycle,
                   cell_data, output_path, csv_path, capVplot_path, dqdvplot_path):
    cyclelist = df['cycle'].unique().tolist()
    cyclerange = list(range(start_cycle, end_cycle+2))
    for i in cyclelist:
        cycleDF = df.loc[df['cycle'].isin([i])]
        steps = cycleDf['step'].unique().tolist()
        try:
            x = len(steps)
            if x<4:
                raise ValueError("Incomplete Cycle")
        except ValueError:
            continue
        else:
            if cyclelist[0] == cyclerange[0]:
                cycle = i
            else:
                cycle = cycle_range[i - 1]
            current = float(abs(cycleDF.loc[cycleDF['status'] == 'charge', 'current(mA)'].values[1]))
            charge_capacity = float(cycleDF.loc[cycleDF['status'] == 'charge', 'charge_capacity(mAh)'].iloc[-1])
            discharge_capacity = float(cycleDF.loc[cycleDF['status'] == 'discharge', 'discharge_capacity(mAh)'].iloc[-1])
            cycle_data = pd.DataFrame([{'cell_name': cell_number,
                                        'cycle#': cycle,
                                        'current_mA': current,
                                        'discharge_capacity(mAh)': discharge_capacity,
                                        'charge_capacity(mAh)': charge_capacity}])
        cell_data = pd.concat([cycle_data, cell_data], ignore_index=True)
        name = filename.split('_')
    return cell_data


#setting up dataframes
cycle_data =pd.DataFrame(index=[],
                         columns=['cell_name', 'cycle#', 'current_mA',
                                  'cell_discharge_capacity_mAh', 'cell_charge_capacity_mAh'])
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
        df = echem.parseArbin(file_path)
        df = convertdf(df, cell_tester)
    elif extension == '.ndax':
        df = NewareNDA.read(file_path, cycle_mode='auto')
        df = convertdf(df, cell_tester)
    elif extension == '.csv':
        df = pd.read_csv(file_path)
    elif extension == '.xlsx':
        df = pd.read_excel(file_path)

    cycle_data = splitcycledata(filename, df, cell_type, cell_number, start_cycle, end_cycle,
                                cycle_data, output_path, csv_path, capVplot_path, dqdvplot_path)
    print(filename)
