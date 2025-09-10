from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import os
import plotly.graph_objects as go
from pyairtable import Api
from pyairtable.formulas import match
import airtable
from dotenv import load_dotenv


#Load Data
Repository = os.getenv('Repository')
meta_data_columns = ['Name', 'Cell_Type', 'Cast', 'AAM', 'AAM_Material', 'AAM_Carbon_Type', 'N/P_Ratio', 'Electrolyte', 'Cyc20vsAF_Retention']
cells = airtable.get_cell_list()
cycle_list = []
#cycle_life = airtable.get_record({'Cell_Name': 'C432'})

#Initialize the App
app = Dash()

#App layout
app.layout = [
    html.Div(children='Cell Tracking'),
    html.Hr(),
    dcc.Dropdown(id='multi_select_dropdown', options=cells, multi=True, value=[]),
    dcc.Graph(figure={}, id='cycle_life'),
    dcc.Graph(figure={}, id='eis')
]

# App Controls
@callback(
    Output(component_id='eis', component_property='figure'),
    Input(component_id='multi_select_dropdown', component_property='value')
)
def update_eis(cells_chosen):
    fig = go.Figure()
    for cell in cells_chosen:
        file_path = Repository + 'eis/' + cell
        data_to_plot = os.listdir(file_path)
        for data in data_to_plot:
            data_path = os.path.join(file_path, data)
            df = pd.read_excel(data_path)
            filename, extension = os.path.splitext(data)
            num_columns = len(df.columns)
            if df.columns[0] == 'Column 1':
                if num_columns == 2:
                    x = df['Column 1']
                    y = df['Column 2']
                    #plt.plot(df['Column 1'], df['Column 2'])
                elif num_columns == 3:
                    x = df['Column 2']
                    y = df['Column 3']
                    #plt.plot(df['Column 2'], df['Column 3'])
                elif num_columns == 6:
                    x = df['Column 2']
                    y = df['Column 3']
            elif df.columns[0] == 'Frequency (Hz)':

                x = df["Z' (Ω)"]
                y = df['-Z'' (Ω)']
            fig.add_traces(go.Scatter(x=x, y=y, mode='lines+markers', name=filename))
    fig.update_layout(autotypenumbers='convert types', height=600)
    fig.update_xaxes(title="Z'")
    fig.update_yaxes(scaleanchor='x', scaleratio=1.5, title='-Z"')
    return fig

@callback(
    Output(component_id='cycle_life', component_property='figure'),
    Input(component_id='multi_select_dropdown', component_property='value')
)
def update_cyclelife(cells_chosen):
    fig = go.Figure()
    for cell in cells_chosen:
        cycle_life = airtable.get_record({'Cell_Name': cell})
        fig.add_traces(go.Scatter(x=cycle_life['Cycle#'], y=cycle_life['Cell_Charge_Cap_mAh'], mode='markers', name=cell + '_Charge'))
        fig.add_traces(go.Scatter(x=cycle_life['Cycle#'], y=cycle_life['Cell_Discharge_Cap_mAh'], mode='markers', name=cell + '_Discharge'))
    fig.update_layout(autotypenumbers='convert types', height=600)
    fig.update_xaxes(title='Cycle#')
    fig.update_yaxes(title='Capacity(mAh)')
    return fig


'''
@callback(
    Output(component_id='single_cycle', component_property='figure'),
    [Input(component_id='multi_select_dropdown', component_property='value'), Input(component_id='cycles', component_property='value')]
)
def update_CapV(cells_chosen, cycles):
    fig = go.Figure()
    for cell in cells_chosen:
        file_path = Repository + 'csv/' + cell + '/'
        files = os.listdir(file_path)
        for file in files:
            filename = os.path.join(file_path, file)
            cycle = file.split('_')[2]
            if cycle in cycles:
                df = pd.read_csv(filename)
                charge = df.loc[df['status'].isin(['charge'])]
                discharge = df.loc[df['status'].isin(['discharge'])]
                fig.add_traces(go.Scatter(x=charge['charge_capacity(mAh)'], y=charge['voltage(V)'], mode='line', name='Charge'))
                fig.add_traces(go.Scatter(x=discharge['discharge_capacity(mAh)'], y=charge['voltage(V)'], mode='line', name='Discharge'))
    return fig
    
@callback(
    Output(component_id='cycles', component_property='cycle_list'),
    Input(component_id='cycle_life', component_property='cycle_list')
)
def update_cycles(cycle_list):
    return cycle_list

'''

if __name__ == '__main__':
    app.run(debug=True)



#dash_table.DataTable(id='meta_data', data=df_dict, page_size=10),
#dcc.Graph(figure={}, id='single_cycle'),
#dcc.Dropdown(id='cycles', options=cycle_list, multi=True, value=[]),


