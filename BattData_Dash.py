from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import pandas as pd
import os
import plotly.graph_objects as go
from pyairtable import Api
from pyairtable.formulas import match
import airtable
from dotenv import load_dotenv
import json


#Load Data
load_dotenv()
Repository = os.getenv('Repository')
dqdv_step = int(os.getenv('dqdv_diff'))
dqdv_smooth = int(os.getenv('dqdv_smooth'))
filter_names = os.getenv('Filter_Columns')
cell_performance_names = os.getenv('Cell_Performance_Columns')

#meta_data_columns = ['Name', 'Cell_Type', 'Cast', 'AAM', 'AAM_Material', 'AAM_Carbon_Type', 'N/P_Ratio', 'Electrolyte', 'Cyc20vsAF_Retention']
filter_columns = filter_names.split(',')
cell_performance_columns = cell_performance_names.split(',')
cell_df = airtable.get_cell_list(filter_columns)
performance_df = airtable.get_cell_list(cell_performance_columns)
cell_df['id'] = cell_df['Name']
performance_df['id'] = performance_df['Name']
performance_df.set_index('id', inplace=True, drop=False)
cell_df.set_index('id', inplace=True, drop=False)
filter_choices = airtable.get_filter_choices(filter_columns)
cells_chosen = []
cycles = []
cycle_life_fig = go.Figure(layout=go.Layout(
    title={'text': 'Cycle Life', 'xanchor': 'center', 'x': 0.5},
    autotypenumbers='convert types',
    height=600,
    legend={'orientation': 'h', 'yanchor': 'top', 'xanchor': 'left', 'y': -.1}))
eis_fig = go.Figure(layout=go.Layout(
    title={'text': 'Nyquist Plot', 'xanchor': 'center', 'x': 0.5},
    autotypenumbers='convert types',
    height=600,
    legend={'orientation': 'h', 'yanchor': 'top', 'xanchor': 'left', 'y': -.1}))
cycle_data_fig = go.Figure(layout=go.Layout(
    title={'text': 'Voltage Profile', 'xanchor': 'center', 'x': 0.5},
    autotypenumbers='convert types',
    height=600,
    legend={'orientation': 'h', 'yanchor': 'top', 'xanchor': 'left', 'y': -0.1}))

'''
test = airtable.get_record('C440')
fig = go.Figure()
cells = ['C441', 'C442']
selected_cycles = ['0001']
for cell in cells:
    cell_directory = Repository + 'csv/' + cell + '/'
    cycle_data = os.listdir(cell_directory)
    for cycle in cycle_data:
        filename = os.path.join(cell_directory, cycle)
        cycle_number = cycle.split('_')[2]
        if cycle_number in selected_cycles:
            df = pd.read_csv(filename)
            charge = df.loc[df['status'].isin(['charge'])]
            charge_time = charge['step_time'].apply(lambda x: f"{x // 3600}Hr:{(x % 3600) // 60}Mn")
            discharge = df.loc[df['status'].isin(['discharge'])]
            discharge_time = discharge['step_time'].apply(lambda x: f"{x // 3600}Hr:{(x % 3600) // 60}Mn")
'''


#Initialize the App
app = Dash()

