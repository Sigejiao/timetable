from PyQt5.QtCore import QPoint, QRectF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap
import math
import datetime

class ClockRenderer:
    """时钟绘制引擎 - 专门负责所有绘制相关的逻辑"""
    
    def __init__(self):
        # 20种事件颜色
        self.event_colors = [
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
        
        # 画笔配置
        self._pens = {
            'tick': QPen(QColor(130, 130, 130, 128), 2),
            'hour_hand': QPen(QColor(0, 0, 0), 4),
            'minute_hand': QPen(QColor(0, 0, 0), 2),
            'second_hand': QPen(QColor(255, 0, 0), 1),
            'button': QPen(QColor(50, 50, 50, 200), 2),
        }
        
        # 几何参数
        self.ring_width_ratio = 0.15
        
        # 缓存
        self._static_pixmap = None
        self._need_static_update = True
        self._tick_coords = []
        self._center = QPoint()
        self._radius = 0
        self._ring_width = 0
        
    def compute_geometry(self, width, height, input_height):
        """计算几何参数"""
        self._center = QPoint(width//2, (height - input_height)//2)
        self._radius = int(min(width, height - input_height) * 0.35)
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
        
        self._need_static_update = True
    
    def render_static(self, size, anchor_segments):
        """渲染静态内容到QPixmap缓存"""
        if not self._need_static_update:
            return self._static_pixmap
            
        self._static_pixmap = QPixmap(size)
        self._static_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self._static_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制窗口背景
        painter.setBrush(QColor(240, 240, 240, 128))
        painter.setPen(QPen(QColor(200, 200, 200, 128), 1))
        painter.drawRoundedRect(self._static_pixmap.rect(), 10, 10)
        
        # 画底色圆
        painter.setBrush(QColor(255, 255, 224))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self._center, self._radius, self._radius)
        
        # 绘制表盘刻度
        painter.setPen(self._pens['tick'])
        for x1, y1, x2, y2 in self._tick_coords:
            painter.drawLine(x1, y1, x2, y2)
        
        # 绘制按钮
        self._draw_buttons(painter, size)
        
        # 绘制历史环段
        self._draw_static_segments(painter, anchor_segments)
        
        painter.end()
        self._need_static_update = False
        return self._static_pixmap
    
    def _draw_buttons(self, painter, size):
        """绘制右上角按钮"""
        button_size = int(size.width() * 0.07)
        margin = int(size.width() * 0.03)
        
        # X按钮（变小）
        x_button_size = int(button_size * 0.7)
        x_center_x = size.width() - margin - x_button_size // 2
        x_center_y = margin + x_button_size // 2
        
        # ☰按钮（变大）
        menu_button_size = int(button_size * 1.3)
        menu_center_x = x_center_x - menu_button_size//2 - 10
        menu_top = margin
        
        painter.setPen(self._pens['button'])
        
        # 绘制☰符号
        line_length = menu_button_size // 2
        line_spacing = menu_button_size // 4
        vertical_offset = menu_button_size // 6
        
        for i in range(3):
            y_pos = menu_top + line_spacing * (i + 1) - vertical_offset
            painter.drawLine(
                menu_center_x - line_length//2, y_pos,
                menu_center_x + line_length//2, y_pos
            )
        
        # 绘制X符号
        painter.drawLine(x_center_x - x_button_size//2, x_center_y - x_button_size//2, 
                        x_center_x + x_button_size//2, x_center_y + x_button_size//2)
        painter.drawLine(x_center_x + x_button_size//2, x_center_y - x_button_size//2, 
                        x_center_x - x_button_size//2, x_center_y + x_button_size//2)
    
    def _draw_static_segments(self, painter, anchor_segments):
        """绘制静态的历史环段"""
        if not anchor_segments:
            return
            
        for i, segment in enumerate(anchor_segments):
            if segment['end'] <= datetime.datetime.now():
                # 为每个环段分配颜色
                color = self.event_colors[i % len(self.event_colors)]
                self._draw_single_segment(painter, segment['start'], segment['end'], color)
    
    def _draw_single_segment(self, painter, start, end, color):
        """绘制单个环段"""
        noon = datetime.datetime.combine(start.date(), datetime.time(12, 0, 0))
        
        inner_radius = self._radius + self._ring_width//2
        outer_radius = self._radius + self._ring_width + self._ring_width//2
        
        if start < noon and end > noon:
            self._draw_arc_part(painter, inner_radius, start, noon - datetime.timedelta(seconds=1), color)
            self._draw_arc_part(painter, outer_radius, noon, end, color)
        elif start >= noon:
            self._draw_arc_part(painter, outer_radius, start, end, color)
        else:
            self._draw_arc_part(painter, inner_radius, start, end, color)
    
    def _draw_arc_part(self, painter, ring_radius, start, end, color):
        """绘制单个环上的弧段"""
        start_of_day = datetime.datetime.combine(start.date(), datetime.time(0, 0, 0))
        
        def time_to_angle(dt):
            seconds = (dt - start_of_day).total_seconds()
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
    
    def draw_dynamic_content(self, painter, anchors, current_segment_index):
        """绘制动态内容：当前时间段和时钟指针"""
        # 绘制当前进行中的时间段
        if anchors and current_segment_index is not None:
            now = datetime.datetime.now()
            anchor = anchors[current_segment_index]
            start_time = datetime.datetime.strptime(anchor["time"], "%H:%M:%S").time()
            
            if start_time <= now.time():
                start_dt = datetime.datetime.combine(now.date(), start_time)
                color = self.event_colors[current_segment_index % len(self.event_colors)]
                self._draw_single_segment(painter, start_dt, now, color)
        
        # 绘制时钟指针
        now = datetime.datetime.now()
        self._draw_clock_hands(painter, now.hour, now.minute, now.second)
    
    def _draw_clock_hands(self, painter, hour, minute, second):
        """绘制时钟指针"""
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
    
    def _draw_hand(self, painter, center, length, angle):
        """绘制指针"""
        rad = math.radians(90 - angle)
        end_x = center.x() + length * math.cos(rad)
        end_y = center.y() - length * math.sin(rad)
        end = QPoint(int(end_x), int(end_y))
        painter.drawLine(center, end)
    
    def get_ring_bounds(self):
        """获取圆环边界信息，用于交互检测"""
        inner_radius = self._radius + self._ring_width//2
        outer_radius = self._radius + self._ring_width + self._ring_width//2
        inner_ring_outer = inner_radius + self._ring_width//2
        outer_ring_outer = outer_radius + self._ring_width//2
        
        return {
            'center': self._center,
            'radius': self._radius,
            'inner_ring_outer': inner_ring_outer,
            'outer_ring_outer': outer_ring_outer,
            'ring_width': self._ring_width
        }
    
    def invalidate_cache(self):
        """使缓存失效，强制重新渲染"""
        self._need_static_update = True 