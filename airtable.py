import os
from dotenv import load_dotenv
from pyairtable import Api
from pyairtable.formulas import match
from pyairtable import Table
import pandas as pd
from collections import OrderedDict

load_dotenv()
API_KEY = os.getenv('API_KEY')
Base_id = os.getenv('Base_id')
Cell_table = os.getenv('Cell_table')
Cycle_table = os.getenv('Cycle_table')
filter_names = os.getenv('Filter_Columns')
cell_performance_names = os.getenv('Cell_Performance_Columns')

data_upload_columns = ['Cell_Name', 'Cycle#', 'Current_mA',
                       'Cell_Discharge_Cap_mAh', 'Cell_Charge_Cap_mAh',
                       'AAM_Charge_Cap_mAh/g', 'AAM_Discharge_Cap_mAh/g',
                       'Coulombic_Efficiency', 'Retention_AF']

meta_data_columns = ['Name', 'Cell_Type', 'Cast', 'AAM', 'AAM_Material',
                     'AAM_Carbon_Type', 'N/P_Ratio', 'Electrolyte',
                     'Cyc20vsAF_Retention']

filter_columns = filter_names.split(',')

cell_performance_columns = cell_performance_names.split(',')


file_path = 'data/output/New_Cycle_Data.csv'


def get_record(cell):
    formula = f"{{Cell_Name}} = '{cell}'"
    api = Api(API_KEY)
    table = api.table(Base_id, Cycle_table)
    records = table.all(sort=['Cycle#'], fields=data_upload_columns,
                        cell_format='string', user_locale='en-nz',
                        time_zone='America/Los_Angeles', formula=formula)
    result = pd.DataFrame(record['fields'] for record in records)
    return result


def get_AAM_Wt(filter: dict) -> dict:
    formula = match(filter)
    api = Api(API_KEY)
    table = api.table(Base_id, Cell_table)
    records = table.all(sort=['Name'], fields=['Name', 'g_AAM_Active'], formula=formula)
    cell_aam_df = pd.DataFrame(record['fields'] for record in records)
    cell_aam_wt = float(cell_aam_df['g_AAM_Active'][0])
    return cell_aam_wt


def create_record(record: dict) -> dict:
    api = Api(API_KEY)
    table = api.table(Base_id, Cycle_table)
    result = table.create(record)
    return result


def data_upload(New_Data_DF):
    api = Api(API_KEY)
    for index, row in New_Data_DF.iterrows():
        Cell_Name = row["cell_name"]
        Cycle = row["cycle#"]
        Current_mA = row['current_mA']
        Cell_Discharge_Cap_mAh = row['discharge_capacity(mAh)']
        Cell_Charge_Cap_mAh = row['charge_capacity(mAh)']
        data = {'Cell_Name': Cell_Name, 'Cycle#': Cycle, 'Current_mA': Current_mA,
                'Cell_Discharge_Cap_mAh': Cell_Discharge_Cap_mAh, 'Cell_Charge_Cap_mAh': Cell_Charge_Cap_mAh}
        cycle_table = api.table(Base_id, Cycle_table)
        formula = f"AND({{Cell_Name}} = '{Cell_Name}', {{Cycle#}} = '{Cycle}')"
        records = cycle_table.all(formula=formula)
        if records:
            print("Entry already exists:", records[0]['fields']['Name'])
        else:
            create_record(data)


def get_cell_list(table_columns):
    api = Api(API_KEY)
    table = api.table(Base_id, Cell_table)
    records = table.all(sort=['Name'], cell_format='string', user_locale='en-nz',
                        time_zone='America/Los_Angeles', fields=table_columns)
    cell_df = pd.DataFrame(record['fields'] for record in records)
    cell_df_filled = cell_df.fillna('Na')
    cell_df_filled['First_Below_80%Ret'] = cell_df_filled['First_Below_80%Ret'].astype(int)
    cell_df_reordered = cell_df_filled[table_columns]
    return cell_df_reordered


def get_cell_record(cell):
    formula = f"{{Name}} = '{cell}'"
    api = Api(API_KEY)
    table = api.table(Base_id, Cell_table)
    records = table.all(fields=cell_performance_columns, cell_format='string', user_locale='en-nz',
                        time_zone='America/Los_Angeles',
                        formula=formula)
    records_list = records[0]['fields']
    for column in cell_performance_columns:
        if column in records_list:
            pass
        else:
            records_list[column] = ''
    result = pd.DataFrame(record["fields"] for record in records)
    result_filled = result.fillna('Na')
    result_filled['First_Below_80%Ret'] = result_filled['First_Below_80%Ret'].astype(int)
    result_reordered = result_filled[cell_performance_columns]
    return result_reordered
