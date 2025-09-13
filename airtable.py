import os
from dotenv import load_dotenv
from pyairtable import Api
from pyairtable.formulas import match
from pyairtable import Table
import pandas as pd

load_dotenv()
API_KEY = os.getenv('API_KEY')
Base_id = os.getenv('Base_id')
Cell_table = os.getenv('Cell_table')
Cycle_table = os.getenv('Cycle_table')

data_upload_columns = ['Cell_Name', 'Cycle#', 'Current_mA',
                       'Cell_Discharge_Cap_mAh', 'Cell_Charge_Cap_mAh',
                       'AAM_Charge_Cap_mAh/g', 'AAM_Discharge_Cap_mAh/g',
                       'Coulombic_Efficiency', 'Retention_AF']

meta_data_columns = ['Name', 'Cell_Type', 'Cast', 'AAM', 'AAM_Material',
                     'AAM_Carbon_Type', 'N/P_Ratio', 'Electrolyte',
                     'Cyc20vsAF_Retention']

file_path = 'data/output/New_Cycle_Data.csv'

def get_record(filter: dict) -> dict:
    formula = match(filter)
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
    for index, row in New_Data_DF.iterrows():
        Cell_Name = row["cell_name"]
        Cycle = row["cycle#"]
        Current_mA = row['current_mA']
        Cell_Discharge_Cap_mAh = row['discharge_capacity(mAh)']
        Cell_Charge_Cap_mAh = row['charge_capacity(mAh)']
        data = {'Cell_Name': Cell_Name, 'Cycle#': Cycle, 'Current_mA': Current_mA,
                'Cell_Discharge_Cap_mAh': Cell_Discharge_Cap_mAh, 'Cell_Charge_Cap_mAh': Cell_Charge_Cap_mAh}
        cycle_table = Table(API_KEY, Base_id, Cycle_table)
        formula = f"AND({{Cell_Name}} = '{Cell_Name}', {{Cycle#}} = '{Cycle}')"
        records = cycle_table.all(formula=formula)
        if records:
            print("Entry already exists:", records[0]['fields']['Name'])
        else:
            create_record(data)

def get_cell_list(meta_data_columns):
    api = Api(API_KEY)
    table = api.table(Base_id, Cell_table)
    records = table.all(sort=['Name'], cell_format='string', user_locale='en-nz',
                        time_zone='America/Los_Angeles', fields=meta_data_columns)
    cell_df = pd.DataFrame(record['fields'] for record in records)
    cell_dict = cell_df.to_dict('records')
    cell_list = cell_df['Name'].tolist()
    return cell_dict, cell_list

def get_cell_record(filter:dict) -> dict:
    formula=match(filter)
    api = Api(API_KEY)
    table = api.table(Base_id, Cell_table)
    records = table.all(fields=meta_data_columns, cell_format='string', user_locale='en-nz',
                        time_zone='America/Los_Angeles',
                        formula=formula)
    result = pd.DataFrame(record["fields"] for record in records)
    return result

'''
New_Data_DF = pd.read_csv(file_path)
cells = New_Data_DF['cell_name'].unique().tolist()
#for cell in cells:
#    airtable_df = get_record({'cell_name': cell})
data_upload(New_Data_DF)
'''