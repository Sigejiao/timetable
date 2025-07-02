from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QToolTip, QApplication, QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QProcess
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QCursor, QPixmap
import math, datetime, json, os, bisect, subprocess, sys

class ClockWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 窗口配置
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize(260, 280)
        self.move_to_bottom_right()

        # 恢复原来的20种颜色
        self.event_colors = [
            # 从绿色开始，沿色相环渐变
            QColor( 64, 222,  90),  # Color 1 草绿
            QColor(  0, 193, 127),  # Color 2 翠绿
            QColor(  0, 179, 164),  # Color 3 青石
            QColor(  0, 227, 201),  # Color 4 浅碧
            QColor( 76, 187, 255),  # Color 5 天蓝
            QColor(106, 143, 255),  # Color 6 薄荷蓝
            QColor(155,  76, 255),  # Color 7 淡紫
            QColor(222,  26, 173),  # Color 8 品红
            QColor(255,  76, 143),  # Color 9 玫瑰
            QColor(247, 236, 181),  # Color 10 柔沙
            QColor(228, 192, 126),  # Color 11 小麦
            QColor(196, 154, 103),  # Color 12 暖驼
            QColor(183, 139,  58),  # Color 13 卡其
            QColor(166,  92,  42),  # Color 14 棕褐
            QColor(218,  58,  27),  # Color 15 深朱
            QColor(255,  79,   0),  # Color 16 朱红
            QColor(255, 140,  26),  # Color 17 橙黄
            QColor(255, 184,   0),  # Color 18 琥珀
            QColor(196, 211,  19),  # Color 19 黄绿
            QColor(153, 216,  75),  # Color 20 青柠
        ]

        # 拖拽支持
        self.dragging = False
        self.drag_position = QPoint()

        # 数据目录与今天
        self.data_dir = "time_data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.today = datetime.date.today().isoformat()
        self.start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
        self.anchors = []

        # 预计算数据
        self.anchor_seconds = []
        self.anchor_events = []
        self._anchor_segments = []

        # 静态缓存标志与画布
        self._static_pixmap = None
        self._need_static_update = True

        # 预计算几何 + 画笔
        self._tick_coords = []
        self._center = QPoint()
        self._radius = 0
        self._ring_width = 0
        self.ring_width_ratio = 0.15
        self._pens = {
            'tick': QPen(QColor(130, 130, 130, 128), 2),
            'hour_hand': QPen(QColor(0, 0, 0), 4),
            'minute_hand': QPen(QColor(0, 0, 0), 2),
            'second_hand': QPen(QColor(255, 0, 0), 1),
            'button': QPen(QColor(50, 50, 50, 200), 2),
        }

        # 悬停标签
        self.hover_label = QLabel(self)
        self.hover_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.hover_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 让标签对鼠标透明
        self.hover_label.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 8px;
                color: #333333;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                font-weight: 500;
            }
            """
        )
        self.hover_label.hide()
        self.last_mouse_pos = None
        self.last_hover_text = ""

        # 悬停节流定时器
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._do_hover_detection)
        
        # 全局检测定时器（200ms轮询）
        self.global_hover_timer = QTimer(self)
        self.global_hover_timer.timeout.connect(self._check_hover_state)
        self.global_hover_timer.start(200)

        # 加载锚点与初始化UI
        self.load_anchors()
        self.init_ui()

        # 指针定时重绘
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("输入事件名称...")
        self.input.returnPressed.connect(self.on_enter)
        # 设置输入框不拦截鼠标事件，让父窗口能接收到鼠标事件
        self.input.setMouseTracking(True)
        # 重写输入框的鼠标事件，让它们传递给父窗口
        self.input.mouseMoveEvent = lambda a0: self.mouseMoveEvent(a0)
        layout.addStretch()
        layout.addWidget(self.input)
        self.setLayout(layout)

        self._compute_geometry()
        self._render_static()

    def move_to_bottom_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.move(geometry.width() - self.width() - 20, geometry.height() - self.height() - 40)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._need_static_update = True
        self._compute_geometry()
        self._render_static()

    def _compute_geometry(self):
        self._center = QPoint(self.width()//2, (self.height() - self.input.height())//2)
        self._radius = int(min(self.width(), self.height() - self.input.height()) * 0.35)
        self._ring_width = int(self._radius * self.ring_width_ratio)
        
        # 预计算刻度坐标
        self._tick_coords = []
        for i in range(60):
            angle = math.radians(i * 6)
            if i % 5 == 0:
                line_len = int(self._radius * 0.17)
            else:
                line_len = int(self._radius * 0.09)
            x1 = self._center.x() + (self._radius - line_len) * math.cos(angle - math.pi/2)
            y1 = self._center.y() + (self._radius - line_len) * math.sin(angle - math.pi/2)
            x2 = self._center.x() + self._radius * math.cos(angle - math.pi/2)
            y2 = self._center.y() + self._radius * math.sin(angle - math.pi/2)
            self._tick_coords.append((int(x1), int(y1), int(x2), int(y2)))

    def load_anchors(self):
        path = self.get_today_file()
        self.anchors = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.anchors = json.load(f)
        if not self.anchors:
            self.anchors.append({"time": self.start_of_day.strftime("%H:%M:%S"), "event": "未命名"})
            self.save_anchors()
        self.precompute_anchor_data()

    def save_anchors(self):
        path = self.get_today_file()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.anchors, f, ensure_ascii=False, indent=2)

    def get_today_file(self):
        return os.path.join(self.data_dir, f"timedata_{self.today}.json")

    def precompute_anchor_data(self):
        """预计算锚点数据和环段几何"""
        self.anchor_seconds = []
        self.anchor_events = []
        self._anchor_segments = []
        
        for i, anchor in enumerate(self.anchors):
            h, m, s = map(int, anchor["time"].split(':'))
            seconds = h * 3600 + m * 60 + s
            self.anchor_seconds.append(seconds)
            
            start_time = anchor["time"]
            if i + 1 < len(self.anchors):
                end_time = self.anchors[i + 1]["time"]
            else:
                end_time = datetime.datetime.now().strftime("%H:%M:%S")
            
            self.anchor_events.append({
                "start_time": start_time,
                "end_time": end_time,
                "event_name": anchor["event"],
                "color_index": i % len(self.event_colors)
            })
            
            # 预计算环段几何数据
            if i + 1 < len(self.anchors):
                # 历史环段（静态）
                start_dt = datetime.datetime.strptime(start_time, "%H:%M:%S")
                end_dt = datetime.datetime.strptime(end_time, "%H:%M:%S")
                self._anchor_segments.append({
                    'start': start_dt,
                    'end': end_dt,
                    'color': self.event_colors[i % len(self.event_colors)],
                    'is_current': False
                })
        
        # 标记需要更新静态内容
        self._need_static_update = True

    def _render_static(self):
        """渲染静态内容到QPixmap缓存"""
        if not self._need_static_update:
            return
            
        self._static_pixmap = QPixmap(self.size())
        self._static_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self._static_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制窗口背景
        painter.setBrush(QColor(240, 240, 240, 128))
        painter.setPen(QPen(QColor(200, 200, 200, 128), 1))
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        # 画底色圆
        painter.setBrush(QColor(255, 255, 224))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self._center, self._radius, self._radius)
        
        # 绘制表盘刻度
        painter.setPen(self._pens['tick'])
        for x1, y1, x2, y2 in self._tick_coords:
            painter.drawLine(x1, y1, x2, y2)
        
        # 画右上角按钮区域
        button_size = int(self.width() * 0.07)
        margin = int(self.width() * 0.03)
        
        # 画☰按钮（在X左侧）
        menu_center_x = self.width() - margin - button_size - button_size - 5  # X左侧留5px间距
        menu_center_y = margin + button_size // 2
        painter.setPen(self._pens['button'])
        
        # 绘制☰符号（三条横线）
        line_length = button_size // 2
        line_spacing = button_size // 6
        
        # 第一条线
        painter.drawLine(
            menu_center_x - line_length//2, 
            menu_center_y - line_spacing, 
            menu_center_x + line_length//2, 
            menu_center_y - line_spacing
        )
        # 第二条线
        painter.drawLine(
            menu_center_x - line_length//2, 
            menu_center_y, 
            menu_center_x + line_length//2, 
            menu_center_y
        )
        # 第三条线
        painter.drawLine(
            menu_center_x - line_length//2, 
            menu_center_y + line_spacing, 
            menu_center_x + line_length//2, 
            menu_center_y + line_spacing
        )
        
        # 画X按钮
        x_center_x = self.width() - margin - button_size // 2
        x_center_y = margin + button_size // 2
        painter.drawLine(x_center_x - button_size//2, x_center_y - button_size//2, 
                        x_center_x + button_size//2, x_center_y + button_size//2)
        painter.drawLine(x_center_x + button_size//2, x_center_y - button_size//2, 
                        x_center_x - button_size//2, x_center_y + button_size//2)
        
        # 绘制历史环段（静态部分）
        self._draw_static_segments(painter)
        
        painter.end()
        self._need_static_update = False

    def _draw_static_segments(self, painter):
        """绘制静态的历史环段"""
        if not self._anchor_segments:
            return
            
        for segment in self._anchor_segments:
            if segment['end'] <= datetime.datetime.now():
                # 只绘制已完成的历史环段
                self._draw_single_segment(painter, segment['start'], segment['end'], segment['color'])

    def _draw_single_segment(self, painter, start, end, color):
        """绘制单个环段"""
        # 计算当天的中午12点
        noon = datetime.datetime.combine(start.date(), datetime.time(12, 0, 0))
        
        # 环半径
        inner_radius = self._radius + self._ring_width//2
        outer_radius = self._radius + self._ring_width + self._ring_width//2
        
        if start < noon and end > noon:
            # 跨中午的情况
            self._draw_arc_part(painter, inner_radius, start, noon - datetime.timedelta(seconds=1), color)
            self._draw_arc_part(painter, outer_radius, noon, end, color)
        elif start >= noon:
            # 全部下午
            self._draw_arc_part(painter, outer_radius, start, end, color)
        else:
            # 全部上午
            self._draw_arc_part(painter, inner_radius, start, end, color)

    def _draw_arc_part(self, painter, ring_radius, start, end, color):
        """绘制单个环上的弧段"""
        def time_to_angle(dt):
            seconds = (dt - self.start_of_day).total_seconds()
            angle = (seconds / 43200) * 360
            return angle
            
        start_angle = time_to_angle(start)
        end_angle = time_to_angle(end)
        span = (end_angle - start_angle) % 360
        if span == 0 and start != end:
            span = 360
            
        start_angle_qt = int((90 - start_angle) * 16)
        span_angle_qt = int(-span * 16)
        
        painter.setPen(QPen(color, self._ring_width))
        painter.drawArc(
            QRectF(self._center.x()-ring_radius, self._center.y()-ring_radius, 
                   2*ring_radius, 2*ring_radius),
            start_angle_qt, span_angle_qt
        )

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 1. 绘制静态缓存内容
            if self._static_pixmap:
                painter.drawPixmap(0, 0, self._static_pixmap)
            
            # 2. 绘制动态内容：当前时间段（如果存在）
            self._draw_current_segment(painter)
            
            # 3. 绘制时钟指针
            now = datetime.datetime.now()
            self._draw_clock_hands(painter, now.hour, now.minute, now.second)

        except Exception as e:
            print(f"Error in paintEvent: {e}")
            import traceback
            traceback.print_exc()

    def _draw_current_segment(self, painter):
        """绘制当前进行中的时间段（动态）"""
        if not self.anchors:
            return
            
        # 找到当前时间段
        now = datetime.datetime.now()
        current_time = now.time()
        
        for i, anchor in enumerate(self.anchors):
            start_time = datetime.datetime.strptime(anchor["time"], "%H:%M:%S").time()
            
            if i + 1 < len(self.anchors):
                end_time = datetime.datetime.strptime(self.anchors[i + 1]["time"], "%H:%M:%S").time()
            else:
                # 最后一个时间段到当前时间
                if start_time <= current_time:
                    # 绘制从开始到当前时间的弧段
                    start_dt = datetime.datetime.combine(now.date(), start_time)
                    color = self.event_colors[i % len(self.event_colors)]
                    self._draw_single_segment(painter, start_dt, now, color)
                break

    def _draw_clock_hands(self, painter, hour, minute, second):
        """绘制时钟指针"""
        try:
            # 时针
            painter.save()
            painter.setPen(self._pens['hour_hand'])
            angle = (hour % 12 + minute/60) * 30
            self._draw_hand(painter, self._center, self._radius*0.6, angle)
            painter.restore()
            
            # 分针
            painter.save()
            painter.setPen(self._pens['minute_hand'])
            angle = (minute + second/60) * 6
            self._draw_hand(painter, self._center, self._radius*0.8, angle)
            painter.restore()
            
            # 秒针
            painter.save()
            painter.setPen(self._pens['second_hand'])
            angle = second * 6
            self._draw_hand(painter, self._center, self._radius*0.9, angle)
            painter.restore()
            
            # 绘制中心点
            painter.setBrush(QColor(0,0,0))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self._center, 3, 3)
        except Exception as e:
            print(f"Error in _draw_clock_hands: {e}")

    def _draw_hand(self, painter, center, length, angle):
        """绘制指针"""
        try:
            rad = math.radians(90 - angle)
            end_x = center.x() + length * math.cos(rad)
            end_y = center.y() - length * math.sin(rad)
            end = QPoint(int(end_x), int(end_y))
            painter.drawLine(center, end)
        except Exception as e:
            print(f"Error in _draw_hand: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            button_size = int(self.width() * 0.07)
            margin = int(self.width() * 0.03)
            
            # 检查是否点击了☰按钮
            menu_left = self.width() - margin - button_size - button_size - 5 - button_size//2
            menu_top = margin
            menu_rect = QRectF(menu_left, menu_top, button_size, button_size)
            if menu_rect.contains(event.pos()):
                self.run_time_manage()
                return
            
            # 检查是否点击了X按钮
            x_left = self.width() - margin - button_size
            x_top = margin
            x_rect = QRectF(x_left, x_top, button_size, button_size)
            if x_rect.contains(event.pos()):
                QApplication.quit()
                return
                
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def run_time_manage(self):
        """运行timeManage.py"""
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            time_manage_path = os.path.join(current_dir, "timeManage.py")
            
            # 检查文件是否存在
            if os.path.exists(time_manage_path):
                # 使用subprocess启动timeManage.py
                subprocess.Popen([sys.executable, time_manage_path], 
                               cwd=current_dir,
                               creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                print(f"已启动 timeManage.py: {time_manage_path}")
            else:
                print(f"timeManage.py 文件不存在: {time_manage_path}")
        except Exception as e:
            print(f"启动 timeManage.py 时出错: {e}")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            # 轻量操作：始终跟随鼠标位置
            if not event.buttons():
                pos = event.pos()
                self.last_mouse_pos = pos  # 始终记录最新位置
                
                # 检查是否在圆环区域内
                if self._is_in_ring(pos):
                    # 计算标签位置（避免遮挡鼠标）
                    global_pos = self.mapToGlobal(pos + QPoint(15, -15))
                    self.hover_label.move(global_pos)
                    
                    # 启动内容更新定时器
                    if not self.hover_timer.isActive():
                        self.hover_timer.start(50)  # 缩短到50ms提高响应速度
                else:
                    # 不在圆环区域，立即隐藏标签
                    self.hover_label.hide()
                    self.last_hover_text = ""
                    self.hover_timer.stop()  # 停止定时器

    def _is_in_ring(self, pos):
        """检查鼠标是否在圆环区域内"""
        center_x = self.width() // 2
        center_y = (self.height() - self.input.height()) // 2
        radius = int(min(self.width(), self.height() - self.input.height()) * 0.35)
        
        mouse_x, mouse_y = pos.x(), pos.y()
        distance = math.sqrt((mouse_x - center_x)**2 + (mouse_y - center_y)**2)
        
        ring_width = int(radius * self.ring_width_ratio)
        inner_radius = radius + ring_width//2
        outer_radius = radius + ring_width + ring_width//2
        
        inner_ring_outer = inner_radius + ring_width//2
        outer_ring_outer = outer_radius + ring_width//2
        
        # 放宽检测边界，增加容错范围
        return (radius - 5 <= distance <= inner_ring_outer + 5 or 
                inner_ring_outer - 2 < distance <= outer_ring_outer + 5)

    def _do_hover_detection(self):
        """定时器回调：内容更新（节流）"""
        if not self.last_mouse_pos:
            return
            
        pos = self.last_mouse_pos
        
        # 再次检查是否在环内（双重保险）
        if not self._is_in_ring(pos):
            self.hover_label.hide()
            self.last_hover_text = ""
            return
        
        # 计算角度和时间
        angle = self._calc_angle(pos)
        is_afternoon = self._is_afternoon_ring(pos)
        
        if is_afternoon:
            target_seconds = int((angle / 360) * 43200) + 43200  # 下午时间
        else:
            target_seconds = int((angle / 360) * 43200)  # 上午时间
        
        # 二分查找事件
        event_info = self._find_event_at_seconds(target_seconds)
        
        # 生成标签文本
        new_text = ""
        if event_info:
            new_text = f"{event_info['start_time']} - {event_info['end_time']}\n{event_info['event_name']}"
        
        # 只有内容真正改变时才更新
        if new_text != self.last_hover_text:
            if new_text:
                self.hover_label.setText(new_text)
                self.hover_label.show()
            else:
                self.hover_label.hide()
            self.last_hover_text = new_text

    def _calc_angle(self, pos):
        """计算鼠标位置对应的角度"""
        center_x = self.width() // 2
        center_y = (self.height() - self.input.height()) // 2
        
        dx = pos.x() - center_x
        dy = pos.y() - center_y
        angle = math.degrees(math.atan2(-dy, -dx))
        return (angle + 270) % 360

    def _is_afternoon_ring(self, pos):
        """判断是否在外环（下午时间）"""
        center_x = self.width() // 2
        center_y = (self.height() - self.input.height()) // 2
        radius = int(min(self.width(), self.height() - self.input.height()) * 0.35)
        
        mouse_x, mouse_y = pos.x(), pos.y()
        distance = math.sqrt((mouse_x - center_x)**2 + (mouse_y - center_y)**2)
        
        ring_width = int(radius * self.ring_width_ratio)
        inner_radius = radius + ring_width//2
        outer_radius = radius + ring_width + ring_width//2
        
        inner_ring_outer = inner_radius + ring_width//2
        outer_ring_outer = outer_radius + ring_width//2
        
        return inner_ring_outer + 2 < distance <= outer_ring_outer + 2

    def _find_event_at_seconds(self, target_seconds):
        """使用二分查找快速定位事件"""
        if not self.anchor_seconds:
            return None
            
        # 特别处理第一个事件（00:00:00开始）
        if target_seconds <= self.anchor_seconds[0]:
            return self.anchor_events[0]
            
        idx = bisect.bisect_right(self.anchor_seconds, target_seconds) - 1
        
        if idx >= 0:
            return self.anchor_events[idx]
        else:
            # 如果找不到匹配的事件，返回第一个事件作为默认
            return self.anchor_events[0] if self.anchor_events else None

    def leaveEvent(self, event):
        """鼠标离开窗口时隐藏标签"""
        self.hover_label.hide()
        self.last_hover_text = ""

    def enterEvent(self, event):
        # 鼠标进入窗口时立即触发一次检测
        self.last_mouse_pos = event.pos()
        if not self.hover_timer.isActive():
            self.hover_timer.start(50)  # 缩短到50ms提高响应速度
        self.update()

    def _check_hover_state(self):
        """全局检测定时器回调：检查鼠标是否还在环内"""
        if not self.last_mouse_pos:
            return
            
        # 检查鼠标是否还在环内
        if not self._is_in_ring(self.last_mouse_pos):
            # 不在环内，立即隐藏标签
            self.hover_label.hide()
            self.last_hover_text = ""
            self.hover_timer.stop()  # 停止节流定时器

    def on_enter(self):
        try:
            event_name = self.input.text().strip()
            if event_name:
                now = datetime.datetime.now().strftime("%H:%M:%S")
                self.anchors.append({"time": now, "event": event_name})
                self.save_anchors()
                self.precompute_anchor_data()
                self._render_static()  # 重新渲染静态内容
                self.input.clear()
                self.update()
        except Exception as e:
            print(f"Error in on_enter: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ClockWindow()
    w.show()
    sys.exit(app.exec_())
