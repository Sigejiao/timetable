import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from data_manager import DataManager

# 初始化Dash应用
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "时间管理可视化"

# 初始化数据管理器
data_manager = DataManager()

# 应用布局
app.layout = html.Div([
    # 标题
    html.H1("时间管理可视化", style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),

    # 柱状图（单独一行）
    html.Div([
        dcc.Graph(
            id='bar-chart',
            config={'displayModeBar': False},
            style={'height': '320px'}
        ),
        html.Div([
            html.Label("显示天数："),
            dcc.Dropdown(
                id='days-dropdown',
                options=[
                    {'label': '最近3天', 'value': 3},
                    {'label': '最近7天', 'value': 7},
                    {'label': '最近14天', 'value': 14},
                    {'label': '最近30天', 'value': 30}
                ],
                value=7,
                style={'width': '150px', 'display': 'inline-block', 'marginLeft': '10px'}
            )
        ], style={'textAlign': 'right', 'marginTop': '-40px', 'marginRight': '30px'})
    ], style={'width': '100%', 'marginBottom': '10px'}),

    # 下方左右分栏
    html.Div([
        # 左侧：详细表格
        html.Div([
            html.H3("详细事件列表", style={'textAlign': 'center', 'marginBottom': '10px'}),
            html.Div(id='detail-list', style={
                'height': '320px',
                'overflowY': 'auto',
                'backgroundColor': '#fff',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px #f0f1f2',
                'padding': '10px'
            })
        ], style={'width': '55%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        # 右侧：圆环饼状图
        html.Div([
            html.H3("时间分布表盘", style={'textAlign': 'center', 'marginBottom': '10px'}),
            dcc.Graph(
                id='clock-ring',
                config={'displayModeBar': False},
                style={'height': '320px'}
            )
        ], style={'width': '43%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
    ], style={'width': '100%', 'marginTop': '10px'}),

    # 隐藏的存储组件
    dcc.Store(id='current-selected-date', data=datetime.now().strftime("%Y-%m-%d")),
    dcc.Store(id='all-data', data={}),
    
    # 右键菜单（暂时隐藏，后续实现）
    html.Div(id='context-menu', style={'display': 'none'}),
    
    # 状态栏
    html.Div([
        html.Span("当前选中日期：", id='current-date-display'),
        html.Span(" | "),
        html.Span("数据文件数量：", id='data-count-display')
    ], style={'textAlign': 'center', 'marginTop': '30px', 'color': '#7f8c8d'})
])

# 回调函数：初始化数据
@app.callback(
    Output('all-data', 'data'),
    Input('days-dropdown', 'value')
)
def load_data(days):
    """加载数据"""
    all_data = data_manager.load_all_data()
    return all_data

# 回调函数：更新柱状图
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('all-data', 'data'),
     Input('days-dropdown', 'value')]
)
def update_bar_chart(all_data, days):
    """更新柱状图"""
    if not all_data:
        return go.Figure()
    
    # 获取最近的日期
    dates = list(all_data.keys())
    if days and len(dates) > days:
        dates = dates[-days:]
    
    # 准备图表数据
    fig = go.Figure()
    
    for date in dates:
        events = data_manager.parse_time_events(date)
        if not events:
            continue
        
        # 为每个事件创建一段柱状图
        for event in events:
            start_hour = float(event['start_time'].split(':')[0]) + float(event['start_time'].split(':')[1]) / 60
            end_hour = float(event['end_time'].split(':')[0]) + float(event['end_time'].split(':')[1]) / 60
            duration = end_hour - start_hour
            
            fig.add_trace(go.Bar(
                x=[date],
                y=[duration],
                name=event['event'],
                base=start_hour,
                marker_color='lightblue',
                showlegend=False,
                hovertemplate=f"<b>{date}</b><br>" +
                             f"时间: {event['start_time']} - {event['end_time']}<br>" +
                             f"事件: {event['event']}<br>" +
                             f"时长: {duration:.2f}小时<extra></extra>"
            ))
    
    # 更新布局
    fig.update_layout(
        title="每日时间分布",
        xaxis_title="日期",
        yaxis_title="时间（小时）",
        yaxis=dict(range=[0, 24]),
        barmode='stack',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

# 回调函数：更新详细信息列表
@app.callback(
    Output('detail-list', 'children'),
    [Input('bar-chart', 'clickData'),
     Input('current-selected-date', 'data')]
)
def update_detail_list(click_data, selected_date):
    """更新详细事件列表"""
    if not selected_date:
        return html.P("请选择一个日期查看详细信息")
    
    events = data_manager.parse_time_events(selected_date)
    
    if not events:
        return html.P("该日期暂无数据")
    
    # 创建事件列表
    event_items = []
    for i, event in enumerate(events):
        event_items.append(
            html.Div([
                html.Span(f"{event['start_time']} - {event['end_time']}", 
                         style={'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.Span(" | "),
                html.Span(event['event'], style={'color': '#34495e'}),
                html.Span(f" ({event['duration']:.2f}h)", 
                         style={'color': '#7f8c8d', 'fontSize': '12px'})
            ], style={
                'padding': '8px',
                'borderBottom': '1px solid #ecf0f1',
                'backgroundColor': '#f8f9fa' if i % 2 == 0 else 'white'
            })
        )
    
    return event_items

# 回调函数：更新表盘
@app.callback(
    Output('clock-ring', 'figure'),
    [Input('current-selected-date', 'data')]
)
def update_clock_ring(selected_date):
    """更新表盘环形图"""
    if not selected_date:
        return go.Figure()
    
    events = data_manager.parse_time_events(selected_date)
    
    if not events:
        return go.Figure()
    
    # 准备饼图数据
    labels = [event['event'] for event in events]
    values = [event['duration'] for event in events]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,  # 创建环形图
        textinfo='label+percent',
        textposition='inside'
    )])
    
    fig.update_layout(
        title=f"{selected_date} 时间分布",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# 回调函数：处理柱状图点击
@app.callback(
    Output('current-selected-date', 'data'),
    [Input('bar-chart', 'clickData')]
)
def handle_bar_click(click_data):
    """处理柱状图点击事件"""
    if click_data and click_data['points']:
        return click_data['points'][0]['x']
    return datetime.now().strftime("%Y-%m-%d")

# 回调函数：更新状态栏
@app.callback(
    [Output('current-date-display', 'children'),
     Output('data-count-display', 'children')],
    [Input('current-selected-date', 'data'),
     Input('all-data', 'data')]
)
def update_status_bar(selected_date, all_data):
    """更新状态栏信息"""
    date_display = f"当前选中日期：{selected_date}"
    count_display = f"数据文件数量：{len(all_data) if all_data else 0}"
    return date_display, count_display

# 运行应用
if __name__ == '__main__':
    print("启动时间管理可视化应用...")
    print("正在加载数据...")
    
    # 测试数据加载
    dates = data_manager.get_all_dates()
    print(f"找到 {len(dates)} 个数据文件: {dates}")
    
    # 启动应用
    app.run(debug=True, host='127.0.0.1', port=8050) 