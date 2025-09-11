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
cell_dict, cells = airtable.get_cell_list(meta_data_columns)
filter_options = ['Cell_Type', 'Cast', 'AAM', 'Electrolyte']
filter_choices = airtable.get_filter_choices(filter_options)
#records = pd.DataFrame(columns=meta_data_columns)
#cycle_life = airtable.get_record({'Cell_Name': 'C432'})

#Initialize the App
app = Dash()

#App layout
app.layout = html.Div(
            [
            html.Div(
                [
                    html.Div([dash_table.DataTable(id='meta_data', data=cell_dict,
                                                   columns=[{'name': i, 'id': i} for i in meta_data_columns],
                                                   page_size=10)]),
                    html.Div(
                        [
                        html.Div(
                            [
                            html.P("Cell Selector"),
                            html.P("Filters"),
                            dcc.Dropdown(id='filter_options', options=filter_options, multi=True, value=[]),
                            html.P("Filtered Options"),
                            dcc.Dropdown(id='filter_choices', options=filter_choices, multi=True, value=[]),
                            html.P("Cell Selection"),
                            dcc.Dropdown(id='cell_selector', options=cells, multi=True, value=[])
                            ],
                            style={"border": "2px solid black", 'flex-basis': '40%'}),
                        html.Div(
                            [
                            html.Div(
                                [dcc.RadioItems(
                                    id='cycle_life_view',
                                    options=['Cell Capacity', 'Specific Capacity', 'Retention', 'Efficiency'],
                                    value='Cell Capacity', inline=True)
                                    ],
                                style={'border': '4px dashed blue'}
                            ),
                            html.Div(
                                [dcc.Graph(figure={'layout': {'title': 'Cycle Life'}}, id='cycle_life')
                                 ],
                                style={"border": "2px solid green"}
                            )
                        ], style={"border": "4px dashed green", 'flex-basis': '60%'})
                            ], style={'border': '4px dashed black', 'display': 'flex', 'flexDirection': 'row'}
                    ),
                    html.Div([
                        html.Div([dcc.Graph(figure={'layout': {'title': 'Nyquist Plot'}}, id='eis')],
                                 style={'flex-basis': '50%'}),
                        html.Div([dcc.Graph(figure={'layout': {'title': 'Cycle Data'}}, id='cycle_data')],
                                 style={'flex-basis': '50%'})],
                        style={'display': 'flex', 'flexDirection': 'row', "border": "2px solid yellow"}),
                    ], style={'display': 'block', "border": "4px dashed red"})
                ])

# App Controls

@callback(
        Output(component_id='filter_choices', component_property='value'),
        Input(component_id='filter_options', component_property='value')
)
def update_filters(filters_chosen):
    for filter in filters_chosen:
        choice = airtable.get_filter_choices(filter)
    return choice

@callback(
    Output(component_id='eis', component_property='figure'),
    Input(component_id='cell_selector', component_property='value')
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
    Output(component_id='cycle_data', component_property='figure'),
    Input(component_id='cell_selector', component_property='value')
)
def update_cycle(cells_chosen):
    fig = go.Figure()
    for cell in cells_chosen:
        cycle_life = airtable.get_record({'Cell_Name': cell})
        fig.add_traces(go.Scatter(x=cycle_life['Cycle#'],
                                  y=cycle_life['Cell_Discharge_Cap_mAh'],
                                  mode='markers',
                                  name=cell))
    fig.update_layout(title={'text': 'Cycle Data', 'xanchor': 'center', 'x': 0.5}, autotypenumbers='convert types',
                          height=600,
                          legend=dict(orientation='h', yanchor='top', y=-.1))
    fig.update_xaxes(title='Cycle#')
    return fig


@callback(Output(component_id='meta_data', component_property='data'),
          Input(component_id='cell_selector', component_property='value')
          )
def update_table(cells_chosen):
    records = pd.DataFrame(columns=meta_data_columns)
    for cell in cells_chosen:
        record = airtable.get_cell_record({'Name': cell})
        records = pd.concat([records, record], ignore_index=True)
    cell_dict = records.to_dict('records')
    return cell_dict

@callback(
    Output(component_id='cycle_life', component_property='figure'),
    [Input(component_id='cell_selector', component_property='value'),
     Input(component_id='cycle_life_view', component_property='value')]
)
def update_cyclelife(cells_chosen, cycle_life_view):
    fig = go.Figure()
    for cell in cells_chosen:
        cycle_life = airtable.get_record({'Cell_Name': cell})
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
    fig.update_layout(title={'text': 'Cycle Life', 'xanchor': 'center', 'x': 0.5}, autotypenumbers='convert types', height=600,
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

if __name__ == '__main__':
    app.run(debug=True)



#,
#dcc.Graph(figure={}, id='single_cycle'),
#dcc.Dropdown(id='cycles', options=cycle_list, multi=True, value=[]),


