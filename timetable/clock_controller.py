from PyQt5.QtCore import QTimer, QPoint, Qt, QRectF
from PyQt5.QtWidgets import QLabel
import math
import datetime
import json
import os
import bisect
import subprocess
import sys
import webbrowser
import time

class ClockController:
    """时钟交互控制器 - 专门负责所有交互和数据管理逻辑"""
    
    def __init__(self, widget):
        self.widget = widget
        
        # 数据管理
        self.data_dir = "time_data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.today = datetime.date.today().isoformat()
        self.start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
        self.anchors = []
        
        # 预计算数据
        self.anchor_seconds = []
        self.anchor_events = []
        self._anchor_segments = []
        
        # 交互状态
        self.dragging = False
        self.drag_position = QPoint()
        self.last_mouse_pos = None
        self.last_hover_text = ""
        
        # 悬停标签
        self.hover_label = QLabel(widget)
        self.hover_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.hover_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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
        
        # 定时器
        self.hover_timer = QTimer(widget)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._do_hover_detection)
        
        self.global_hover_timer = QTimer(widget)
        self.global_hover_timer.timeout.connect(self._check_hover_state)
        self.global_hover_timer.start(200)
        
        self.date_check_timer = QTimer(widget)
        self.date_check_timer.timeout.connect(self._check_date_change)
        self.date_check_timer.start(60000)
        
        # 加载数据
        self.load_anchors()
    
    def load_anchors(self):
        """加载锚点数据"""
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
        """保存锚点数据"""
        path = self.get_today_file()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.anchors, f, ensure_ascii=False, indent=2)
    
    def get_today_file(self):
        """获取今天的数据文件路径"""
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
                "color_index": i % 20  # 20种颜色
            })
            
            # 预计算环段几何数据
            if i + 1 < len(self.anchors):
                start_dt = datetime.datetime.strptime(start_time, "%H:%M:%S")
                end_dt = datetime.datetime.strptime(end_time, "%H:%M:%S")
                self._anchor_segments.append({
                    'start': start_dt,
                    'end': end_dt,
                    'color': None,  # 颜色由渲染器提供
                    'is_current': False
                })
    
    def add_event(self, event_name):
        """添加新事件"""
        # 如果输入为空或只包含空白字符，使用"未命名"作为默认名称
        if not event_name or not event_name.strip():
            event_name = "未命名"
        else:
            event_name = event_name.strip()
        
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.anchors.append({"time": now, "event": event_name})
        self.save_anchors()
        self.precompute_anchor_data()
        return True
    
    def get_current_segment_index(self):
        """获取当前时间段的索引"""
        if not self.anchors:
            return None
            
        now = datetime.datetime.now()
        current_time = now.time()
        
        for i, anchor in enumerate(self.anchors):
            start_time = datetime.datetime.strptime(anchor["time"], "%H:%M:%S").time()
            
            if i + 1 < len(self.anchors):
                end_time = datetime.datetime.strptime(self.anchors[i + 1]["time"], "%H:%M:%S").time()
                if start_time <= current_time < end_time:
                    return i
            else:
                if start_time <= current_time:
                    return i
        return None
    
    def get_anchor_segments(self):
        """获取锚点环段数据"""
        return self._anchor_segments
    
    def get_anchors(self):
        """获取锚点数据"""
        return self.anchors
    
    def handle_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 检查按钮点击
            if self._is_menu_button_clicked(event.pos()):
                self.run_time_manage()
                return True
            elif self._is_close_button_clicked(event.pos()):
                return "close"
            
            # 开始拖拽
            self.dragging = True
            self.drag_position = event.globalPos() - self.widget.frameGeometry().topLeft()
            return "drag"
        return None
    
    def handle_mouse_release(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            return True
        return False
    
    def handle_mouse_move(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.widget.move(event.globalPos() - self.drag_position)
            return "drag"
        else:
            # 悬停检测
            if not event.buttons():
                pos = event.pos()
                self.last_mouse_pos = pos
                
                if self._is_in_ring(pos):
                    global_pos = self.widget.mapToGlobal(pos + QPoint(15, -15))
                    self.hover_label.move(global_pos)
                    
                    if not self.hover_timer.isActive():
                        self.hover_timer.start(50)
                else:
                    self.hover_label.hide()
                    self.last_hover_text = ""
                    self.hover_timer.stop()
            return "hover"
    
    def _is_menu_button_clicked(self, pos):
        """检查是否点击了菜单按钮"""
        button_size = int(self.widget.width() * 0.07)
        margin = int(self.widget.width() * 0.03)
        
        x_button_size = int(button_size * 0.7)
        x_left = self.widget.width() - margin - x_button_size
        
        menu_button_size = int(button_size * 1.3)
        menu_left = x_left - menu_button_size - 5
        menu_top = margin
        menu_rect = QRectF(menu_left, menu_top, menu_button_size, menu_button_size)
        
        return menu_rect.contains(pos)
    
    def _is_close_button_clicked(self, pos):
        """检查是否点击了关闭按钮"""
        button_size = int(self.widget.width() * 0.07)
        margin = int(self.widget.width() * 0.03)
        
        x_button_size = int(button_size * 0.7)
        x_left = self.widget.width() - margin - x_button_size
        x_top = margin
        x_rect = QRectF(x_left, x_top, x_button_size, x_button_size)
        
        return x_rect.contains(pos)
    
    def _is_in_ring(self, pos):
        """检查鼠标是否在圆环区域内"""
        bounds = self.widget.renderer.get_ring_bounds()
        center = bounds['center']
        
        mouse_x, mouse_y = pos.x(), pos.y()
        distance = math.sqrt((mouse_x - center.x())**2 + (mouse_y - center.y())**2)
        
        inner_ring_outer = bounds['inner_ring_outer']
        outer_ring_outer = bounds['outer_ring_outer']
        
        return (bounds['radius'] - 5 <= distance <= inner_ring_outer + 5 or 
                inner_ring_outer - 2 < distance <= outer_ring_outer + 5)
    
    def _do_hover_detection(self):
        """悬停检测处理"""
        if not self.last_mouse_pos:
            return
            
        pos = self.last_mouse_pos
        
        if not self._is_in_ring(pos):
            self.hover_label.hide()
            self.last_hover_text = ""
            return
        
        angle = self._calc_angle(pos)
        is_afternoon = self._is_afternoon_ring(pos)
        
        if is_afternoon:
            target_seconds = int((angle / 360) * 43200) + 43200
        else:
            target_seconds = int((angle / 360) * 43200)
        
        # 检查目标时间是否已经过去
        now = datetime.datetime.now()
        current_seconds = (now - self.start_of_day).total_seconds()
        
        # 如果目标时间在未来，不显示标签
        if target_seconds > current_seconds:
            self.hover_label.hide()
            self.last_hover_text = ""
            return
        
        event_info = self._find_event_at_seconds(target_seconds)
        
        new_text = ""
        if event_info:
            new_text = f"{event_info['start_time']} - {event_info['end_time']}\n{event_info['event_name']}"
        
        if new_text != self.last_hover_text:
            if new_text:
                self.hover_label.setText(new_text)
                self.hover_label.show()
            else:
                self.hover_label.hide()
            self.last_hover_text = new_text
    
    def _calc_angle(self, pos):
        """计算鼠标位置对应的角度"""
        bounds = self.widget.renderer.get_ring_bounds()
        center = bounds['center']
        
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        angle = math.degrees(math.atan2(-dy, -dx))
        return (angle + 270) % 360
    
    def _is_afternoon_ring(self, pos):
        """判断是否在外环（下午时间）"""
        bounds = self.widget.renderer.get_ring_bounds()
        center = bounds['center']
        
        mouse_x, mouse_y = pos.x(), pos.y()
        distance = math.sqrt((mouse_x - center.x())**2 + (mouse_y - center.y())**2)
        
        inner_ring_outer = bounds['inner_ring_outer']
        outer_ring_outer = bounds['outer_ring_outer']
        
        return inner_ring_outer + 2 < distance <= outer_ring_outer + 2
    
    def _find_event_at_seconds(self, target_seconds):
        """使用二分查找快速定位事件"""
        if not self.anchor_seconds:
            return None
        
        # 获取当前时间
        now = datetime.datetime.now()
        current_seconds = (now - self.start_of_day).total_seconds()
        
        # 如果目标时间在未来，返回None
        if target_seconds > current_seconds:
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
    
    def _check_hover_state(self):
        """检查悬停状态"""
        if not self.last_mouse_pos:
            return
            
        if not self._is_in_ring(self.last_mouse_pos):
            self.hover_label.hide()
            self.last_hover_text = ""
            self.hover_timer.stop()
    
    def _check_date_change(self):
        """检查日期变化"""
        current_date = datetime.date.today().isoformat()
        if current_date != self.today:
            print(f"日期已变化：{self.today} -> {current_date}，正在刷新数据...")
            
            self.today = current_date
            self.start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0, 0))
            
            self.load_anchors()
            
            # 通知渲染器更新
            self.widget.renderer.invalidate_cache()
            
            self.hover_label.hide()
            self.last_hover_text = ""
            self.hover_timer.stop()
            
            print(f"数据刷新完成，新文件：{self.get_today_file()}")
    
    def run_time_manage(self):
        """运行时间管理可视化应用"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            run_app_path = os.path.join(current_dir, "run_app.py")
            
            if os.path.exists(run_app_path):
                if os.name == 'nt':
                    process = subprocess.Popen([sys.executable, run_app_path], 
                                             cwd=current_dir,
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process = subprocess.Popen([sys.executable, run_app_path], 
                                             cwd=current_dir,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                
                time.sleep(2)
                
                try:
                    webbrowser.open('http://127.0.0.1:8050', new=0, autoraise=True)
                except Exception:
                    pass
            else:
                pass
        except Exception:
            pass
    
    def handle_leave_event(self):
        """处理鼠标离开事件"""
        self.hover_label.hide()
        self.last_hover_text = ""
    
    def handle_enter_event(self, event):
        """处理鼠标进入事件"""
        self.last_mouse_pos = event.pos()
        if not self.hover_timer.isActive():
            self.hover_timer.start(50) 