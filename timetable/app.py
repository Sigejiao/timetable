import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_manager import DataManager

# 初始化Dash应用
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "时间管理可视化"

# 初始化数据管理器
data_manager = DataManager()

# 统一配色方案，与clock_renderer.py一致
COLOR_LIST = [
    '#40DE5A',  # 草绿
    '#00C17F',  # 翠绿
    '#00B3A4',  # 青石
    '#00E3C9',  # 浅碧
    '#4CBBFF',  # 天蓝
    '#6A8FFF',  # 薄荷蓝
    '#9B4CFF',  # 淡紫
    '#DE1AAD',  # 品红
    '#FF4C8F',  # 玫瑰
    '#F7ECB5',  # 柔沙
    '#E4C07E',  # 小麦
    '#C49A67',  # 暖驼
    '#B78B3A',  # 卡其
    '#A65C2A',  # 棕褐
    '#DA3A1B',  # 深朱
    '#FF4F00',  # 朱红
    '#FF8C1A',  # 橙黄
    '#FFB800',  # 琥珀
    '#C4D313',  # 黄绿
    '#99D84B',  # 青柠
]

# 应用布局
app.layout = html.Div([
    # 标题
    html.H1("时间管理可视化", style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),

    # 柱状图（单独一行）
    html.Div([
        dcc.Graph(
            id='bar-chart',
            figure=go.Figure(),  # 初始空图表
            config={
                'displayModeBar': False,  # 不显示任何工具栏按钮
                'doubleClick': False     # 禁用双击行为
            },
            style={'height': '500px'}
        ),
        html.Div([
            html.Label("显示天数：", style={'marginRight': '8px', 'fontSize': '16px'}),
            dcc.Dropdown(
                id='days-dropdown',
                options=[
                    {'label': '最近3天', 'value': 3},
                    {'label': '最近7天', 'value': 7},
                    {'label': '最近14天', 'value': 14},
                    {'label': '最近30天', 'value': 30}
                ],
                value=7,
                style={'width': '120px', 'display': 'inline-block'}
            )
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'flex-end',
            'marginTop': '20px',
            'marginRight': '30px'
        }),
    ], style={'width': '100%', 'marginBottom': '10px'}),

    # 下方左右分栏
    html.Div([
        # 左侧：预留区域
        html.Div([
            html.H3("左侧区域", style={'textAlign': 'center', 'marginBottom': '10px'}),
            html.Div(id='left-panel', style={
                'height': '100%',
                'overflowY': 'auto',
                'backgroundColor': '#fff',
                'borderRadius': '12px',
                'boxShadow': '0 2px 12px #f0f1f2',
                'padding': '16px',
                'margin': '0 8px',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'flex-start',
            })
        ], style={'width': '48%', 'display': 'flex', 'flexDirection': 'column', 'background': 'none', 'boxShadow': 'none', 'marginRight': '2%', 'marginBottom': '0', 'height': '100%'}),

        # 右侧：圆环饼状图
        html.Div([
            html.H3("时间分布表盘", style={'textAlign': 'center', 'marginBottom': '10px'}),
            html.Div([
                dcc.Graph(
                    id='clock-ring',
                    figure=go.Figure(),
                    config={'displayModeBar': False},
                    style={'height': '100%', 'width': '100%'}
                )
            ], style={
                'backgroundColor': '#fff',
                'borderRadius': '12px',
                'boxShadow': '0 2px 12px #f0f1f2',
                'padding': '16px',
                'margin': '0 8px',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'center',   # 垂直居中
                'alignItems': 'center',       # 水平居中
                'height': '100%',
            })
        ], style={'width': '48%', 'display': 'flex', 'flexDirection': 'column', 'background': 'none', 'boxShadow': 'none', 'marginBottom': '0', 'height': '100%'}),
    ], style={'width': '100%', 'marginTop': '40px', 'padding': '0 10px', 'display': 'flex', 'alignItems': 'stretch', 'height': '480px'}),

    # 隐藏的存储组件
    dcc.Store(id='current-selected-date', data=datetime.now().strftime("%Y-%m-%d")),
    dcc.Store(id='all-data', data={}),
    # 新增定时器组件，每10分钟刷新一次（600,000毫秒）
    dcc.Interval(id='clock-refresh', interval=600000, n_intervals=0),
    
    # 状态栏
    html.Div([
        html.Span("当前选中日期：", id='current-date-display'),
        html.Span(" | "),
        html.Span("数据文件数量：", id='data-count-display')
    ], style={'textAlign': 'center', 'marginTop': '30px', 'color': '#7f8c8d'}),
    
    # 版权信息
    html.Div([
        html.Span("copyright@github.com/Sigejiao/")
    ], style={'textAlign': 'center', 'marginTop': '10px', 'color': '#7f8c8d'})
])