#App layout
app.layout = html.Div(
            [
                html.Div(
                    [
                        html.Div([dash_table.DataTable(id='cell_table',
                                                       data=cell_df.to_dict('records'),
                                                       columns=[
                                                           {'name': i, 'id': i, 'selectable': True}
                                                           for i in cell_df.columns],
                                                       editable=True,
                                                       filter_action='native',
                                                       sort_action='native',
                                                       sort_mode='multi',
                                                       column_selectable='multi',
                                                       row_selectable='multi',
                                                       selected_columns=[],
                                                       selected_rows=[],
                                                       page_action='native',
                                                       page_current=0,
                                                       page_size=10,
                                                       style_table={'overflowX': 'auto'})
                                  ], style={}),
                        html.Div(
                            [dash_table.DataTable(id='selected_cells',
                                                  data=performance_df.to_dict('records'),
                                                  columns=[{'name': i, 'id': i} for i in performance_df.columns],
                                                  row_deletable=True,
                                                  style_table={'overflowX': 'auto'})
                                ], style={}),
                        html.Div(
                            [
                                dcc.RadioItems(id='cycle_life_view',
                                                options=['Cell Capacity', 'Specific Capacity', 'Retention', 'Efficiency'],
                                                value='Cell Capacity', inline=True),
                                dcc.Graph(figure=cycle_life_fig, id='cycle_life')
                            ], style={'display':'100%', 'border': '2px solid black'}),
                        html.Div(
                            [
                                html.Div([
                                        dcc.Graph(figure=eis_fig, id='eis')
                                     ], style={'flex-basis': '50%', 'height': '100%'})
                                ], style={}),
                        html.Div(
                             [
                                html.Div(
                                       [dcc.Graph(
                                          figure=cycle_data_fig,
                                           id='single_cycle_view')],
                                    style={'flex-basis': '80%'}),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        dcc.RadioItems(id='cycle_view',
                                                               options=['Cell Capacity vs Voltage',
                                                                        'Specific Capacity vs Voltage',
                                                                        'Time vs Voltage',
                                                                        'dQ/dV'],
                                                               value='Cell Capacity vs Voltage')
                                                        ], style={'flex-basis': '50%'}),
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(id='selected_cycles', options=cycles,
                                                             multi=True, value=[], placeholder='Select Cycles')
                                                        ], style={'flex-basis': '50%'})
                                            ], style={'display': 'flex', 'flexDirection': 'row', 'border': '2pt solid black', 'flex-basis': '20%'}),
                                    ], style={'flex-basis': '50%', 'display': 'flex', 'flexDirection': 'column', 'border':'2pt solid yellow'}),
                    ], style={})
                ])


# App Controls

# Update DataTable
@callback(Output(component_id='selected_cells', component_property='data'),
          Input(component_id='cell_table', component_property='selected_row_ids'))
def update_selected_cells(selected_cells):
    if selected_cells is None:
        selected_cells = []
    records = pd.DataFrame(columns=filter_columns)
    cells = cell_df['id'][selected_cells].tolist()
    for cell in cells:
        record = airtable.get_cell_record(cell)
        record['id'] = record['Name']
        records = pd.concat([records, record], ignore_index=True)
    selected_cell_data = records.to_dict('records')
    return selected_cell_data


@callback(Output(component_id='cell_table', component_property='selected_rows'),
          Input(component_id='selected_cells', component_property='data'),
          State(component_id='cell_table', component_property='data'))
def update_cell_table(selected_cells, checked_cells):
    active_cells = set(cell['id'] for cell in selected_cells)
    new_active_cells = [i for i, cell in enumerate(checked_cells) if cell['id'] in active_cells]
    return new_active_cells

# Update Cycle Life Plot
@callback(
    Output(component_id='cycle_life', component_property='figure'),
    [Input(component_id='selected_cells', component_property='data'),
     Input(component_id='cycle_life_view', component_property='value')]
)
def update_cyclelife(cells_chosen, cycle_life_view):
    fig = cycle_life_fig
    fig.data = []
    if cells_chosen is None:
        cells_chosen = []
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    for cell in cells:
        cycle_life = airtable.get_record(cell)
        if cycle_life_view == 'Cell Capacity':
            fig.add_traces([go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Cell_Discharge_Cap_mAh'],
                                      mode='markers',
                                      name=cell)])
            fig.update_yaxes(title='Cell Capacity(mAh)')
        elif cycle_life_view == 'Specific Capacity':
            fig.add_traces([go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['AAM_Discharge_Cap_mAh/g'],
                                      mode='markers',
                                      name=cell)])
            fig.update_yaxes(title='Specific Capacity (mAh/g)')
        elif cycle_life_view == 'Retention':
            fig.add_traces([go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Retention_AF'],
                                      mode='markers',
                                      name=cell)])
            fig.update_yaxes(title='Capacity Retention(%)')
        elif cycle_life_view == 'Efficiency':
            fig.add_traces([go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Coulombic_Efficiency'],
                                      mode='markers',
                                      name=cell)])
            fig.update_yaxes(title='Coulombic Efficiency(%)')
    fig.update_xaxes(title='Cycle#')
    return fig


