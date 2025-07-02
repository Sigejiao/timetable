from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QToolTip, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF  # 导入核心常量、定时器、点、矩形
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor  # 导入绘图、颜色、画笔、字体、光标
import math, datetime, json, os  # 导入数学和日期时间模块、json模块、os模块

class ClockWindow(QWidget):  # 定义主窗口类，继承自QWidget
    def __init__(self):  # 构造函数
        super().__init__()  # 调用父类构造
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  # 设置窗口置顶且无边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.resize(260, 280)  # 设置窗口大小，高度从320调整到280
        self.move_to_bottom_right()  # 移动窗口到屏幕右下角
        
        # 颜色列表
        self.event_colors = [
            QColor(93, 88, 79),    # Color 1
            QColor(235, 248, 253), # Color 2
            QColor(177, 206, 228), # Color 3
            QColor(161, 169, 181), # Color 4
            QColor(217, 192, 169), # Color 5
            QColor(173, 192, 213), # Color 6
        ]   
        
        self.hover_segment = None  # 鼠标悬停的时段
        self.dragging = False  # 是否正在拖动
        self.drag_position = QPoint()  # 拖动起始位置
        
        self.data_dir = "time_data"  # 数据文件夹
        os.makedirs(self.data_dir, exist_ok=True)
        self.today = datetime.date.today().isoformat()
        self.anchors = []  # [{"time": "08:00:00", "event": "未命名"}, ...]
        self.start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
        self.load_anchors()
        
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
            
            # 绘制历史圆环段
            self.draw_segments(painter, center, radius)
            
            # 画时钟指针
            now = datetime.datetime.now()
            self.draw_clock_hands(painter, center, radius, now.hour, now.minute, now.second)
            
            # 显示悬停标签
            # if self.hover_segment is not None:
            #     self.show_hover_tooltip(painter)
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
            self.draw_arc_segment(painter, center, radius, start, end, color)

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
        if event.buttons() == Qt.LeftButton and self.dragging:  # 左键按下且正在拖动
            self.move(event.globalPos() - self.drag_position)  # 移动窗口
            event.accept()  # 接受事件
        else:
            # 检测鼠标是否在圆环上
            # center = QPoint(self.width()//2, 130)
            # radius = 90
            
            # mouse_pos = event.pos()
            # distance = math.sqrt((mouse_pos.x() - center.x())**2 + (mouse_pos.y() - center.y())**2)
            
            # 检测内圆环（上午）
            # if radius - 15 <= distance <= radius + 15:
            #     # 计算鼠标角度，转换为与圆环一致的角度系统
            #     angle = math.degrees(math.atan2(mouse_pos.y() - center.y(), mouse_pos.x() - center.x()))
            #     angle = (angle + 90) % 360  # 转换为12点方向为0度
            #     self.hover_segment = self.find_segment_at_angle(angle, "inner")
            # # 检测外圆环（下午）
            # elif radius + 5 <= distance <= radius + 25:
            #     # 计算鼠标角度，转换为与圆环一致的角度系统
            #     angle = math.degrees(math.atan2(mouse_pos.y() - center.y(), mouse_pos.x() - center.x()))
            #     angle = (angle + 90) % 360  # 转换为12点方向为0度
            #     self.hover_segment = self.find_segment_at_angle(angle, "outer")
            # else:
            #     self.hover_segment = None
            
            # self.update()
            pass

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

    def mouseReleaseEvent(self, event):  # 鼠标释放事件
        if event.button() == Qt.LeftButton:  # 左键释放
            self.dragging = False  # 停止拖动
            event.accept()  # 接受事件

    def enterEvent(self, event):  # 鼠标进入事件
        self.update()  # 刷新界面

    def leaveEvent(self, event):  # 鼠标离开事件
        self.hover_segment = None
        self.update()  # 刷新界面 