def get_recent_dates(days):
    today = datetime.now().date()
    return [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(days))]

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
    
    # 获取最近days天的所有日期
    dates = get_recent_dates(days)
    # 横轴标签只显示月-日
    ticktext = [date[5:] for date in dates]
    
    # 准备图表数据
    fig = go.Figure()
    
    for date in dates:
        events = data_manager.parse_time_events(date) if date in all_data else []
        is_today = date == datetime.now().strftime('%Y-%m-%d')
        now_seconds = None
        if is_today:
            now = datetime.now().strftime('%H:%M:%S')
            h, m, s = map(int, now.split(':'))
            now_seconds = h * 3600 + m * 60 + s
        if not events:
            fig.add_trace(go.Bar(
                x=[date],
                y=[24],
                name="无数据",
                marker_color='#e0e0e0',
                showlegend=False,
                hovertemplate=f"<b>{date}</b><br>暂无数据<extra></extra>"
            ))
        else:
            for i, event in enumerate(events):
                start_h, start_m, start_s = map(int, event['start_time'].split(':'))
                end_h, end_m, end_s = map(int, event['end_time'].split(':'))
                start_sec = start_h * 3600 + start_m * 60 + start_s
                end_sec = end_h * 3600 + end_m * 60 + end_s
                duration = end_sec - start_sec
                # 对当天，未到达的部分用灰色
                if is_today and now_seconds is not None and start_sec < now_seconds < end_sec:
                    # 已用部分
                    used = now_seconds - start_sec
                    if used > 0:
                        fig.add_trace(go.Bar(
                            x=[date],
                            y=[used/3600],
                            name=event['event'],
                            base=start_sec/3600,
                            marker_color=COLOR_LIST[i % len(COLOR_LIST)],
                            showlegend=False,
                            hovertemplate=f"<b>{date}</b><br>" +
                                         f"时间: {event['start_time']} - {now}\n" +
                                         f"事件: {event['event']}<extra></extra>"
                        ))
                    # 未用部分
                    left = end_sec - now_seconds
                    if left > 0:
                        fig.add_trace(go.Bar(
                            x=[date],
                            y=[left/3600],
                            name='未到时间',
                            base=now_seconds/3600,
                            marker_color='#e0e0e0',
                            showlegend=False,
                            hovertemplate=f"<b>{date}</b><br>未到时间<extra></extra>"
                        ))
                    break
                elif is_today and now_seconds is not None and end_sec > now_seconds:
                    # 整段未到时间
                    fig.add_trace(go.Bar(
                        x=[date],
                        y=[duration/3600],
                        name='未到时间',
                        base=start_sec/3600,
                        marker_color='#e0e0e0',
                        showlegend=False,
                        hovertemplate=f"<b>{date}</b><br>未到时间<extra></extra>"
                    ))
                    break
                else:
                    # 已过去的事件
                    fig.add_trace(go.Bar(
                        x=[date],
                        y=[duration/3600],
                        name=event['event'],
                        base=start_sec/3600,
                        marker_color=COLOR_LIST[i % len(COLOR_LIST)],
                        showlegend=False,
                        hovertemplate=f"<b>{date}</b><br>" +
                                     f"时间: {event['start_time']} - {event['end_time']}<br>" +
                                     f"事件: {event['event']}<br>" +
                                     f"时长: {duration/3600:.2f}小时<extra></extra>"
                    ))
            if is_today and now_seconds is not None:
                # 计算当前时间到24:00:00的秒数
                end_of_day_sec = 24 * 3600
                left = end_of_day_sec - now_seconds
                if left > 0:
                    fig.add_trace(go.Bar(
                        x=[date],
                        y=[left/3600],
                        name='未来',
                        base=now_seconds/3600,
                        marker_color='#e0e0e0',
                        showlegend=False,
                        hovertemplate=f"<b>{date}</b><br>未来<extra></extra>"
                    ))
    # 更新布局
    fig.update_layout(
        #title="每日时间分布",
        xaxis_title="日期",
        yaxis_title="时间（小时）",
        yaxis=dict(
            range=[0, 24],
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=True,
            tickvals=[0, 5, 10, 15, 20, 24],      # 手动指定刻度
            ticktext=['0', '5', '10', '15', '20', '24']  # 手动指定标签
        ),
        xaxis=dict(
            type='category',
            categoryorder='category ascending',
            tickangle=0,
            tickmode='array',
            ticktext=ticktext,  # 只显示月-日
            tickvals=dates,
            tickfont=dict(size=10 if len(dates) > 7 else 12),
            showgrid=False, zeroline=False, showline=False, showticklabels=True
        ),
        barmode='stack',
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.02,
        bargroupgap=0.01,
        legend=dict(
            itemclick=False,
            itemdoubleclick=False,
            bgcolor='rgba(0,0,0,0)',  # 透明
            bordercolor='rgba(0,0,0,0)'
        ),
        dragmode=False,
        title_font=dict(size=18, color='#222'),
        font=dict(color='#222', size=12)
    )
    return fig



