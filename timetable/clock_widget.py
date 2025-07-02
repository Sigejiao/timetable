from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter
import sys

from clock_renderer import ClockRenderer
from clock_controller import ClockController

class ClockWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # 窗口配置
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize(260, 280)
        self.move_to_bottom_right()
        
        # 初始化渲染器和控制器
        self.renderer = ClockRenderer()
        self.controller = ClockController(self)
        
        # 初始化UI
        self.init_ui()
        
        # 指针定时重绘
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("输入事件名称...")
        self.input.returnPressed.connect(self.on_enter)
        self.input.setMouseTracking(True)
        self.input.mouseMoveEvent = lambda a0: self.mouseMoveEvent(a0)
        
        layout.addStretch()
        layout.addWidget(self.input)
        self.setLayout(layout)
        
        # 计算几何并渲染静态内容
        self.renderer.compute_geometry(self.width(), self.height(), self.input.height())
        self.renderer.render_static(self.size(), self.controller.get_anchor_segments())
    
    def move_to_bottom_right(self):
        """移动到屏幕右下角"""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.move(geometry.width() - self.width() - 20, geometry.height() - self.height() - 40)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.renderer.compute_geometry(self.width(), self.height(), self.input.height())
        self.renderer.render_static(self.size(), self.controller.get_anchor_segments())
    
    def paintEvent(self, event):
        """绘制事件"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制静态缓存内容
            static_pixmap = self.renderer.render_static(self.size(), self.controller.get_anchor_segments())
            if static_pixmap:
                painter.drawPixmap(0, 0, static_pixmap)
            
            # 绘制动态内容
            current_segment_index = self.controller.get_current_segment_index()
            self.renderer.draw_dynamic_content(painter, self.controller.get_anchors(), current_segment_index)
            
        except Exception as e:
            print(f"Error in paintEvent: {e}")
            import traceback
            traceback.print_exc()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        result = self.controller.handle_mouse_press(event)
        if result == "close":
            QApplication.quit()
        elif result == "drag":
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if self.controller.handle_mouse_release(event):
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        result = self.controller.handle_mouse_move(event)
        if result in ["drag", "hover"]:
            event.accept()
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.controller.handle_leave_event()
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.controller.handle_enter_event(event)
        self.update()
    
    def on_enter(self):
        """输入框回车事件"""
        try:
            event_name = self.input.text()
            if self.controller.add_event(event_name):
                self.input.clear()
                self.renderer.invalidate_cache()
                self.update()
        except Exception as e:
            print(f"Error in on_enter: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ClockWindow()
    w.show()
    sys.exit(app.exec_())
