from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import os
import plotly.graph_objects as go
from pyairtable import Api
from pyairtable.formulas import match
import airtable
from dotenv import load_dotenv


#Load Data
load_dotenv()
Repository = os.getenv('Repository')
meta_data_columns = ['Name', 'Cell_Type', 'Cast', 'AAM', 'AAM_Material', 'AAM_Carbon_Type', 'N/P_Ratio', 'Electrolyte', 'Cyc20vsAF_Retention']
cell_df = airtable.get_cell_list(meta_data_columns)
cell_df['id'] = cell_df['Name']
cell_df.set_index('id', inplace=True, drop=False)
filter_options = ['Cell_Type', 'Cast', 'AAM', 'Electrolyte']
filter_choices = airtable.get_filter_choices(filter_options)
cycles = ['1', '2', '3']
test = airtable.get_record('C440')
cells_chosen = []
#records = pd.DataFrame(columns=meta_data_columns)
#cycle_life = airtable.get_record({'Cell_Name': 'C432'})

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
                                                       page_size=10)
                                  ], style={}),
                        html.Div(
                            [dash_table.DataTable(id='selected_cells',
                                                  data=cell_df.to_dict('records'),
                                                  columns=[{'name': i, 'id': i} for i in cell_df.columns],
                                                  row_deletable=True)], style={}),
                        html.Div(
                            [
                                dcc.RadioItems(id='cycle_life_view',
                                                options=['Cell Capacity', 'Specific Capacity', 'Retention', 'Efficiency'],
                                                value='Cell Capacity', inline=True),
                                dcc.Graph(figure={'layout': {'title': 'Cycle Life'}}, id='cycle_life')
                            ], style={'display':'100%', 'border': '2px solid black'}),
                        html.Div(
                            [
                                html.Div([
                                        dcc.Graph(figure={'layout': {'title': 'Nyquist Plot'}}, id='eis')
                                     ], style={'flex-basis': '50%', 'height': '100%'})
                                ], style={}),
                        html.Div(
                             [
                                html.Div(
                                       [dcc.Graph(
                                          figure={'layout': {'title': 'Cycle Data'}},
                                           id='cycle_data')],
                                    style={'flex-basis': '80%'}),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        dcc.RadioItems(id='cell_view',
                                                               options=['Cell Capacity vs Voltage',
                                                                        'Specific Capacity vs Voltage',
                                                                        'Time vs Voltage',
                                                                        'dQ/dV'],
                                                               value='Cell Capacity vs Voltage')
                                                        ], style={'flex-basis': '50%'}),
                                                html.Div(
                                                    [
                                                        dcc.Dropdown(id='cycle_selection', options=cycles,
                                                             multi=True, value=[], placeholder='Select Cycles')
                                                        ], style={'flex-basis': '50%'})
                                            ], style={'display': 'flex', 'flexDirection': 'row', 'border': '2pt solid black', 'flex-basis': '20%'}),
                                    ], style={'flex-basis': '50%', 'display': 'flex', 'flexDirection': 'column', 'border':'2pt solid yellow'}),
                    ], style={})
                ])


# App Controls
@callback(Output(component_id='selected_cells', component_property='data'),
          Input(component_id='cell_table', component_property='selected_row_ids'))
def update_selected_cells(selected_cells):
    if selected_cells is None:
        selected_cells = []
    records = pd.DataFrame(columns=meta_data_columns)
    cells = cell_df['id'][selected_cells].tolist()
    for cell in cells:
        record = airtable.get_cell_record(cell)
        records = pd.concat([records, record], ignore_index=True)
    selected_cell_data = records.to_dict('records')
    return selected_cell_data


@callback(
    Output(component_id='eis', component_property='figure'),
    Input(component_id='selected_cells', component_property='data')
)
def update_eis(cells_chosen):
    fig = go.Figure()
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
    fig.update_layout(title={'text': 'Nyquist Plot', 'xanchor': 'center', 'x': 0.5}, autotypenumbers='convert types', height=600,
                      legend=dict(orientation='h', yanchor='top', xanchor='left', y=-.1))
    fig.update_xaxes(title="Z'")
    fig.update_yaxes(scaleanchor='x', scaleratio=1.5, title='-Z"')
    return fig


