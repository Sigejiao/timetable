from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QToolTip, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF  # 导入核心常量、定时器、点、矩形
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor  # 导入绘图、颜色、画笔、字体、光标
import math, datetime, json, os  # 导入数学和日期时间模块、json模块、os模块

class ClockWindow(QWidget):  # 定义主窗口类，继承自QWidget
    def __init__(self):  # 构造函数
        super().__init__()  # 调用父类构造
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  # 设置窗口置顶且无边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setMouseTracking(True)  # 启用鼠标跟踪，确保能接收到鼠标移动事件
        self.resize(260, 280)  # 设置窗口大小，高度从320调整到280
        self.move_to_bottom_right()  # 移动窗口到屏幕右下角
        
        # 颜色列表
        
        self.event_colors = [
            QColor(247, 236, 181),  # Color 1 柔沙
            QColor(228, 192, 126),  # Color 2 小麦
            QColor(196, 154, 103),  # Color 3 暖驼
            QColor(183, 139,  58),  # Color 4 卡其
            QColor(166,  92,  42),  # Color 5 棕褐
            QColor(218,  58,  27),  # Color 6 深朱
            QColor(255,  79,   0),  # Color 7 朱红
            QColor(255, 140,  26),  # Color 8 橙黄
            QColor(255, 184,   0),  # Color 9 琥珀
            QColor(196, 211,  19),  # Color 10 黄绿
            QColor(153, 216,  75),  # Color 11 青柠
            QColor( 64, 222,  90),  # Color 12 草绿
            QColor(  0, 193, 127),  # Color 13 翠绿
            QColor(  0, 179, 164),  # Color 14 青石
            QColor(  0, 227, 201),  # Color 15 浅碧
            QColor( 76, 207, 255),  # Color 16 天蓝
            QColor(106, 143, 255),  # Color 17 薄荷蓝
            QColor(155,  76, 255),  # Color 18 淡紫
            QColor(222,  26, 173),  # Color 19 品红
            QColor(255,  76, 143),  # Color 20 玫瑰
        ]

        

        self.dragging = False  # 是否正在拖动
        self.drag_position = QPoint()  # 拖动起始位置
        
        self.data_dir = "time_data"  # 数据文件夹
        os.makedirs(self.data_dir, exist_ok=True)
        self.today = datetime.date.today().isoformat()
        self.anchors = []  # [{"time": "08:00:00", "event": "未命名"}, ...]
        self.start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
        self.load_anchors()
        
        self.ring_width_ratio = 0.15  # 圆环宽度为表盘半径的比例
        self.hover_info = None  # 当前悬停的事件信息
        
        self.init_ui()  # 初始化界面
        self.timer = QTimer(self)  # 创建定时器
        self.timer.timeout.connect(self.update)  # 定时器超时后刷新界面
        self.timer.start(1000)  # 每秒刷新一次

    def get_today_file(self):
        return os.path.join(self.data_dir, f"timedata_{self.today}.json")

    def load_anchors(self):
        path = self.get_today_file()
        self.anchors = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.anchors = json.load(f)
        if not self.anchors:
            # 新的一天，插入第一个锚点
            self.anchors.append({"time": self.start_of_day.strftime("%H:%M:%S"), "event": "未命名"})
            self.save_anchors()

    def save_anchors(self):
        path = self.get_today_file()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.anchors, f, ensure_ascii=False, indent=2)

    def move_to_bottom_right(self):  # 移动窗口到屏幕右下角
        screen = QApplication.primaryScreen()  # 获取主屏幕
        if screen:
            geometry = screen.geometry()  # 获取屏幕几何信息
            self.move(geometry.width() - self.width() - 20, geometry.height() - self.height() - 40)  # 计算并移动

    def init_ui(self):  # 初始化界面控件
        layout = QVBoxLayout(self)  # 创建垂直布局
        layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        self.input = QLineEdit(self)  # 创建文本输入框
        self.input.setPlaceholderText("输入事件名称...")  # 设置占位提示
        self.input.returnPressed.connect(self.on_enter)  # 回车时调用on_enter
        # 设置输入框不拦截鼠标事件，让父窗口能接收到鼠标事件
        self.input.setMouseTracking(True)
        # 重写输入框的鼠标事件，让它们传递给父窗口
        self.input.mouseMoveEvent = lambda a0: self.mouseMoveEvent(a0)
        layout.addStretch()  # 添加弹性空间
        layout.addWidget(self.input)  # 添加输入框到布局
        self.setLayout(layout)  # 应用布局

    def on_enter(self):  # 输入框回车事件
        try:
            event_name = self.input.text().strip()
            if event_name:
                now = datetime.datetime.now().strftime("%H:%M:%S")
                self.anchors.append({"time": now, "event": event_name})
                self.save_anchors()
                self.input.clear()
                self.update()
        except Exception as e:
            print(f"Error in on_enter: {e}")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制窗口背景
            painter.setBrush(QColor(240, 240, 240, 128))
            painter.setPen(QPen(QColor(200, 200, 200, 128), 1))
            painter.drawRoundedRect(self.rect(), 10, 10)
            
            # 自适应表盘中心和半径
            center = QPoint(self.width()//2, (self.height() - self.input.height())//2)
            radius = int(min(self.width(), self.height() - self.input.height()) * 0.35)
            
            # 画底色圆（完全不透明）
            painter.setBrush(QColor(255, 255, 224))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            
            # 绘制表盘刻度
            painter.setPen(QPen(QColor(130, 130, 130, 128), 2))
            for i in range(60):
                angle = math.radians(i * 6)
                if i % 5 == 0:
                    line_len = int(radius * 0.17)
                else:
                    line_len = int(radius * 0.09)
                x1 = center.x() + (radius - line_len) * math.cos(angle - math.pi/2)
                y1 = center.y() + (radius - line_len) * math.sin(angle - math.pi/2)
                x2 = center.x() + radius * math.cos(angle - math.pi/2)
                y2 = center.y() + radius * math.sin(angle - math.pi/2)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # 画右上角X符号
            x_size = int(self.width() * 0.07)
            margin = int(self.width() * 0.03)
            x_center_x = self.width() - margin - x_size // 2
            x_center_y = margin + x_size // 2
            painter.setPen(QPen(QColor(50, 50, 50, 200), max(2, x_size // 7)))
            painter.drawLine(x_center_x - x_size//2, x_center_y - x_size//2, x_center_x + x_size//2, x_center_y + x_size//2)
            painter.drawLine(x_center_x + x_size//2, x_center_y - x_size//2, x_center_x - x_size//2, x_center_y + x_size//2)
            
            # 计算圆环宽度（表盘半径的0.1倍）
            self.draw_ring_width = int(radius * self.ring_width_ratio)
            # 绘制历史圆环段
            self.draw_segments(painter, center, radius)
            
            # 画时钟指针
            now = datetime.datetime.now()
            self.draw_clock_hands(painter, center, radius, now.hour, now.minute, now.second)
            
            # 绘制悬停标签
            if self.hover_info:
                # 获取当前鼠标位置
                mouse_pos = self.mapFromGlobal(self.cursor().pos())
                self.draw_hover_tooltip(painter, mouse_pos, self.hover_info)
            

        except Exception as e:
            print(f"Error in paintEvent: {e}")
            import traceback
            traceback.print_exc()

    def draw_segments(self, painter, center, radius):
        if not self.anchors:
            return
        now = datetime.datetime.now()
        # 组装所有锚点的时间
        points = []
        for anchor in self.anchors:
            t = datetime.datetime.strptime(anchor["time"], "%H:%M:%S").time()
            dt = datetime.datetime.combine(now.date(), t)
            points.append(dt)
        points.append(now)  # 最后一段到当前时间
        # 绘制分段
        for i in range(len(points)-1):
            start = points[i]
            end = points[i+1]
            event_name = self.anchors[i]["event"]
            color = self.event_colors[i % len(self.event_colors)]
            self.draw_arc_segment_cross_ring(painter, center, radius, start, end, color)

    def draw_arc_segment(self, painter, center, radius, start, end, color):
        # 以start_of_day为0度，顺时针
        def time_to_angle(dt):
            seconds = (dt - self.start_of_day).total_seconds()
            angle = (seconds / 43200) * 360  # 12小时一圈
            return angle
        start_angle = time_to_angle(start)
        end_angle = time_to_angle(end)
        span = (end_angle - start_angle) % 360
        start_angle_qt = int((90 - start_angle) * 16)
        span_angle_qt = int(-span * 16)
        painter.setPen(QPen(color, max(6, radius//10)))
        painter.drawArc(QRectF(center.x()-radius, center.y()-radius, 2*radius, 2*radius), start_angle_qt, span_angle_qt)

    def draw_arc_segment_cross_ring(self, painter, center, radius, start, end, color):
        """绘制跨环的时间段（上午画内环，下午画外环）"""
        # 计算当天的中午12点（注意：noon的日期与start一致，若start跨天可能导致问题）
        noon = datetime.datetime.combine(start.date(), datetime.time(12, 0, 0))
        # 使用统一管理的宽度参数
        # 内环内界贴合表盘外界，外环内界贴合内环外界
        inner_radius = radius + self.draw_ring_width//2  # 内环半径：表盘半径 + 圆环宽度的一半
        outer_radius = radius + self.draw_ring_width + self.draw_ring_width//2  # 外环半径：表盘半径 + 圆环宽度 + 圆环宽度的一半
        # print(f"[cross_ring] 调用: start={start}, end={end}, noon={noon}")
        if start < noon and end > noon:
            # print(f"[cross_ring] 跨中午: {start} ~ {noon} (内环), {noon} ~ {end} (外环)")
            # 内环只画到11:59:59，避免span=0
            self.draw_arc_segment_part(painter, center, inner_radius, start, noon - datetime.timedelta(seconds=1), color)
            self.draw_arc_segment_part(painter, center, outer_radius, noon, end, color)
        elif start >= noon:
            # print(f"[cross_ring] 全部下午: {start} ~ {end} (外环)")
            self.draw_arc_segment_part(painter, center, outer_radius, start, end, color)
        else:
            # print(f"[cross_ring] 全部上午: {start} ~ {end} (内环)")
            self.draw_arc_segment_part(painter, center, inner_radius, start, end, color)

    def draw_arc_segment_part(self, painter, center, ring_radius, start, end, color):
        """绘制单个环上的时间段"""
        def time_to_angle(dt):
            seconds = (dt - self.start_of_day).total_seconds()
            angle = (seconds / 43200) * 360
            return angle
        start_angle = time_to_angle(start)
        end_angle = time_to_angle(end)
        span = (end_angle - start_angle) % 360
        if span == 0 and start != end:
            span = 360  # 画整圈
        start_angle_qt = int((90 - start_angle) * 16)
        span_angle_qt = int(-span * 16)
        # print(f"[part] 调用: ring_radius={ring_radius}, start={start}, end={end}, start_angle={start_angle}, end_angle={end_angle}, span={span}")
        painter.setPen(QPen(color, self.draw_ring_width))  # 使用统一管理的宽度
        painter.drawArc(
            QRectF(center.x()-ring_radius, center.y()-ring_radius, 2*ring_radius, 2*ring_radius),
            start_angle_qt, span_angle_qt
        )

    def draw_clock_hands(self, painter, center, radius, hour, minute, second):
        try:
            # 时针
            painter.save()
            painter.setPen(QPen(QColor(0,0,0), 4))
            angle = (hour % 12 + minute/60) * 30
            self.draw_hand(painter, center, radius*0.6, angle)
            painter.restore()
            
            # 分针
            painter.save()
            painter.setPen(QPen(QColor(0,0,0), 2))
            angle = (minute + second/60) * 6
            self.draw_hand(painter, center, radius*0.8, angle)
            painter.restore()
            
            # 秒针
            painter.save()
            painter.setPen(QPen(QColor(255,0,0), 1))
            angle = second * 6
            self.draw_hand(painter, center, radius*0.9, angle)
            painter.restore()
            
            # 绘制中心点
            painter.setBrush(QColor(0,0,0))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, 3, 3)
        except Exception as e:
            print(f"Error in draw_clock_hands: {e}")
            import traceback
            traceback.print_exc()

    def draw_hand(self, painter, center, length, angle):
        try:
            
            rad = math.radians(90 - angle)
            end_x = center.x() + length * math.cos(rad)
            end_y = center.y() - length * math.sin(rad)
            end = QPoint(int(end_x), int(end_y))
            painter.drawLine(center, end)
        except Exception as e:
            print(f"Error in draw_hand: {e}")
            import traceback
            traceback.print_exc()

    def mousePressEvent(self, event):  # 鼠标按下事件
        if event.button() == Qt.LeftButton:  # 左键按下
            # 检查是否点击了右上角X
            x_size = int(self.width() * 0.07)
            margin = int(self.width() * 0.03)
            x_left = self.width() - margin - x_size
            x_top = margin
            x_rect = QRectF(x_left, x_top, x_size, x_size)
            if x_rect.contains(event.pos()):
                QApplication.quit()
                return
            self.dragging = True  # 开始拖动
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()  # 记录拖动起始位置
            event.accept()  # 接受事件

    def mouseMoveEvent(self, event):  # 鼠标移动事件
        # print(f"[鼠标移动] 事件被调用 - 位置:({event.pos().x()},{event.pos().y()}), 按钮状态:{event.buttons()}, 拖动状态:{self.dragging}")
        
        if event.buttons() == Qt.LeftButton and self.dragging:  # 左键按下且正在拖动
            self.move(event.globalPos() - self.drag_position)  # 移动窗口
            event.accept()  # 接受事件
        else:
            # print("进入位置检测模块")
            # 悬停检测：鼠标没有按下时检测圆环区域
            if not event.buttons():
                # 计算圆环参数
                center_x = self.width() // 2
                center_y = (self.height() - self.input.height()) // 2
                radius = int(min(self.width(), self.height() - self.input.height()) * 0.35)
                
                # 计算鼠标到圆环中心的距离
                mouse_x = event.pos().x()
                mouse_y = event.pos().y()
                distance = math.sqrt((mouse_x - center_x)**2 + (mouse_y - center_y)**2)
                
                # 计算圆环宽度（表盘半径的0.1倍）
                ring_width = int(radius * self.ring_width_ratio)  # 与绘制部分保持一致
                # 内环内界贴合表盘外界，外环内界贴合内环外界
                inner_radius = radius + ring_width//2  # 内环半径：表盘半径 + 圆环宽度的一半
                outer_radius = radius + ring_width + ring_width//2  # 外环半径：表盘半径 + 圆环宽度 + 圆环宽度的一半
                
                # 检测鼠标位置
                # 内环区域：从表盘外界(radius)到内环外界(inner_radius + ring_width//2)
                inner_ring_outer = inner_radius + ring_width//2
                # 外环区域：从内环外界到外环外界(outer_radius + ring_width//2)
                outer_ring_outer = outer_radius + ring_width//2
                
                if distance < radius - 5:
                    print(f"[悬停检测] 鼠标在表盘内部 - 位置:({mouse_x},{mouse_y}), 距离:{distance:.1f}, 表盘半径:{radius}")
                elif radius - 2 <= distance <= inner_ring_outer + 2:
                    print(f"[悬停检测] 鼠标在内环区域 - 位置:({mouse_x},{mouse_y}), 距离:{distance:.1f}, 内环范围:{radius}-{inner_ring_outer}")
                    # 在内环区域时，计算角度和时间（上午时间）
                    angle = self.mouse_pos_to_angle(mouse_x, mouse_y, center_x, center_y)
                    time_str = self.angle_to_time(angle)
                    print(f"[角度计算] 内环角度:{angle:.1f}°, 对应上午时间:{time_str}")
                    
                    # 查找对应事件并更新悬停信息
                    target_time = datetime.datetime.strptime(time_str, "%H:%M:%S")
                    self.hover_info = self.find_event_at_time(target_time)
                    self.update()  # 触发重绘
                elif inner_ring_outer + 2 < distance <= outer_ring_outer + 2:
                    print(f"[悬停检测] 鼠标在外环区域 - 位置:({mouse_x},{mouse_y}), 距离:{distance:.1f}, 外环范围:{inner_ring_outer}-{outer_ring_outer}")
                    # 在外环区域时，计算角度和时间（下午时间，+12小时）
                    angle = self.mouse_pos_to_angle(mouse_x, mouse_y, center_x, center_y)
                    time_str = self.angle_to_time_afternoon(angle)
                    print(f"[角度计算] 外环角度:{angle:.1f}°, 对应下午时间:{time_str}")
                    
                    # 查找对应事件并更新悬停信息
                    target_time = datetime.datetime.strptime(time_str, "%H:%M:%S")
                    self.hover_info = self.find_event_at_time(target_time)
                    self.update()  # 触发重绘
                else:
                    print(f"[悬停检测] 鼠标超出检测范围 - 位置:({mouse_x},{mouse_y}), 距离:{distance:.1f}, 检测上限:{outer_ring_outer+2}")
                    # 清空悬停信息
                    if self.hover_info is not None:
                        self.hover_info = None
                        self.update()  # 触发重绘

    # def find_segment_at_angle(self, angle, ring_type):
    #     """根据角度和圆环类型找到对应的时段"""
    #     # 检查历史时段
    #     for i, (start_time, end_time, event_name, color) in enumerate(self.time_segments):
    #         if self.get_ring_info(start_time) == ring_type:
    #             start_angle = self.time_to_angle(start_time)
    #             end_angle = self.time_to_angle(end_time)
    #             
    #             # 处理跨越0度的情况
    #             if end_angle < start_angle:
    #                 if angle >= start_angle or angle <= end_angle:
    #                     return i
    #             else:
    #                 if start_angle <= angle <= end_angle:
    #                     return i
    #         
    #         # 检查当前时段
    #         if self.current_segment_start is not None:
    #             if self.get_ring_info(self.current_segment_start) == ring_type:
    #                 start_angle = self.time_to_angle(self.current_segment_start)
    #                 now = datetime.datetime.now()
    #                 current_angle = self.time_to_angle(now)
    #                 
    #                 if current_angle < start_angle:
    #                     if angle >= start_angle or angle <= current_angle:
    #                         return len(self.time_segments)
    #                 else:
    #                     if start_angle <= angle <= current_angle:
    #                         return len(self.time_segments)
    #         
    #         return None

    def draw_hover_tooltip(self, painter, mouse_pos, event_info):
        """绘制悬停标签"""
        if not event_info:
            return
            
        # 设置字体
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        
        # 准备文本内容
        time_text = f"{event_info['start_time']} - {event_info['end_time']}"
        event_text = event_info['event_name']
        
        # 计算文本尺寸
        time_rect = painter.fontMetrics().boundingRect(time_text)
        event_rect = painter.fontMetrics().boundingRect(event_text)
        
        # 计算标签位置（避免遮挡鼠标）
        offset_x = 15
        offset_y = -15
        label_x = mouse_pos.x() + offset_x
        label_y = mouse_pos.y() + offset_y
        
        # 边界检测，确保标签不超出窗口
        max_text_width = max(time_rect.width(), event_rect.width())
        if label_x + max_text_width > self.width():
            label_x = mouse_pos.x() - max_text_width - offset_x
        
        # 修改下边界检测：当鼠标比表盘圆心低时，标签向上偏移
        center_y = (self.height() - self.input.height()) // 2  # 表盘圆心Y坐标
        if mouse_pos.y() > center_y:
            label_y = mouse_pos.y() - (time_rect.height() + event_rect.height() + 8) - offset_y
        
        if label_y < 0:
            label_y = mouse_pos.y() + offset_y
        
        # 判断标签在鼠标左侧还是右侧，设置对齐方式
        if label_x < mouse_pos.x():
            # 标签在鼠标左侧，右对齐
            time_x = label_x + max_text_width - time_rect.width()
            event_x = label_x + max_text_width - event_rect.width()
        else:
            # 标签在鼠标右侧，左对齐
            time_x = label_x
            event_x = label_x

        # 绘制文本
        painter.setPen(QColor(50, 50, 50))
        time_y = label_y + time_rect.height()
        painter.drawText(time_x, time_y, time_text)
        # 下划线严格跟随文字宽度
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.drawLine(time_x, time_y + 2, time_x + time_rect.width(), time_y + 2)

        event_y = time_y + event_rect.height() + 4
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(event_x, event_y, event_text)
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.drawLine(event_x, event_y + 2, event_x + event_rect.width(), event_y + 2)

    def mouseReleaseEvent(self, event):  # 鼠标释放事件
        if event.button() == Qt.LeftButton:  # 左键释放
            self.dragging = False  # 停止拖动
            event.accept()  # 接受事件

    def enterEvent(self, event):  # 鼠标进入事件
        self.update()  # 刷新界面



    def leaveEvent(self, event):  # 鼠标离开事件
        self.update()  # 刷新界面

    def mouse_pos_to_angle(self, mouse_x, mouse_y, center_x, center_y):
        """将鼠标位置转换为角度（0-360度）"""
        # 计算相对于圆心的角度
        dx = mouse_x - center_x
        dy = mouse_y - center_y
        angle = math.degrees(math.atan2(-dy, -dx))  # 负dy和负dx实现水平翻转
        return (angle + 270) % 360  # 调整到12点方向为0度，旋转180度

    def angle_to_time(self, angle):
        """将角度转换为时间字符串（上午时间）"""
        # 12小时制映射：0度=00:00, 90度=06:00, 180度=12:00, 270度=18:00
        seconds = int((angle / 360) * 43200)  # 12小时=43200秒
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}:00"

    def angle_to_time_afternoon(self, angle):
        """将角度转换为时间字符串（下午时间，+12小时）"""
        # 12小时制映射：0度=12:00, 90度=18:00, 180度=00:00, 270度=06:00
        seconds = int((angle / 360) * 43200)  # 12小时=43200秒
        hours = (seconds // 3600 + 12) % 24  # 加12小时并确保在24小时内
        minutes = (seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}:00"

    def find_event_at_time(self, target_time):
        """根据时间点查找对应的事件信息"""
        if not self.anchors:
            return None
            
        # 将target_time转换为time对象进行比较
        target_time_obj = target_time.time() if hasattr(target_time, 'time') else target_time
        
        # 遍历anchors查找对应时间段
        for i in range(len(self.anchors)):
            start_time_str = self.anchors[i]["time"]
            start_time_obj = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
            
            # 确定结束时间
            if i + 1 < len(self.anchors):
                end_time_str = self.anchors[i + 1]["time"]
                end_time_obj = datetime.datetime.strptime(end_time_str, "%H:%M:%S").time()
            else:
                # 最后一个时间段到当前时间
                end_time_obj = datetime.datetime.now().time()
            
            # 判断target_time是否在这个时间段内
            if start_time_obj <= target_time_obj < end_time_obj:
                return {
                    "start_time": start_time_str,
                    "end_time": end_time_str if i + 1 < len(self.anchors) else datetime.datetime.now().strftime("%H:%M:%S"),
                    "event_name": self.anchors[i]["event"],
                    "color_index": i % len(self.event_colors)
                }
        
        # 如果target_time在第一个锚点之前
        if self.anchors and target_time_obj < datetime.datetime.strptime(self.anchors[0]["time"], "%H:%M:%S").time():
            return {
                "start_time": "00:00:00",
                "end_time": self.anchors[0]["time"],
                "event_name": "未定义时间段",
                "color_index": 0
            }
        
        return None 