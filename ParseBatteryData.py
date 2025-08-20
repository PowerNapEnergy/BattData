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
    elif extension == '.ndax':
        df = NewareNDA.read(file_path, cycle_mode='auto')
    elif extension == '.csv':
        df = pd.read_csv(file_path)
    elif extension == '.xlsx':
        df = pd.read_excel(file_path)
    print(filename)
