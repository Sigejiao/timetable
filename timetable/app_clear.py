import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_table
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_manager import DataManager

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "时间管理可视化"

# Data manager
data_manager = DataManager()

# Color palette
COLOR_LIST = [
    '#40DE5A', '#00C17F', '#00B3A4', '#00E3C9', '#4CBBFF',
    '#6A8FFF', '#9B4CFF', '#DE1AAD', '#FF4C8F', '#F7ECB5',
    '#E4C07E', '#C49A67', '#B78B3A', '#A65C2A', '#DA3A1B',
    '#FF4F00', '#FF8C1A', '#FFB800', '#C4D313', '#99D84B',
]

# Helper: list of recent dates
def get_recent_dates(days):
    today = datetime.now().date()
    return [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(days))]

# App layout
app.layout = html.Div([
    html.H1("时间管理可视化", style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Bar chart section
    html.Div([
        dcc.Graph(id='bar-chart', config={'displayModeBar': False, 'doubleClick': False}),
        html.Div([
            html.Label("显示天数："),
            dcc.Dropdown(
                id='days-dropdown',
                options=[{'label': f'最近{n}天', 'value': n} for n in (3, 7, 14, 30)],
                value=7,
                style={'width': '120px'}
            )
        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'marginTop': '10px'})
    ], style={'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px'}),

    # Main content: schedule table & clock ring
    html.Div([
        html.Div([
            html.H3("时间安排表"),
            dcc.Dropdown(
                id='schedule-sort-dropdown',
                options=[
                    {'label': '按开始时间', 'value': 'start_time'},
                    {'label': '按事件名称', 'value': 'event'}
                ],
                value='start_time',
                clearable=False,
                style={'width': '140px'}
            ),
            dash_table.DataTable(
                id='schedule-table',
                columns=[
                    {'name': '+', 'id': 'add-row', 'presentation': 'markdown'},
                    {'name': '时', 'id': 'start_hour', 'presentation': 'dropdown'},
                    {'name': '分', 'id': 'start_minute', 'presentation': 'dropdown'},
                    {'name': '秒', 'id': 'start_second', 'presentation': 'dropdown'},
                    {'name': '结束时间', 'id': 'end_time'},
                    {'name': '颜色', 'id': 'color', 'presentation': 'markdown'},
                    {'name': '事件', 'id': 'event', 'editable': True},
                    {'name': '时长', 'id': 'duration'},
                    {'name': '×', 'id': 'delete-row', 'presentation': 'markdown'},
                ],
                data=[],
                dropdown={
                    col: {
                        'clearable': False,
                        'options': [
                            {'label': f"{i:02d}", 'value': f"{i:02d}"}
                            for i in (range(24) if 'hour' in col else range(60))
                        ]
                    } for col in ('start_hour', 'start_minute', 'start_second')
                },
                style_cell={'textAlign': 'center', 'minWidth': '40px'},
                markdown_options={'html': True}
            )
        ], style={'width': '48%', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px'}),

        html.Div([
            html.H3("时间分布表盘"),
            dcc.Graph(id='clock-ring', config={'displayModeBar': False})
        ], style={'width': '48%', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '8px'})
    ], style={'display': 'flex', 'gap': '4%', 'marginTop': '20px'}),

    # Hidden stores and interval
    dcc.Store(id='current-selected-date', data=datetime.now().strftime('%Y-%m-%d')),
    dcc.Store(id='all-data', data={}),
    dcc.Interval(id='clock-refresh', interval=600000)
])

# Callback: load all data when days change
@app.callback(
    Output('all-data', 'data'),
    Input('days-dropdown', 'value')
)
def load_data(days):
    return data_manager.load_all_data()

# Callback: update bar chart
@app.callback(
    Output('bar-chart', 'figure'),
    Input('all-data', 'data'),
    Input('days-dropdown', 'value')
)
def update_bar(all_data, days):
    dates = get_recent_dates(days)
    fig = go.Figure()
    for date in dates:
        events = data_manager.parse_time_events(date) if date in all_data else []
        # TODO: build stacked bars here
    fig.update_layout(barmode='stack', plot_bgcolor='white')
    return fig

# Callback: handle bar click -> update selected date
@app.callback(
    Output('current-selected-date', 'data'),
    Input('bar-chart', 'clickData')
)
def on_bar_click(click):
    if click and click.get('points'):
        return click['points'][0]['x']
    return datetime.now().strftime('%Y-%m-%d')

# Callback: update schedule table data on date or sort change
@app.callback(
    Output('schedule-table', 'data'),
    Input('current-selected-date', 'data'),
    Input('schedule-sort-dropdown', 'value')
)
def update_table(date, sort_by):
    events = data_manager.parse_time_events(date)
    if sort_by == 'event':
        events = sorted(events, key=lambda e: e.get('event', ''))
    rows = []
    # fill each row
    for idx, e in enumerate(events or [{'time':'00:00:00','event':'未命名'}]):
        hh, mm, ss = e['time'].split(':')
        # compute end_time and duration (implement as needed)
        end_time = '23:59:59'
        duration = 0.0
        color = f"<div style='background-color:{COLOR_LIST[idx % len(COLOR_LIST)]};width:20px;height:20px;border-radius:3px;'></div>"
        rows.append({
            'add-row': '**+**',
            'start_hour': hh, 'start_minute': mm, 'start_second': ss,
            'end_time': end_time,
            'color': color,
            'event': e.get('event', ''),
            'duration': f"{duration:.1f}",
            'delete-row': '**×**'
        })
    return rows

# Callback: clear active_cell when clicking elsewhere (bar-chart used as proxy)
@app.callback(
    Output('schedule-table', 'active_cell'),
    Input('bar-chart', 'n_clicks')
)
def clear_active(_):
    return None

# Callback: handle table edits and button ops
@app.callback(
    Output('schedule-table', 'data'),
    Output('schedule-table', 'active_cell'),
    Input('schedule-table', 'data'),
    Input('schedule-table', 'active_cell'),
    State('current-selected-date', 'data')
)
def table_ops(data, active_cell, date):
    prop = callback_context.triggered[0]['prop_id'].split('.')[0]
    # TODO: implement save on edit, add/delete row logic
    return data, active_cell

# Callback: update clock ring
@app.callback(
    Output('clock-ring', 'figure'),
    Input('current-selected-date', 'data'),
    Input('all-data', 'data'),
    Input('clock-refresh', 'n_intervals')
)
def update_ring(date, all_data, _):
    events = data_manager.parse_time_events(date)
    fig = go.Figure()
    # TODO: build pie chart segments here
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