# Update EIS Plot
@callback(
    Output(component_id='eis', component_property='figure'),
    Input(component_id='selected_cells', component_property='data')
)
def update_eis(cells_chosen):
    fig = eis_fig
    fig.data = []
    if cells_chosen is None:
        cells_chosen = []
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    for cell in cells:
        file_path = Repository + 'eis/' + cell
        data_to_plot = os.listdir(file_path)
        for data in data_to_plot:
            data_path = os.path.join(file_path, data)
            df = pd.read_excel(data_path)
            filename, extension = os.path.splitext(data)
            if filename[4] == '_':
                testdata = filename.split('_')
                if len(testdata) == 2:
                    cell = testdata[0]
                    cycle = testdata[1]
                    extra = ''
                elif len(testdata) == 3:
                    cell = testdata[0]
                    cycle = testdata[1]
                    extra = testdata[2]
                if cycle[5] == '0':
                    if cycle[6] == '0':
                        cyclename = 'Cy' + cycle[7] + cycle[8]
                    else:
                        cyclename = 'Cy' + cycle[6] + cycle[7] + cycle[8]
                else:
                    cyclename = 'Cy' + cycle[5] + cycle[6] + cycle[7] + cycle[8]
                if len(testdata) == 2:
                    plotname = cell + '_' + cyclename
                elif len(testdata) == 3:
                    plotname = cell + '_' + cyclename + '_' + extra
            else:
                plotname = filename
            num_columns = len(df.columns)
            if df.columns[0] == 'Column 1':
                if num_columns == 2:
                    x = df['Column 1']
                    y = df['Column 2']
                elif num_columns == 3:
                    x = df['Column 2']
                    y = df['Column 3']
                elif num_columns == 6:
                    x = df['Column 2']
                    y = df['Column 3']
            elif df.columns[0] == 'Frequency (Hz)':

                x = df["Z' (Ω)"]
                y = df['-Z'' (Ω)']
            fig.add_traces(go.Scatter(x=x, y=y, mode='lines+markers', name=plotname))
    fig.update_xaxes(title="Z'")
    fig.update_yaxes(scaleanchor='x', scaleratio=1.5, title='-Z"')
    return fig

# Update Cycle List
@callback(
    Output(component_id='selected_cycles', component_property='options'),
    Input(component_id='selected_cells', component_property='data')
)
def update_cycle_list(cells_chosen):
    if cells_chosen is None:
        cells_chosen=[]
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    cycle_numbers = []
    for cell in cells:
        cell_directory = Repository + 'csv/' + cell + '/'
        cycle_data = os.listdir(cell_directory)
        for file in cycle_data:
            file_path = os.path.join(cell_directory, file)
            filename, extension = os.path.splitext(file)
            cycle_number = filename.split('_')[2]
            file_type = filename.split('_')[-1]
            if file_type == 'cycle':
                cycle_numbers.append(cycle_number)
            else:
                continue
    return cycle_numbers