@callback(
    Output(component_id='cycle_life', component_property='figure'),
    [Input(component_id='selected_cells', component_property='data'),
     Input(component_id='cycle_life_view', component_property='value')]
)
def update_cyclelife(cells_chosen, cycle_life_view):
    fig = go.Figure()
    if cells_chosen is None:
        cells_chosen = []
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    for cell in cells:
        cycle_life = airtable.get_record(cell)
        if cycle_life_view == 'Cell Capacity':
            fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Cell_Discharge_Cap_mAh'],
                                      mode='markers',
                                      name=cell))
            fig.update_yaxes(title='Cell Capacity(mAh)')
        elif cycle_life_view == 'Specific Capacity':
            fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['AAM_Discharge_Cap_mAh/g'],
                                      mode='markers',
                                      name=cell))
            fig.update_yaxes(title='Specific Capacity (mAh/g)')
        elif cycle_life_view == 'Retention':
            fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Retention_AF'],
                                      mode='markers',
                                      name=cell))
            fig.update_yaxes(title='Capacity Retention(%)')
        elif cycle_life_view == 'Efficiency':
            fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                      y=cycle_life['Coulombic_Efficiency'],
                                      mode='markers',
                                      name=cell))
            fig.update_yaxes(title='Coulombic Efficiency(%)')
    fig.update_layout(title={'text': 'Cycle Life', 'xanchor': 'center', 'x': 0.5}, autotypenumbers='convert types',
                      legend=dict(orientation='h', yanchor='top', y=-.1))
    fig.update_xaxes(title='Cycle#')
    return fig


@callback(
    Output(component_id='cycle_data', component_property='figure'),
    Input(component_id='selected_cells', component_property='data')
)
def update_cycle(cells_chosen):
    fig = go.Figure()
    if cells_chosen is None:
        cells_chosen = []
    cells = [d['Name'] for d in cells_chosen if 'Name' in d]
    for cell in cells:
        cycle_life = airtable.get_record(cell)
        fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                  y=cycle_life['Cell_Discharge_Cap_mAh'],
                                  mode='markers',
                                  name=cell))
    fig.update_layout(title={'text': 'Cycle Data', 'xanchor': 'center', 'x': 0.5}, autotypenumbers='convert types',
                          height=600,
                          legend=dict(orientation='h', yanchor='top', y=-.1))
    fig.update_xaxes(title='Cycle#')
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

'''
@callback(Output(component_id='cell_table', component_property='data'),
          Input(component_id='cell_selector', component_property='value')
          )
def update_table(cells_chosen):
    records = pd.DataFrame(columns=meta_data_columns)
    for cell in cells_chosen:
        record = airtable.get_cell_record({'Name': cell})
        records = pd.concat([records, record], ignore_index=True)
    cell_dict = records.to_dict('records')
    return cell_dict
'''

if __name__ == '__main__':
    app.run(debug=True)



#,
#dcc.Graph(figure={}, id='single_cycle'),
#dcc.Dropdown(id='cycles', options=cycle_list, multi=True, value=[]),

'''
html.Div(
                                    [
                                        html.P("Cell Selector"),
                                        html.P("Filtering Options"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.P("Cell Type"),
                                                        dcc.Dropdown(id='cell_type',
                                                                     options=['All',
                                                                              'Full Cell',
                                                                              'Cathode Half Cell',
                                                                              'Anode Half Cell'],
                                                                     value=['Full Cell'])
                                                    ], style={}),
                                                html.Div(
                                                    [
                                                        html.P('Cast'),
                                                        dcc.Dropdown(id='cast_name',
                                                                     options=cast_names,
                                                                        value=['Any'])
                                                    ], style={}),
                                                html.Div(
                                                    [
                                                        html.P('Anode Active Material'),
                                                        dcc.Dropdown(id='AAM',
                                                                        options=AAM_names,
                                                                        value=['Any'])
                                                    ], style={}),
                                                html.Div(
                                                    [
                                                        html.P('Electrolyte'),
                                                        dcc.Dropdown(id='Electrolyte',
                                                                     options=electrolyte_names,
                                                                     value=['Any'])
                                                    ], style={'flex-basis': '10%'}),
                                            ], style={'display': 'flex', 'flexDirection': 'column'}),
                                        html.P("Cell Selection"),
                                        dcc.Dropdown(id='cell_selector', options=cells, multi=True, value=[])
                                    ], style={'flex-basis': '50%', 'border': '2px solid yellow'}),
'''