# 回调函数：更新表盘
@app.callback(
    Output('clock-ring', 'figure'),
    [Input('current-selected-date', 'data'),
     Input('all-data', 'data'),
     Input('clock-refresh', 'n_intervals')]
)
def update_clock_ring(selected_date, all_data, n_intervals):
    """更新表盘环形图"""
    from datetime import datetime, timedelta
    if not selected_date:
        return go.Figure()
    # 重新获取当天数据，保证刷新
    events = data_manager.parse_time_events(selected_date)
    if not events:
        # 无数据时显示纯灰色圆环且不显示图例
        fig = go.Figure(data=[go.Pie(
            labels=['无数据'],
            values=[24],
            marker=dict(colors=['#e0e0e0']),
            hole=0.6,
            textinfo='none',
            sort=False,
            direction='clockwise',
            showlegend=False
        )])
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        return fig
    labels = [event['event'] for event in events]
    values = [event['duration'] for event in events]
    colors = [COLOR_LIST[i % len(COLOR_LIST)] for i in range(len(events))]
    total = sum(values)
    # 判断是否需要“未来”灰色
    now = datetime.now()
    try:
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    except Exception:
        selected_date_obj = now
    day_end = selected_date_obj + timedelta(days=1)
    if now < day_end:
        # 还没到24:00，才画“未来”灰色
        if total < 24:
            labels.append('未来')
            values.append(24 - total)
            colors.append('#e0e0e0')
    # 否则（已经过了24:00），不画“未来”，最后一段事件自动画满
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.6,
        textinfo='none',  # 不在内部显示文字
        textposition='inside',
        sort=False,
        direction='clockwise'
    )])
    fig.update_layout(
        #title=f"{selected_date} 时间分布",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(
            orientation='v',
            x=0,
            y=0.8,  # 向上调整
            xanchor='left',
            yanchor='middle',
            font=dict(size=12)
        )
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