# Update Cycle Data Plot
@callback(
    Output(component_id='single_cycle_view', component_property='figure'),
    [Input(component_id='selected_cells', component_property='data'),
     Input(component_id='selected_cycles', component_property='value'),
     Input(component_id='cycle_view', component_property='value')]
)
def update_single_cycle(cells_chosen, selected_cycles, cycle_view):
    fig = cycle_data_fig
    fig.data = []
    if cells_chosen is None:
        cells_chosen = []
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    for cell in cells:
        cell_directory = Repository + 'csv/' + cell + '/'
        cycle_data = os.listdir(cell_directory)
        for cycle in cycle_data:
            filename = os.path.join(cell_directory, cycle)
            cycle_number = cycle.split('_')[2]
            if cycle_number in selected_cycles:
                df = pd.read_csv(filename)
                charge = df.loc[df['status'].isin(['charge'])]
                charge_time = charge['step_time'].apply(lambda x: f"{x // 3600}Hr:{(x % 3600) // 60}Mn")
                discharge = df.loc[df['status'].isin(['discharge'])]
                discharge_time = discharge['step_time'].apply(lambda x: f"{x // 3600}Hr:{(x % 3600) // 60}Mn")
                dqdv_data = pd.DataFrame({
                    'step': df['step'], 'status': df['status'], 'current(mA)': df['current(mA)'],
                    'voltage(V)': df['voltage(V)'], 'DV': df['voltage(V)'].diff(dqdv_step),
                    'charge_capacity(mAh)': df['charge_capacity(mAh)'],
                    'dq_charge': df['charge_capacity(mAh)'].diff(dqdv_step),
                    'discharge_capacity(mAh)': df['discharge_capacity(mAh)'],
                    'dq_discharge': df['discharge_capacity(mAh)'].diff(dqdv_step)})
                dqdv_data = dqdv_data[abs(dqdv_data['DV']) > 0.001]
                dqdv_data['dqdv_charge'] = dqdv_data['dq_charge'] / dqdv_data['DV']
                dqdv_data['smoothed_charge'] = dqdv_data['dqdv_charge'].rolling(window=dqdv_smooth).mean()
                dqdv_data['dqdv_discharge'] = dqdv_data['dq_discharge'] / dqdv_data['DV']
                dqdv_data['smoothed_discharge'] = dqdv_data['dqdv_discharge'].rolling(window=dqdv_smooth).mean()
                dqdv_charge = dqdv_data[dqdv_data['status'] == 'charge']
                dqdv_discharge = dqdv_data[dqdv_data['status'] == 'discharge']
                if cycle_view == 'Cell Capacity vs Voltage':
                    fig.add_traces([go.Scatter(x=discharge['discharge_capacity(mAh)'],
                                               y=discharge['voltage(V)'],
                                               mode='lines',
                                               name=cell + '_Discharge'),
                                    go.Scatter(x=charge['charge_capacity(mAh)'],
                                               y=charge['voltage(V)'],
                                               mode='lines',
                                               name=cell + '_Charge')])
                    fig.update_xaxes(title='Cell Capacity (mAh)')
                elif cycle_view == 'Specific Capacity vs Voltage':
                    cell_aam_wt = airtable.get_AAM_Wt({'Name': cell})
                    specific_charge = charge['charge_capacity(mAh)'] / cell_aam_wt
                    specific_discharge = discharge['discharge_capacity(mAh)'] / cell_aam_wt
                    fig.add_traces([go.Scatter(x=specific_discharge,
                                               y=discharge['voltage(V)'],
                                               mode='lines',
                                               name=cell + '_Discharge'),
                                    go.Scatter(x=specific_charge,
                                               y=charge['voltage(V)'],
                                               mode='lines',
                                               name=cell + '_Charge')])
                    fig.update_xaxes(title='Specific Capacity(mAh/g)')
                elif cycle_view == 'Time vs Voltage':
                    fig.add_traces([go.Scatter(x=discharge_time,
                                               y=discharge['voltage(V)'],
                                               mode='lines',
                                               name=cell + '_Discharge'),
                                   go.Scatter(x=charge_time,
                                              y=charge['voltage(V)'],
                                              mode='lines',
                                              name=cell + '_Charge')])
                    fig.update_xaxes(title='Step Time (s)', nticks=20)
                elif cycle_view == 'dQ/dV':
                    fig.add_traces([go.Scatter(x=dqdv_discharge['voltage(V)'],
                                              y=dqdv_discharge['smoothed_discharge'],
                                              mode='lines',
                                              name=cell + '_' + cycle_number + '_Discharge'),
                                   go.Scatter(x=dqdv_charge['voltage(V)'],
                                              y=dqdv_charge['smoothed_charge'],
                                              mode='lines',
                                              name=cell + '_' + cycle_number + '_Charge')])
                    fig.update_xaxes(title='Voltage')

    return fig


if __name__ == '__main__':
    app.run(debug=True)
